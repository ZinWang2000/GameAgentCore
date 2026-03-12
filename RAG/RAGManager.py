import config
import chromadb
from Logger.Logger import Logger
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

class RAGManager:
    def __init__(self, embeddingModel, collectionName, host, port, logger: Logger):
        self.logger = logger
        self.embedding = DashScopeEmbeddings(model = embeddingModel)
        self.chromaClient = chromadb.HttpClient(
            host=host,
            port=port,
        )
        self.vectorStore = Chroma(
            collection_name = collectionName,
            embedding_function = self.embedding,
            client = self.chromaClient,
        )

        self.logger.Info("RAGManager init")

    def GetRetriever(self, topK):
        """
        返回向量检索器
        :return:
        """
        return self.vectorStore.as_retriever(search_kwargs={"k": topK})