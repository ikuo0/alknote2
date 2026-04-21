"""
pytest -s -vv impl/backend/src/modules/usecase/signup_verify_identity/repository_test.py
"""
import os

import pytest

from src.modules.app_logger.app_logger import get_logger
from src.modules.application.application import ApplicationContext
from src.modules.config.config import get_config
from src.modules.usecase.signup_verify_identity import repository


SEND_TO_EMAIL = os.environ["TEST_SENDER_EMAIL"]


def make_ctx() -> ApplicationContext:
    cfg = get_config(os.environ.get("APP_ENV", "LOCAL"))
    logger = get_logger("test_repository")
    return ApplicationContext("test", cfg, logger)


"""
pytest -s -vv impl/backend/src/modules/usecase/signup_verify_identity/repository_test.py::TestSendVerifyEmail
"""
class TestSendVerifyEmail:

    def test_正常系_メール送信が成功する(self):
        ctx = make_ctx()
        verify_token = "vtoken.test.dummy_token_for_test"
        # 例外が発生しなければ成功
        repository.send_verify_email(ctx, SEND_TO_EMAIL, verify_token)
