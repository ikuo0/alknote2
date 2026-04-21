import logging
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:  # ハンドラーが設定されていない場合のみ設定を行う
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        # formatter = logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s')
        formatter = logging.Formatter('%(created).3f\t%(name)s\t%(levelname)s\t%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
