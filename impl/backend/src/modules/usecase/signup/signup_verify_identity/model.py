from dataclasses import dataclass


class InvalidEmailError(Exception):
    pass


class InvalidPasswordError(Exception):
    pass


@dataclass
class VerifyTokenData:
    verify_token: str
    email: str
    password_hash: str
    attempts: int
    create_utms: int
    ttl_expire_at: int
