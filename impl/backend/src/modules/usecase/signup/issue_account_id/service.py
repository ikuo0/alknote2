import time
import traceback

from src.modules.application.application import ApplicationContext
from src.modules.helper.helper import unixtime_ms, uuid_hex, verify_hash
from impl.backend.src.modules.usecase.signup.issue_account_id.model import (
    InvalidTokenError,
    TooManyAttemptsError,
    TokenExpiredError,
    InvalidPasswordError,
    DatabaseError,
    StoredVerifyTokenData,
    IssuedAccountData,
)
from impl.backend.src.modules.usecase.signup.issue_account_id import repository


# ─────────────────────────────────────────────
# 入力処理
# ─────────────────────────────────────────────

def fetch_verify_token_data(ctx: ApplicationContext, verify_token: str) -> StoredVerifyTokenData:
    ctx.info(f"ddbVerifyToken 取得開始: verify_token={verify_token}")
    item = repository.get_verify_token(ctx, verify_token)
    if item is None:
        ctx.error(f"ddbVerifyToken が存在しません: verify_token={verify_token}\n{traceback.format_exc()}")
        raise InvalidTokenError(f"Verify token not found: {verify_token}")

    data = StoredVerifyTokenData(
        verify_token=item["verify_token"]["S"],
        email=item["email"]["S"],
        password_hash=item["password_hash"]["S"],
        attempts=int(item["attempts"]["N"]),
        create_utms=int(item["create_utms"]["N"]),
        ttl_expire_at=int(item["ttl_expire_at"]["N"]),
    )
    ctx.info(f"ddbVerifyToken 取得完了: verify_token={verify_token}")
    return data


# ─────────────────────────────────────────────
# 主処理
# ─────────────────────────────────────────────

def verify_and_create_account_data(
    ctx: ApplicationContext,
    password: str,
    stored: StoredVerifyTokenData,
) -> IssuedAccountData:
    cfg = ctx.config
    ctx.info("アカウント発行 主処理開始")

    # attempts 確認
    ctx.info(f"attempts 確認: stored_attempts={stored.attempts}")
    if stored.attempts >= cfg.VTOKEN_MAX_ATTEMPTS:
        ctx.error(f"試行回数超過: attempts={stored.attempts}\n{traceback.format_exc()}")
        raise TooManyAttemptsError(f"Too many attempts: {stored.attempts}")

    # トークン有効期限確認
    ctx.info(f"トークン有効期限確認: ttl_expire_at={stored.ttl_expire_at}")
    now_s = int(time.time())
    if now_s > stored.ttl_expire_at:
        ctx.error(f"トークン期限切れ: ttl_expire_at={stored.ttl_expire_at}, now={now_s}\n{traceback.format_exc()}")
        raise TokenExpiredError(f"Verify token has expired: ttl_expire_at={stored.ttl_expire_at}")

    # パスワード確認
    ctx.info("パスワード確認")
    if not verify_hash(password.encode("utf-8"), stored.password_hash):
        new_attempts = stored.attempts + 1
        ctx.error(f"パスワード不一致: attempts を {stored.attempts} -> {new_attempts} に更新\n{traceback.format_exc()}")
        repository.increment_attempts(ctx, stored.verify_token, new_attempts)
        raise InvalidPasswordError("Password does not match")

    # 出力用の値作成
    ctx.info("アカウント発行データ作成開始")
    now_ms = unixtime_ms()
    account_id = f"aid.{now_ms}.{uuid_hex()}.{uuid_hex()}"
    instance_id = f"iid.{now_ms}.{uuid_hex()}"
    expiry_utms = now_ms + cfg.INITIAL_EXTENSION_UTMS
    reverify_due_utms = now_ms + cfg.REVERIFY_INTERVAL_UTMS
    ttl_expire_at = int(now_ms / 1000) + int(cfg.LIFE_TIME_UTMS / 1000)

    data = IssuedAccountData(
        account_id=account_id,
        instance_id=instance_id,
        email=stored.email,
        create_utms=now_ms,
        billing_utms=now_ms,
        expiry_utms=expiry_utms,
        reverify_due_utms=reverify_due_utms,
        ttl_expire_at=ttl_expire_at,
    )
    ctx.info(f"アカウント発行データ作成完了: account_id={account_id}")
    return data


# ─────────────────────────────────────────────
# 出力処理
# ─────────────────────────────────────────────

def save_and_notify(
    ctx: ApplicationContext,
    verify_token: str,
    data: IssuedAccountData,
) -> None:
    ctx.info("出力処理開始")

    # DB操作
    try:
        ctx.info(f"ddbAccount 保存: account_id={data.account_id}")
        repository.save_account(ctx, data)

        ctx.info(f"ddbInstance 保存: instance_id={data.instance_id}")
        repository.save_instance(ctx, data)

        ctx.info(f"ddbVerifyToken 削除: verify_token={verify_token}")
        repository.delete_verify_token(ctx, verify_token)
    except Exception as e:
        ctx.error(f"DB操作エラー: {e}\n{traceback.format_exc()}")
        raise DatabaseError(f"Database operation failed: {e}") from e

    # メール送信
    ctx.info(f"アカウント発行メール送信: email={data.email}")
    repository.send_account_email(ctx, data.email, data.account_id)
    ctx.info("出力処理完了")
