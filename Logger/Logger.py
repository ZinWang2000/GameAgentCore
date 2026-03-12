import os
import sys
from enum import IntEnum
from datetime import datetime

def __LINE__():
    return sys._getframe(4).f_lineno

def __FILE__():
    return os.path.basename(sys._getframe(4).f_code.co_filename)

class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

class Logger:
    def __init__(self, logPath: str, minLogLevel: int):
        """
        日志管理类
        :param logPath: 日志文件地址
        :param minLogLevel: 打印等级，建议INFO（1）或WARNING（2）
        """
        self.logPath = logPath
        self.minLogLevel = minLogLevel
        self.logFile = open(logPath, 'a', encoding='utf-8')

    @staticmethod
    def _format_message(level: LogLevel, message: str):
        currentTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = __FILE__()
        line = __LINE__()
        return f"{currentTime} [{level.name}] {filename}:{line}: {message}"

    def _log(self, level: LogLevel, message: str):
        if level >= self.minLogLevel:
            formattedMsg = self._format_message(level, message)
            print(formattedMsg)
            self.logFile.write(formattedMsg + "\n")
        pass

    def Debug(self, message: str):
        self._log(LogLevel.DEBUG, message)

    def Info(self, message: str):
        self._log(LogLevel.INFO, message)

    def Warning(self, message: str):
        self._log(LogLevel.WARNING, message)

    def Error(self, message: str):
        self._log(LogLevel.ERROR, message)



