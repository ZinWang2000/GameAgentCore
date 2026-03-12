from dataclasses import dataclass
from Logger.Logger import Logger
from Gateway.SSEService import SSEService
from Gateway.WebSocketService import WebSocketService
from MCP.MCPManager import MCPManager
from Memory.MemoryManager import MemoryManager
from RAG.RAGManager import RAGManager
from Model.ModelManager import ModelManager

@dataclass
class AgentContext:
    logger: Logger
    sse_service: SSEService
    ws_service: WebSocketService
    mcp_manager: MCPManager
    memory_manager: MemoryManager
    rag_manager: RAGManager
    model_manager: ModelManager