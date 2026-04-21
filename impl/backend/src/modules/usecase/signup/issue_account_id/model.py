from dataclasses import dataclass


class InvalidTokenError(Exception):
    pass


class TooManyAttemptsError(Exception):
    pass


class TokenExpiredError(Exception):
    pass


class InvalidPasswordError(Exception):
    pass


class DatabaseError(Exception):
    pass


@dataclass
class StoredVerifyTokenData:
    verify_token: str
    email: str
    password_hash: str
    attempts: int
    create_utms: int
    ttl_expire_at: int


@dataclass
class IssuedAccountData:
    account_id: str
    instance_id: str
    email: str
    create_utms: int
    billing_utms: int
    expiry_utms: int
    reverify_due_utms: int
    ttl_expire_at: int
