import re
import smtplib
import traceback
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3

from src.modules.application.application import ApplicationContext
from src.modules.helper.helper import unixtime_ms, uuid_hex, hash_string


# ─────────────────────────────────────────────
# 例外
# ─────────────────────────────────────────────

class InvalidEmailError(Exception):
    pass


class InvalidPasswordError(Exception):
    pass


class DatabaseError(Exception):
    pass


class EmailSendError(Exception):
    pass


# ─────────────────────────────────────────────
# データクラス
# ─────────────────────────────────────────────

@dataclass
class VerifyTokenData:
    verify_token: str
    email: str
    password_hash: str
    attempts: int
    create_utms: int
    expiry_utms: int
    ttl_expire_at: int


# ─────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────

_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_PASSWORD_PATTERN = re.compile(r"^[0-9]{4}$")


# ─────────────────────────────────────────────
# メイン処理
# ─────────────────────────────────────────────

def execute(ctx: ApplicationContext, email: str, password: str) -> VerifyTokenData:
    ctx.info("signup_verify_identity usecase 開始")

    # メールアドレス検証
    ctx.info(f"メールアドレス検証: email={email}")
    if not _EMAIL_PATTERN.match(email):
        ctx.error(f"メールアドレスが不正です: email={email}\n{traceback.format_exc()}")
        raise InvalidEmailError(f"Invalid email address: {email}")

    # パスワード検証
    ctx.info("パスワード検証")
    if not _PASSWORD_PATTERN.match(password):
        ctx.error(f"パスワードが不正です（4桁の数字である必要があります）\n{traceback.format_exc()}")
        raise InvalidPasswordError("Password must be a 4-digit number")

    # ddbVerifyToken 用データ作成
    ctx.info("ddbVerifyToken 用データ作成")
    cfg = ctx.config
    now_ms = unixtime_ms()
    verify_token = f"vtoken.{now_ms}.{uuid_hex()}"
    password_hash = hash_string(password.encode("utf-8"))
    expiry_utms = now_ms + cfg.VTOKEN_LIFETIME_UTMS
    ttl_expire_at = int(expiry_utms / 1000)

    data = VerifyTokenData(
        verify_token=verify_token,
        email=email,
        password_hash=password_hash,
        attempts=0,
        create_utms=now_ms,
        expiry_utms=expiry_utms,
        ttl_expire_at=ttl_expire_at,
    )
    ctx.info(f"ddbVerifyToken 用データ作成完了: verify_token={verify_token}")

    # DynamoDB 保存
    ctx.info(f"ddbVerifyToken 保存: verify_token={verify_token}")
    try:
        client = boto3.client(
            "dynamodb",
            region_name=cfg.DDB_REGION,
            endpoint_url=f"http://{cfg.DDB_HOST}",
            aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
        )
        client.put_item(
            TableName="ddbVerifyToken",
            Item={
                "verify_token": {"S": data.verify_token},
                "email": {"S": data.email},
                "password_hash": {"S": data.password_hash},
                "attempts": {"N": str(data.attempts)},
                "create_utms": {"N": str(data.create_utms)},
                "expiry_utms": {"N": str(data.expiry_utms)},
                "ttl_expire_at": {"N": str(data.ttl_expire_at)},
            },
        )
    except Exception as e:
        ctx.error(f"ddbVerifyToken 保存失敗: {e}\n{traceback.format_exc()}")
        raise DatabaseError(f"Database operation failed: {e}") from e
    ctx.info("ddbVerifyToken 保存完了")

    # メール送信
    ctx.info(f"検証メール送信: email={email}")
    try:
        body = (
            "以下のURLをクリックして本人確認を完了してください。\n\n"
            f"https://example.com/verify?vtoken={verify_token}\n\n"
            "このURLは１時間有効です。"
        )
        msg = MIMEMultipart()
        msg["From"] = cfg.GMAIL_APP_USER_NAME
        msg["To"] = email
        msg["Subject"] = "【AlkNote】本人確認のお願い"
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(cfg.GMAIL_HOST, cfg.GMAIL_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(cfg.GMAIL_APP_USER_NAME, cfg.GMAIL_APP_PASSWORD)
            smtp.sendmail(cfg.GMAIL_APP_USER_NAME, email, msg.as_string())
    except Exception as e:
        ctx.error(f"メール送信失敗: {e}\n{traceback.format_exc()}")
        raise EmailSendError(f"Email send failed: {e}") from e
    ctx.info("検証メール送信完了")

    ctx.info("signup_verify_identity usecase 完了")
    return data
