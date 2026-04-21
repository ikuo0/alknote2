
import bcrypt
import time
import uuid

def unixtime_ms() -> int:
    return int(time.time() * 1000)

def uuid_hex() -> str:
    return uuid.uuid4().hex

def hash_string(raw: bytes, rounds=8) -> str:
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(raw, salt)
    return hashed.decode('utf-8')

def verify_hash(raw: bytes, hashed_string: str) -> bool:
    return bcrypt.checkpw(raw, hashed_string.encode('utf-8'))
