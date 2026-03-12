import time
import threading
from enum import IntEnum
from public import AgentContext
from concurrent.futures import ThreadPoolExecutor

class Time(IntEnum):
    COUNTER_50MS  = 1
    COUNTER_100MS = COUNTER_50MS * 2
    COUNTER_1S    = COUNTER_50MS * 20
    COUNTER_10S   = COUNTER_1S * 10
    COUNTER_30S   = COUNTER_1S * 30

class Scheduler:
    def __init__(self, maximumReq, context: AgentContext):
        self.maximumReq = maximumReq
        self.taskCounter = 0
        self.executor = ThreadPoolExecutor(max_workers = self.maximumReq)

        self.ctx = context
        self.promptTemplate = (
            [
                ("system", "参考提供的资料，专业地回答用户问题。参考资料：{context}"),
                ("user", "{input}")
            ]
        )

        self.ctx.model_manager.CreatePromptTemplate(self.promptTemplate)
        self.ctx.model_manager.InitChain(self.ctx.rag_manager.GetRetriever(1))

        self.counter = 0

        pass

    def _fetch_and_print_reply(self, user_input):
        try:
            self.ctx.logger.Info("Send Req")
            print(self.ctx.model_manager.GetReply(user_input))
        except Exception as e:
            self.ctx.logger.Error(f"Req Failed: {e}")

    def run(self):
        if self.counter < Time.COUNTER_1S:
            self.counter += 1
        else:
            self.counter = 0
            user_input = "我刚进入游戏，怎么制造工作台"
            self.executor.submit(self._fetch_and_print_reply, user_input)
            self.ctx.logger.Info("Req submit")

        self.ctx.logger.Info(f"{self.counter}")
        time.sleep(0.05)