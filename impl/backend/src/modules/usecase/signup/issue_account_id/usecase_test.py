"""
pytest -s -vv impl/backend/src/modules/usecase/signup/issue_account_id/usecase_test.py
"""
import os
import time

import boto3
import pytest

from src.modules.app_logger.app_logger import get_logger
from src.modules.application.application import ApplicationContext
from src.modules.config.config import get_config, Config
from src.modules.helper.helper import unixtime_ms, uuid_hex, hash_string
from impl.backend.src.modules.usecase.signup.issue_account_id.model import (
    InvalidTokenError,
    TooManyAttemptsError,
    TokenExpiredError,
    InvalidPasswordError,
)
from impl.backend.src.modules.usecase.signup.issue_account_id import usecase

EMAIL_RECIPIENT = os.environ["TEST_SENDER_EMAIL"]

# ─────────────────────────────────────────────
# ヘルパー
# ─────────────────────────────────────────────

def make_ctx() -> ApplicationContext:
    cfg = get_config("local")
    logger = get_logger("test_issue_account_id")
    return ApplicationContext("test", cfg, logger)


def make_ddb_client(cfg: Config):
    return boto3.client(
        "dynamodb",
        region_name=cfg.DDB_REGION,
        endpoint_url=f"http://{cfg.DDB_HOST}",
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
    )


def insert_verify_token(
    cfg: Config,
    verify_token: str,
    email: str,
    password_hash: str,
    attempts: int,
    ttl_expire_at: int,
) -> None:
    client = make_ddb_client(cfg)
    client.put_item(
        TableName="ddbVerifyToken",
        Item={
            "verify_token": {"S": verify_token},
            "email": {"S": email},
            "password_hash": {"S": password_hash},
            "attempts": {"N": str(attempts)},
            "create_utms": {"N": str(unixtime_ms())},
            "ttl_expire_at": {"N": str(ttl_expire_at)},
        },
    )


def fetch_verify_token_item(cfg: Config, verify_token: str) -> dict | None:
    client = make_ddb_client(cfg)
    resp = client.get_item(
        TableName="ddbVerifyToken",
        Key={"verify_token": {"S": verify_token}},
    )
    return resp.get("Item")


def fetch_account_item(cfg: Config, account_id: str) -> dict | None:
    client = make_ddb_client(cfg)
    resp = client.get_item(
        TableName="ddbAccount",
        Key={"account_id": {"S": account_id}},
    )
    return resp.get("Item")


def fetch_instance_item(cfg: Config, instance_id: str) -> dict | None:
    client = make_ddb_client(cfg)
    resp = client.get_item(
        TableName="ddbInstance",
        Key={"instance_id": {"S": instance_id}},
    )
    return resp.get("Item")


def delete_verify_token(cfg: Config, verify_token: str) -> None:
    client = make_ddb_client(cfg)
    client.delete_item(
        TableName="ddbVerifyToken",
        Key={"verify_token": {"S": verify_token}},
    )


def delete_account(cfg: Config, account_id: str) -> None:
    client = make_ddb_client(cfg)
    client.delete_item(
        TableName="ddbAccount",
        Key={"account_id": {"S": account_id}},
    )


def delete_instance(cfg: Config, instance_id: str) -> None:
    client = make_ddb_client(cfg)
    client.delete_item(
        TableName="ddbInstance",
        Key={"instance_id": {"S": instance_id}},
    )


def make_verify_token() -> str:
    now_ms = unixtime_ms()
    return f"vtoken.{now_ms}.{uuid_hex()}"


def future_ttl() -> int:
    """十分先の有効期限（現在+1時間）"""
    return int(time.time()) + 3600


def past_ttl() -> int:
    """過去の有効期限（1秒）"""
    return 1


# ─────────────────────────────────────────────
# 正常系テスト
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup/issue_account_id/usecase_test.py::TestExecuteSuccess
"""
class TestExecuteSuccess:

    # pytest -s -vv impl/backend/src/modules/usecase/signup/issue_account_id/usecase_test.py::TestExecuteSuccess::test_正常系_戻り値にaccount_idが含まれる
    def test_正常系_戻り値にaccount_idが含まれる(self):
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())

        result = usecase.execute(ctx, verify_token, password)

        assert result.account_id.startswith("aid.")

    def test_正常系_戻り値にinstance_idが含まれる(self):
        ctx = make_ctx()
        password = "5678"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())

        result = usecase.execute(ctx, verify_token, password)

        assert result.instance_id.startswith("iid.")

    def test_正常系_ddbAccountにレコードが保存される(self):
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())

        result = usecase.execute(ctx, verify_token, password)

        item = fetch_account_item(ctx.config, result.account_id)
        assert item is not None
        assert item["instance_id"]["S"] == result.instance_id

    def test_正常系_ddbInstanceにレコードが保存される(self):
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())

        result = usecase.execute(ctx, verify_token, password)

        item = fetch_instance_item(ctx.config, result.instance_id)
        assert item is not None
        assert item["account_id"]["S"] == result.account_id

    def test_正常系_ddbVerifyTokenが削除される(self):
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())

        result = usecase.execute(ctx, verify_token, password)

        item = fetch_verify_token_item(ctx.config, verify_token)
        assert item is None

    def test_正常系_expiry_utmsが現在時刻より未来である(self):
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        before_ms = unixtime_ms()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())

        result = usecase.execute(ctx, verify_token, password)

        assert result.expiry_utms > before_ms

    def test_正常系_ttl_expire_atが現在時刻より未来である(self):
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        before_s = int(time.time())
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())

        result = usecase.execute(ctx, verify_token, password)

        assert result.ttl_expire_at > before_s

    def test_正常系_emailが入力値と一致する(self):
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())

        result = usecase.execute(ctx, verify_token, password)

        assert result.email == EMAIL_RECIPIENT

    def test_正常系_メール送信が完了する(self):
        """実際にメールを送信する"""
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())

        result = usecase.execute(ctx, verify_token, password)


# ─────────────────────────────────────────────
# 異常系: 存在しないトークン
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup/issue_account_id/usecase_test.py::TestInvalidToken
"""
class TestInvalidToken:

    def test_異常系_存在しないトークンでInvalidTokenErrorが発生する(self):
        ctx = make_ctx()
        non_existent_token = f"vtoken.0.nonexistent_{uuid_hex()}"
        with pytest.raises(InvalidTokenError):
            usecase.execute(ctx, non_existent_token, "1234")


# ─────────────────────────────────────────────
# 異常系: attempts 超過
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup/issue_account_id/usecase_test.py::TestTooManyAttempts
"""
class TestTooManyAttempts:

    def test_異常系_attempts3でTooManyAttemptsErrorが発生する(self):
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 3, future_ttl())

        with pytest.raises(TooManyAttemptsError):
            usecase.execute(ctx, verify_token, password)

    def test_異常系_attempts5でTooManyAttemptsErrorが発生する(self):
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 5, future_ttl())

        with pytest.raises(TooManyAttemptsError):
            usecase.execute(ctx, verify_token, password)


# ─────────────────────────────────────────────
# 異常系: トークン期限切れ
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup/issue_account_id/usecase_test.py::TestTokenExpired
"""
class TestTokenExpired:

    def test_異常系_期限切れトークンでTokenExpiredErrorが発生する(self):
        ctx = make_ctx()
        password = "1234"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(password.encode()), 0, past_ttl())

        with pytest.raises(TokenExpiredError):
            usecase.execute(ctx, verify_token, password)


# ─────────────────────────────────────────────
# 異常系: パスワード不一致
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/modules/usecase/signup/issue_account_id/usecase_test.py::TestInvalidPassword
"""
class TestInvalidPassword:

    def test_異常系_パスワード不一致でInvalidPasswordErrorが発生する(self):
        ctx = make_ctx()
        correct_password = "1234"
        wrong_password = "9999"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(correct_password.encode()), 0, future_ttl())

        with pytest.raises(InvalidPasswordError):
            usecase.execute(ctx, verify_token, wrong_password)

    def test_異常系_パスワード不一致でattemptsがインクリメントされる(self):
        ctx = make_ctx()
        correct_password = "1234"
        wrong_password = "9999"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(correct_password.encode()), 0, future_ttl())

        with pytest.raises(InvalidPasswordError):
            usecase.execute(ctx, verify_token, wrong_password)

        item = fetch_verify_token_item(ctx.config, verify_token)
        assert item is not None
        assert int(item["attempts"]["N"]) == 1

    def test_異常系_パスワード不一致2回でattempts2になる(self):
        ctx = make_ctx()
        correct_password = "1234"
        wrong_password = "9999"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(correct_password.encode()), 0, future_ttl())

        with pytest.raises(InvalidPasswordError):
            usecase.execute(ctx, verify_token, wrong_password)
        with pytest.raises(InvalidPasswordError):
            usecase.execute(ctx, verify_token, wrong_password)

        item = fetch_verify_token_item(ctx.config, verify_token)
        assert item is not None
        assert int(item["attempts"]["N"]) == 2

    def test_異常系_パスワード不一致3回目でTooManyAttemptsErrorが発生する(self):
        ctx = make_ctx()
        correct_password = "1234"
        wrong_password = "9999"
        verify_token = make_verify_token()
        insert_verify_token(ctx.config, verify_token, EMAIL_RECIPIENT, hash_string(correct_password.encode()), 0, future_ttl())

        with pytest.raises(InvalidPasswordError):
            usecase.execute(ctx, verify_token, wrong_password)
        with pytest.raises(InvalidPasswordError):
            usecase.execute(ctx, verify_token, wrong_password)
        with pytest.raises(InvalidPasswordError):
            usecase.execute(ctx, verify_token, wrong_password)
        # 4回目は TooManyAttemptsError
        with pytest.raises(TooManyAttemptsError):
            usecase.execute(ctx, verify_token, wrong_password)
