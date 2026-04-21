"""
pytest -s -vv impl/backend/src/modules/usecase/signup/signup_verify_identity/usecase_test.py
"""
import time

import boto3
import pytest

from src.modules.app_logger.app_logger import get_logger
from src.modules.application.application import ApplicationContext
from src.modules.config.config import get_config, Config
from src.modules.helper.helper import unixtime_ms, uuid_hex
from src.modules.usecase.signup.signup_verify_identity.usecase import (
    InvalidEmailError,
    InvalidPasswordError,
    execute,
)

EMAIL_RECIPIENT = "ikuo.pg@gmail.com"

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


def fetch_verify_token_item(cfg: Config, verify_token: str) -> dict | None:
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


# ─────────────────────────────────────────────
# 正常系テスト
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup/signup_verify_identity/usecase_test.py::TestExecuteSuccess
"""
class TestExecuteSuccess:

    # pytest -s -vv impl/backend/src/modules/usecase/signup/signup_verify_identity/usecase_test.py::TestExecuteSuccess::test_正常系_戻り値にverify_tokenが含まれる
    def test_正常系_戻り値にverify_tokenが含まれる(self):
        ctx = make_ctx()
        result = execute(ctx, EMAIL_RECIPIENT, "1234")
        assert result.verify_token.startswith("vtoken.")
        delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_ddbVerifyTokenにレコードが保存される(self):
        ctx = make_ctx()
        result = execute(ctx, EMAIL_RECIPIENT, "1234")
        item = fetch_verify_token_item(ctx.config, result.verify_token)
        assert item is not None
        delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_ddbVerifyTokenのemailが一致する(self):
        ctx = make_ctx()
        result = execute(ctx, EMAIL_RECIPIENT, "1234")
        item = fetch_verify_token_item(ctx.config, result.verify_token)
        assert item["email"]["S"] == EMAIL_RECIPIENT
        delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_ddbVerifyTokenのattemptsが0である(self):
        ctx = make_ctx()
        result = execute(ctx, EMAIL_RECIPIENT, "1234")
        item = fetch_verify_token_item(ctx.config, result.verify_token)
        assert int(item["attempts"]["N"]) == 0
        delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_ddbVerifyTokenのexpiry_utmsが現在時刻より未来である(self):
        ctx = make_ctx()
        before_ms = unixtime_ms()
        result = execute(ctx, EMAIL_RECIPIENT, "1234")
        assert result.expiry_utms > before_ms
        delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_ddbVerifyTokenのttl_expire_atが秒単位で未来である(self):
        ctx = make_ctx()
        before_s = int(time.time())
        result = execute(ctx, EMAIL_RECIPIENT, "1234")
        assert result.ttl_expire_at > before_s
        delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_ttl_expire_atはexpiry_utmsを秒換算した値である(self):
        ctx = make_ctx()
        result = execute(ctx, EMAIL_RECIPIENT, "1234")
        assert result.ttl_expire_at == int(result.expiry_utms / 1000)
        delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_password_hashが保存される(self):
        ctx = make_ctx()
        result = execute(ctx, EMAIL_RECIPIENT, "1234")
        item = fetch_verify_token_item(ctx.config, result.verify_token)
        assert "password_hash" in item
        assert item["password_hash"]["S"] != ""
        delete_verify_token(ctx.config, result.verify_token)

    def test_正常系_メール送信が完了する(self):
        """実際にメールを送信する"""
        ctx = make_ctx()
        result = execute(ctx, EMAIL_RECIPIENT, "5678")
        delete_verify_token(ctx.config, result.verify_token)


# ─────────────────────────────────────────────
# 異常系: 不正メールアドレス
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup/signup_verify_identity/usecase_test.py::TestInvalidEmail
"""
class TestInvalidEmail:

    def test_異常系_メールアドレスが空でInvalidEmailErrorが発生する(self):
        ctx = make_ctx()
        with pytest.raises(InvalidEmailError):
            execute(ctx, "", "1234")

    def test_異常系_メールアドレスにatマークなしでInvalidEmailErrorが発生する(self):
        ctx = make_ctx()
        with pytest.raises(InvalidEmailError):
            execute(ctx, "invalidemail", "1234")

    def test_異常系_メールアドレスにドメインなしでInvalidEmailErrorが発生する(self):
        ctx = make_ctx()
        with pytest.raises(InvalidEmailError):
            execute(ctx, "user@", "1234")


# ─────────────────────────────────────────────
# 異常系: 不正パスワード
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup/signup_verify_identity/usecase_test.py::TestInvalidPassword
"""
class TestInvalidPassword:

    def test_異常系_パスワードが空でInvalidPasswordErrorが発生する(self):
        ctx = make_ctx()
        with pytest.raises(InvalidPasswordError):
            execute(ctx, EMAIL_RECIPIENT, "")

    def test_異常系_パスワードが3桁でInvalidPasswordErrorが発生する(self):
        ctx = make_ctx()
        with pytest.raises(InvalidPasswordError):
            execute(ctx, EMAIL_RECIPIENT, "123")

    def test_異常系_パスワードが5桁でInvalidPasswordErrorが発生する(self):
        ctx = make_ctx()
        with pytest.raises(InvalidPasswordError):
            execute(ctx, EMAIL_RECIPIENT, "12345")

    def test_異常系_パスワードに文字が含まれるとInvalidPasswordErrorが発生する(self):
        ctx = make_ctx()
        with pytest.raises(InvalidPasswordError):
            execute(ctx, EMAIL_RECIPIENT, "12ab")
