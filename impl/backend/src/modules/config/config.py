import logging
import os
from dataclasses import dataclass, field
from enum import Enum

class Env(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STG = "stg"
    PROD = "prod"

def _days_to_utms(days: int) -> int:
    return days * 24 * 60 * 60 * 1000

def _hours_to_utms(hours: int) -> int:
    return hours * 60 * 60 * 1000

@dataclass
class Config:
    # アカウント関係
    # 作成時は7日使える、8日目～14日目までは閲覧、エクスポートだけ行える課金猶予期間がある
    # 15日目以降は完全に使えなくなる
    # 無課金のまま40日経過したら、関連したデータは全て削除される
    # 課金すると利用期間が32日延長される、課金した瞬間からではなく expiry_utms に加算される点に注意
    BILLING_EXTENSION_UTMS: int = field(default_factory=lambda: _days_to_utms(32))
    INITIAL_EXTENSION_UTMS: int = field(default_factory=lambda: _days_to_utms(7))
    VIEW_ONLY_GRACE_UTMS: int = field(default_factory=lambda: _days_to_utms(7)) # expiry_utms + VIEW_ONLY_GRACE_UTMS までは閲覧、エクスポートだけ行える猶予期間
    LIFE_TIME_UTMS: int = field(default_factory=lambda: _days_to_utms(40))
    REVERIFY_INTERVAL_UTMS: int = field(default_factory=lambda: _days_to_utms(7)) # 本人確認を1週間に1回求めるためのインターバル

    # 検証トークン関係
    VTOKEN_LIFETIME_UTMS: int = field(default_factory=lambda: _hours_to_utms(1))
    VTOKEN_MAX_ATTEMPTS: int = 3

    # アクセストークン関係
    ATOKEN_DEFAULT_LIFETIME_UTMS: int = field(default_factory=lambda: _days_to_utms(7))

    # AWS関係
    AWS_ACCESS_KEY_ID: str = "dummy"
    AWS_SECRET_ACCESS_KEY: str = "dummy"
    AWS_DEFAULT_REGION: str = "ap-northeast-1"


    # DynamoDB関係
    DDB_HOST: str = "localhost:8000"
    DDB_REGION: str = "ap-northeast-1"

    # S3関係
    S3_BUCKET_NAME: str = "none"

    # GMAIL関係
    GMAIL_HOST: str = "smtp.gmail.com"
    GMAIL_PORT: int = 587
    GMAIL_APP_USER_NAME: str = "none"
    GMAIL_APP_PASSWORD: str = "none"
    TEST_SENDER_EMAIL: str = ""

@dataclass
class LocalConfig(Config):
    DDB_HOST: str = "192.168.10.153:8000"
    S3_BUCKET_NAME: str = "alknote-local-bucket"

@dataclass
class DevConfig(Config):
    S3_BUCKET_NAME: str = "alknote-dev-bucket"

@dataclass
class StgConfig(Config):
    S3_BUCKET_NAME: str = "alknote-stg-bucket"

@dataclass
class ProdConfig(Config):
    S3_BUCKET_NAME: str = "alknote-prod-bucket"

def _get_config(env: Env) -> Config:
    if env == Env.LOCAL:
        return LocalConfig()
    elif env == Env.DEV:
        return DevConfig()
    elif env == Env.STG:
        return StgConfig()
    elif env == Env.PROD:
        return ProdConfig()
    else:
        raise ValueError(f"Unsupported environment: {env}")

def override_config_with_env(config: Config) -> Config:
    # 環境変数で上書き可能な設定項目とその型を定義
    env_overrides = {
        "AWS_ACCESS_KEY_ID": str,
        "AWS_SECRET_ACCESS_KEY": str,
        "GMAIL_APP_USER_NAME": str,
        "GMAIL_APP_PASSWORD": str,
        "TEST_SENDER_EMAIL": str,
    }
    for key, typ in env_overrides.items():
        if key in os.environ:
            setattr(config, key, typ(os.environ[key]))
        else:
            required_keys = ", ".join(env_overrides.keys())
            print(f"Warning: Environment variable {key} is not set. It is recommended to set it for proper functioning. Required keys are: {required_keys}")
            raise ValueError(f"Please set the required environment variable: {key}")
    return config

def get_config(env_str: str) -> Config:
    try:
        env = Env(env_str)
    except ValueError:
        raise ValueError(f"Invalid APP_ENV value: {env_str}")
    cfg = _get_config(env)
    cfg = override_config_with_env(cfg)
    return cfg
