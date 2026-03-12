from Logger import Logger
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.output_parsers import StrOutputParser

class ModelManager:
    def __init__(self, model, logger: Logger):
        self.logger = logger
        self.chain = None
        self.promptTemplate = None

        self.logger.Info(f"Creating model {model}")
        self.Model = ChatTongyi(
            model=model,
        )

        self.logger.Info("ModelManager init")

    def CreatePromptTemplate(self, promptTemplate):
        self.promptTemplate = ChatPromptTemplate.from_messages(promptTemplate)
        self.logger.Info("PromptTemplate Created")

    def InitChain(self, retriever):
        if self.chain is None:
            def format_document(docs: list[Document]):
                if not docs:
                    return "无参考资料"

                formatted_str = ""
                for doc in docs:
                    formatted_str += f"文档片段：{doc.page_content}\n文档元数据：{doc.metadata}\n\n"

                return formatted_str

            self.chain = (
                {
                    "input": RunnablePassthrough(),
                    "context": retriever | format_document
                } | self.promptTemplate | self.Model | StrOutputParser()
            )
            self.logger.Info(f"Chain Init")
        else:
            self.logger.Warning(f"Chain already existed")

    def GetReply(self, input: str):
        if self.chain is None:
            self.logger.Error(f"Chain is empty")
            return ""
        return self.chain.invoke(input)