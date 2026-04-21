import os

from src.modules.app_logger.app_logger import get_logger
from src.modules.config.config import get_config
from src.modules.application.application import ApplicationContext
import zlib

def file_to_process_identity(file_path: str) -> str:
    crc = zlib.crc32(file_path.encode())
    basename = os.path.basename(file_path)
    process_identity = f"{basename}.{crc}"
    return process_identity

def create_app_context(process_identity: str) -> ApplicationContext:
    # 環境変数から環境を取得
    env_str = os.getenv("APP_ENV", "__invalid_env__").lower()

    # 環境に応じたConfigを取得し、環境変数で上書き
    cfg = get_config(env_str)

    # ロガーの作成
    logger = get_logger(process_identity)

    return ApplicationContext(process_identity, cfg, logger)
