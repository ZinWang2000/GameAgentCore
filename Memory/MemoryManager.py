import uuid
import json

import pymongo
import redis
from pymongo import MongoClient, UpdateOne
from Logger.Logger import Logger
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage

class MemoryManager:
    def __init__(self, logger: Logger, redisHost: str, redisPort: int, mongoHost: str, mongoPort: int):
        """
        长短期记忆管理类
        :param logger:
        :param redisHost:
        :param redisPort:
        :param mongoHost:
        :param mongoPort:
        """
        self.logger = logger
        self.shorttermMemoryDB = redis.Redis(
            host = redisHost,
            port = redisPort,
            db = 0
        )
        self.logger.Info("RedisDB Init")

        self.longtermMemoryDB = MongoClient(
            host = mongoHost,
            port = mongoPort,
            db = 0
        )["Minecraft"]
        self.logger.Info("MongoDB Init")
        self.activeSessions = [] # 用于记录正在进行中的会话

    #===============================================================
    # 会话
    def _CreateNewSession(self, sessionID, playerUUID: str):
        """
        会话ID未被记录时，创建一个活跃中的会话
        :param sessionID:
        :return: empty session
        """
        self.activeSessions[sessionID] = {}
        self.sessionList.append(sessionID)
        return self.activeSessions[sessionID]

    def _FetchSession(self, sessionID, playerUUID: str):
        """
        会话已存在但不在活跃中，从数据库中取出会话
        :param sessionID:
        :return:
        """
        pass

    #===============================================================
    # 数据库调用
    def _LoadChatHistoryFromMongoDB(self, sessionID, playerUUID: str):
        """
        从MongoDB中加载对话历史数据，MongoDB内的对话历史根据玩家UUID建立集合
        :param sessionID: 唯一Session ID，用于区分玩家对话的对象
        :param playerUUID: 玩家UUID = 集合名
        :return: 返回会话历史和操作结果
        """
        messageCollection = self.longtermMemoryDB[playerUUID]
        cursor = messageCollection.find(
            {
                "session_id": sessionID
            }
        ).sort(
            [
                ("time.day_time", 1),
                ("time.tick", 1)
            ]
        )

        langchainMessage = []

        for item in cursor:
            messageType = item.get("message_type")
            content = item.get("content", "")

            if messageType == "human":
                langchainMessage.append(HumanMessage(content))

            elif messageType == "ai":
                kwargs = {"content": content}
                # 如果有工具调用，一并传入
                if "tool_calls" in item and item["tool_calls"]:
                    kwargs["tool_calls"] = item["tool_calls"]
                langchainMessage.append(AIMessage(**kwargs))

            elif messageType == "tool":
                toolCallID = item.get("tool_call_id")
                langchainMessage.append(ToolMessage(
                    content = content,
                    too_call_id = toolCallID
                ))

        return {
            "langchainMessage": langchainMessage,
            "status": "success"
        }

    def _SaveChatHistoryToMongoDB(self, sessionID, playerUUID: str, time: dict, message: BaseMessage):
        """
        将 LangChain 消息对象转换为 JSON 并存入 MongoDB
        :param sessionID: Session ID
        :param playerUUID: 玩家UUID，存入玩家集合
        :param time: {real_time, day_time, tick}, 真实时间戳，服务器的日期， 服务器的tick时间
        :param message: LangChain Message对象
        :return: 返回Session ID和操作结果
        """
        # 给message兜底
        messageID = message.id if message.id else f"msg_{uuid.uuid4().hex}"

        doc = {
            "session_id": sessionID,
            "message_id": messageID,
            "time": time,
            "content": message.content,
        }

        if isinstance(message, HumanMessage):
            doc["type"] = "human"

        elif isinstance(message, AIMessage):
            doc["type"] = "ai"
            if message.tool_calls:
                doc["tool_calls"] = message.tool_calls

        elif isinstance(message, ToolMessage):
            doc["type"] = "tool"
            doc["tool_call_id"] = message.tool_call_id
            if isinstance(message.content, str):
                try:
                    doc["mcp_result"] = json.loads(message.content)
                except json.JSONDecodeError:
                    pass

        elif isinstance(message, SystemMessage):
            doc["type"] = "system"

        else:
            self.logger.Error(f"Unknown message type: {type(message)}")
            return {
                "sessionID": sessionID,
                "status": "failed"
            }

        messageCollection = self.longtermMemoryDB[playerUUID]
        messageCollection.insert_one(doc)
        self.logger.Info(f"Save {type(message)} chat history to MongoDB")

        return {
            "sessionID": sessionID,
            "status": "success"
        }

    def _LoadChatHistoryFromRedisDB(self, sessionID):
        """
        从Redis中读取会话记录
        :param sessionID:
        :return: 返回会话历史和操作结果
        """

        redisKey = f"chat:session:{sessionID}"
        cachedChatHistory = self.shorttermMemoryDB.zrange(redisKey, 0, -1)

        if cachedChatHistory:
            return {
                "langchainMessage": cachedChatHistory,
                "status": "success"
            }

        return {
            "langchainMessage": [],
            "status": "failed"
        }

    def _SaveChatHistoryToRedisDB(self, sessionID, time: dict, message: BaseMessage):
        """
        将会话记录保存到Redis中
        :param sessionID:
        :param time:
        :param message:
        :return: 返回Session ID和操作结果
        """
        # 给message兜底
        messageID = message.id if message.id else f"msg_{uuid.uuid4().hex}"

        doc = {
            "session_id": sessionID,
            "message_id": messageID,
            "time": time,
            "content": message.content,
        }

        if isinstance(message, HumanMessage):
            doc["type"] = "human"

        elif isinstance(message, AIMessage):
            doc["type"] = "ai"
            if message.tool_calls:
                doc["tool_calls"] = message.tool_calls

        elif isinstance(message, ToolMessage):
            doc["type"] = "tool"
            doc["tool_call_id"] = message.tool_call_id
            if isinstance(message.content, str):
                try:
                    doc["mcp_result"] = json.loads(message.content)
                except json.JSONDecodeError:
                    pass

        elif isinstance(message, SystemMessage):
            doc["type"] = "system"

        else:
            self.logger.Error(f"Unknown message type: {type(message)}")
            return {
                "sessionID": sessionID,
                "status": "failed"
            }

        redisScore = doc['time']['day_time'] * 24000 + doc['time']['tick']  # Minecraft的计算方式
        redisKey = f"chat:session:{sessionID}"
        self.shorttermMemoryDB.zadd(redisKey, {json.dumps(doc): redisScore})
        self.shorttermMemoryDB.expire(redisKey, 86400) # 保存一天，第二天玩家就会忘了昨天干了啥

        return {
            "sessionID": sessionID,
            "status": "success"
        }

    def _LoadChatHistoryFromDB(self, sessionID, playerUUID: str):
        """
        从数据库中获取会话历史
        :param sessionID:
        :param playerUUID:
        :return: 返回会话记录
        """
        fetchChatHistoryResult = self._LoadChatHistoryFromRedisDB(sessionID)
        if fetchChatHistoryResult.get("status") == "success":
            self.logger.Info(f"Load chat history from RedisDB")
            return fetchChatHistoryResult.get("langchainMessage")

        fetchChatHistoryResult = self._LoadChatHistoryFromMongoDB(sessionID, playerUUID)
        if fetchChatHistoryResult.get("status") == "success":
            self.logger.Info(f"Load chat history from MongoDB")
            return fetchChatHistoryResult.get("langchainMessage")

        self.logger.Warning(f"No chat history found for {sessionID}")
        return []

    def _TransferChatHistoryToMongoDB(self, sessionID, playerUUID: str):
        """
        主动调用后会将指定会话从Redis中转移到Mongo保存
        :param sessionID:
        :param playerUUID:
        :return:
        """
        # 从Redis中读取会话记录
        redisKey = f"chat:session:{sessionID}"

        cachedChatHistory = self.shorttermMemoryDB.zrange(redisKey, 0, -1)
        if not cachedChatHistory:
            self.logger.Warning(f"No chat history found for {sessionID} in RedisDB")
            return {
                "sessionID": sessionID,
                "status": "success"
            }

        # 写入MongoDB，需要考虑防重写
        bulkOperations = []
        for record in cachedChatHistory:
            try:
                doc = json.loads(record)
                operation = UpdateOne(
                    filter={"message_id": doc["message_id"]},
                    update={"$set": doc},
                    upsert=True,
                )
                bulkOperations.append(operation)
            except json.JSONDecodeError:
                self.logger.Warning(f"Failed to parse JSON from Redis record: {record}")
                continue

        if not bulkOperations:
            self.logger.Warning(f"bulkOperations is empty")
            return {
                "sessionID": sessionID,
                "status": "failed"
            }

        messageCollection = self.longtermMemoryDB[playerUUID]
        try:
            result = messageCollection.bulk_write(bulkOperations)
            self.logger.Info(f"Transfer success for {sessionID}. Inserted/Updated {len(bulkOperations)} records")
            return {
                "sessionID": sessionID,
                "status": "success"
            }

        except Exception as e:
            self.logger.Error(f"Bulk write to MongoDB failed for session {sessionID}: {e}")
            return {
                "sessionID": sessionID,
                "status": "failed"
            }

    #===============================================================
    # 外部接口
    def GetSession(self, sessionID, playerUUID: str):
        """
        获取会话，会话进入活跃状态
        :param playerUUID:
        :param sessionID:
        :return: session data
        """
        self.activeSessions.append(sessionID)
        if sessionID in self.activeSessions:
            return self.activeSessions[sessionID]
        else:
            if sessionID in self.sessionList:
                return self._FetchSession(sessionID, playerUUID)
            else:
                return self._CreateNewSession(sessionID, playerUUID)

    def CloseSession(self, sessionID, playerUUID: str):
        """
        关闭会话，会话退出活跃状态并保存到数据库中
        :param playerUUID:
        :param sessionID:
        :return:
        """
        result = self._TransferChatHistoryToMongoDB(sessionID, playerUUID)
        if result['status'] == "success":
            self.logger.Info(f"Transfer message Success for {sessionID}: {playerUUID}")
            self.activeSessions.remove(sessionID)
        else:
            self.logger.Warning(f"Transfer message Failed for {sessionID}: {playerUUID}")

    def CacheMessage(self, sessionID, playerUUID: str, time: dict, message: BaseMessage):
        """
        每次产生新的对话或者发生工具调用时缓存消息，消息会缓存到Redis数据库中
        :param time:
        :param sessionID:
        :param playerUUID:
        :param message:
        :return:
        """
        result = self._SaveChatHistoryToRedisDB(sessionID, time, message)
        if result['status'] == "success":
            self.logger.Info(f"Cache message Success for {sessionID}: {playerUUID}")
        else:
            self.logger.Warning(f"Cache message Failed for {sessionID}: {playerUUID}")
