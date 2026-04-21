import logging
from enum import IntEnum

from src.modules.config.config import Config
from src.modules.helper.helper import unixtime_ms, uuid_hex


class ProcessStatus(IntEnum):
    PENDING = 0
    SUCCESS = 1
    FAILURE = 2


class ApplicationContext:
    def __init__(self, process_name: str, cfg: Config, logger: logging.Logger):
        self.process_status = ProcessStatus.PENDING
        self.start_utms = unixtime_ms()
        self.end_utms = 0
        self.elapsed_ms = 0
        self.process_id = ApplicationContext.gen_process_id()
        self.process_name = process_name
        self.logger = logger
        self.config = cfg

    @staticmethod
    def gen_process_id() -> str:
        return f"pid.{unixtime_ms()}.{uuid_hex()}"

    def ok(self) -> bool:
        return self.process_status == ProcessStatus.SUCCESS

    def _log_message(self, msg: str) -> str:
        # return f"{self.process_id} {self.process_name} {msg}"
        return f"{self.process_id} {msg}"

    def info(self, message: str):
        self.logger.info(self._log_message(message))

    def warning(self, message: str):
        self.logger.warning(self._log_message(message))

    def error(self, message: str):
        self.logger.error(self._log_message(message))

    def debug(self, message: str):
        self.logger.debug(self._log_message(message))
