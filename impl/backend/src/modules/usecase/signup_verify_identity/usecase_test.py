"""
pytest -s -vv impl/backend/src/modules/usecase/signup_verify_identity/usecase_test.py
"""
import os
from unittest.mock import patch, MagicMock

import boto3
import pytest

from src.modules.app_logger.app_logger import get_logger
from src.modules.application.application import ApplicationContext
from src.modules.config.config import get_config, Config
from src.modules.usecase.signup_verify_identity.model import (
    InvalidEmailError,
    InvalidPasswordError,
)
from src.modules.usecase.signup_verify_identity import usecase

# ─────────────────────────────────────────────
# ヘルパー
# ─────────────────────────────────────────────

def make_ctx() -> ApplicationContext:
    cfg = get_config("local")
    logger = get_logger("test_signup_verify_identity")
    return ApplicationContext("test", cfg, logger)


def make_ddb_client(cfg: Config):
    return boto3.client(
        "dynamodb",
        region_name=cfg.DDB_REGION,
        endpoint_url=f"http://{cfg.DDB_HOST}",
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
    )


def fetch_verify_token(cfg: Config, verify_token: str) -> dict | None:
    client = make_ddb_client(cfg)
    resp = client.get_item(
        TableName="ddbVerifyToken",
        Key={"verify_token": {"S": verify_token}},
    )
    return resp.get("Item")


def delete_verify_token(cfg: Config, verify_token: str) -> None:
    client = make_ddb_client(cfg)
    client.delete_item(
        TableName="ddbVerifyToken",
        Key={"verify_token": {"S": verify_token}},
    )


# smtplib.SMTP はテスト環境では実際に送信しない（SMTP サーバー不在）ため最小限のモックを使用
SMTP_MOCK_TARGET = "src.modules.usecase.signup_verify_identity.repository.smtplib.SMTP"

SEND_TO_EMAIL = os.getenv("TEST_SENDER_EMAIL")

# ─────────────────────────────────────────────
# 正常系テスト
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup_verify_identity/usecase_test.py::TestExecuteSuccess
"""
class TestExecuteSuccess:

    def test_正常系_戻り値にverify_tokenが含まれる(self):
        ctx = make_ctx()
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            result = usecase.execute(ctx, SEND_TO_EMAIL, "1234")

        try:
            assert result.verify_token.startswith("vtoken.")
        finally:
            delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_戻り値のemailが入力値と一致する(self):
        ctx = make_ctx()
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            result = usecase.execute(ctx, SEND_TO_EMAIL, "1234")

        try:
            assert result.email == SEND_TO_EMAIL
        finally:
            delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_ddbVerifyTokenにレコードが保存される(self):
        ctx = make_ctx()
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            result = usecase.execute(ctx, SEND_TO_EMAIL, "1234")

        try:
            item = fetch_verify_token(ctx.config, result.verify_token)
            assert item is not None
            assert item["email"]["S"] == SEND_TO_EMAIL
            assert item["attempts"]["N"] == "0"
        finally:
            delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_ddbVerifyTokenのttl_expire_atが正しく設定される(self):
        ctx = make_ctx()
        import time
        before = int(time.time())
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            result = usecase.execute(ctx, SEND_TO_EMAIL, "1234")
        after = int(time.time())

        try:
            expected_lifetime_s = int(ctx.config.VTOKEN_LIFETIME_UTMS / 1000)
            assert before + expected_lifetime_s <= result.ttl_expire_at <= after + expected_lifetime_s
        finally:
            delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_password_hashがハッシュ化されている(self):
        ctx = make_ctx()
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            result = usecase.execute(ctx, SEND_TO_EMAIL, "1234")

        try:
            assert result.password_hash != "1234"
            assert len(result.password_hash) > 0
        finally:
            delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_SMTPが呼び出される(self):
        ctx = make_ctx()
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            smtp_instance = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=smtp_instance)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            result = usecase.execute(ctx, SEND_TO_EMAIL, "1234")
            mock_smtp.assert_called_once()

        delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_attemptsが0である(self):
        ctx = make_ctx()
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            result = usecase.execute(ctx, SEND_TO_EMAIL, "1234")

        try:
            assert result.attempts == 0
        finally:
            delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_create_utmsが現在時刻付近である(self):
        ctx = make_ctx()
        import time
        before_ms = int(time.time() * 1000)
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            result = usecase.execute(ctx, SEND_TO_EMAIL, "1234")
        after_ms = int(time.time() * 1000)

        try:
            assert before_ms <= result.create_utms <= after_ms
        finally:
            delete_verify_token(ctx.config, result.verify_token)

    # def test_正常系_メールアドレスにサブドメインを含む場合も通る(self):
    #     ctx = make_ctx()
    #     with patch(SMTP_MOCK_TARGET) as mock_smtp:
    #         mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
    #         mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
    #         result = usecase.execute(ctx, SEND_TO_EMAIL, "0000")

    #     try:
    #         assert result.email == SEND_TO_EMAIL
    #     finally:
    #         delete_verify_token(ctx.config, result.verify_token)


# ─────────────────────────────────────────────
# 異常系: メールアドレス
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup_verify_identity/usecase_test.py::TestInvalidEmail
"""
class TestInvalidEmail:

    def _assert_invalid_email(self, email: str):
        ctx = make_ctx()
        with pytest.raises(InvalidEmailError):
            with patch(SMTP_MOCK_TARGET):
                usecase.execute(ctx, email, "1234")

    def test_異常系_メールアドレスが空文字(self):
        self._assert_invalid_email("")

    def test_異常系_メールアドレスにatがない(self):
        self._assert_invalid_email("userexample.com")

    def test_異常系_メールアドレスのローカル部が空(self):
        self._assert_invalid_email("@example.com")

    def test_異常系_メールアドレスのドメイン部が空(self):
        self._assert_invalid_email("user@")

    def test_異常系_メールアドレスにドットがない(self):
        self._assert_invalid_email("user@example")

    def test_異常系_メールアドレスにスペースが含まれる(self):
        self._assert_invalid_email("user @example.com")

    def test_異常系_メールアドレスが複数のatを持つ(self):
        self._assert_invalid_email("user@@example.com")


# ─────────────────────────────────────────────
# 異常系: パスワード
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup_verify_identity/usecase_test.py::TestInvalidPassword
"""
class TestInvalidPassword:

    def _assert_invalid_password(self, password: str):
        ctx = make_ctx()
        with pytest.raises(InvalidPasswordError):
            with patch(SMTP_MOCK_TARGET):
                usecase.execute(ctx, SEND_TO_EMAIL, password)

    def test_異常系_パスワードが空文字(self):
        self._assert_invalid_password("")

    def test_異常系_パスワードが3桁(self):
        self._assert_invalid_password("123")

    def test_異常系_パスワードが5桁(self):
        self._assert_invalid_password("12345")

    def test_異常系_パスワードに英字が含まれる(self):
        self._assert_invalid_password("123a")

    def test_異常系_パスワードが英字のみ(self):
        self._assert_invalid_password("abcd")

    def test_異常系_パスワードに記号が含まれる(self):
        self._assert_invalid_password("12.4")

    def test_異常系_パスワードにスペースが含まれる(self):
        self._assert_invalid_password("12 4")

    def test_異常系_パスワードが全角数字(self):
        self._assert_invalid_password("１２３４")
