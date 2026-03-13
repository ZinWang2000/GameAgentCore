import redis
from pymongo import MongoClient
from Logger.Logger import Logger

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
        )
        self.logger.Info("MongoDB Init")

        self.sessionList = []
        self.activeSessions = {}
        self._FetchSessionList()

    def _FetchSessionList(self):
        """
        初始化时获取现有的所有会话ID
        :return:
        """
        pass

    def _CreateNewSession(self, sessionID):
        """
        会话ID未被记录时，创建一个活跃中的会话
        :param sessionID:
        :return: empty session
        """
        self.activeSessions[sessionID] = {}
        self.sessionList.append(sessionID)
        return self.activeSessions[sessionID]

    def _FetchSession(self, sessionID):
        """
        会话已存在但不在活跃中，从数据库中取出会话
        :param sessionID:
        :return:
        """
        pass

    def getSession(self, sessionID):
        """
        获取会话，会话进入活跃状态
        :param sessionID:
        :return: session data
        """
        if sessionID in self.activeSessions:
            return self.activeSessions[sessionID]
        else:
            if sessionID in self.sessionList:
                return self._FetchSession(sessionID)
            else:
                return self._CreateNewSession(sessionID)

    def saveSession(self, sessionID, sessionData: dict):
        """
        临时保存会话，不会退出活跃状态，会话内容不会被保存到数据库
        :param sessionID:
        :param sessionData:
        :return:
        """
        self.activeSessions[sessionID] = sessionData
        pass

    def closeSession(self, sessionID, sessionData: dict):
        """
        关闭会话，会话退出活跃状态并保存到数据库中
        :param sessionID:
        :param sessionData:
        :return:
        """
        pass