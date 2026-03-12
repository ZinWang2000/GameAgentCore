from dotenv import load_dotenv
load_dotenv()

import config
from Logger.Logger import Logger
from Scheduler.Scheduler import Scheduler
from Gateway.SSEService import SSEService
from Gateway.WebSocketService import WebSocketService
from MCP.MCPManager import MCPManager
from Memory.MemoryManager import MemoryManager
from RAG.RAGManager import RAGManager
from Model.ModelManager import ModelManager
from public import AgentContext

class GameAgentCore:
    def __init__(self):
        print("Initializing GameAgentCore...")
        self.Logger = Logger(config.LOG_PATH, config.MIN_LOG_LEVEL)
        self.Logger.Info("Logger Init")

        self.SSEService = SSEService()
        self.Logger.Info("SSEService Init")

        self.WebSocketService = WebSocketService()
        self.Logger.Info("WebSocketService Init")

        self.MCPManager = MCPManager()
        self.Logger.Info("MCPManager Init")

        self.MemoryManager = MemoryManager()
        self.Logger.Info("MemoryManager Init")

        self.RAGManager = RAGManager(
            embeddingModel = config.EMBEDDING_MODEL,
            collectionName = config.COLLECTION_NAME,
            host = config.HOST,
            port = config.PORT,
            logger = self.Logger,
        )
        self.Logger.Info("RAGManager Init")

        self.ModelManager = ModelManager(
            model = config.MODEL,
            logger=self.Logger,
        )
        self.Logger.Info("ModelManager Init")

        self.context = AgentContext(
            logger=self.Logger,
            sse_service=self.SSEService,
            ws_service=self.WebSocketService,
            mcp_manager=self.MCPManager,
            memory_manager=self.MemoryManager,
            rag_manager=self.RAGManager,
            model_manager=self.ModelManager
        )

        self.Scheduler = Scheduler(
            config.MAX_MODEL_CONCURRENCY,
            self.context,
        )
        self.Logger.Info("Scheduler Init")

    def start(self):
        while True:
            self.Scheduler.run()




if __name__ == "__main__":
    gameAgentCore = GameAgentCore()
    gameAgentCore.start()