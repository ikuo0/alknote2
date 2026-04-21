import pytest
from helper import hash_string, verify_hash
import inspect


def dumpvars(**kwargs):
    print("\n" + "#" * 100)
    for name, value in kwargs.items():
        print(f"{name} = {value!r}")

"""
pytest -s -vv impl/backend/src/modules/helper/helper_test.py::TestHashString
"""
class TestHashString:
    def test_returns_string(self):
        target = "password"
        result = hash_string(target.encode("utf-8"))
        assert isinstance(result, str)
        dumpvars(function=inspect.currentframe().f_code.co_name, raw=target, result=result)

    def test_hashed_value_is_not_plain(self):
        raw = b"password"
        result = hash_string(raw)
        assert result != raw.decode("utf-8")
        dumpvars(function=inspect.currentframe().f_code.co_name, raw=raw, result=result)

    def test_different_calls_produce_different_hashes(self):
        raw = b"password"
        hash1 = hash_string(raw)
        hash2 = hash_string(raw)
        assert hash1 != hash2
        dumpvars(function=inspect.currentframe().f_code.co_name, raw=raw, hash1=hash1, hash2=hash2)


"""
pytest -s -vv impl/backend/src/modules/helper/helper_test.py::TestVerifyHash
"""
class TestVerifyHash:
    def test_correct_password_returns_true(self):
        raw = b"password"
        hashed = hash_string(raw)
        assert verify_hash(raw, hashed) is True
        dumpvars(function=inspect.currentframe().f_code.co_name, raw=raw, hashed=hashed)

    def test_wrong_password_returns_false(self):
        raw = b"password"
        hashed = hash_string(raw)
        assert verify_hash(b"wrong_password", hashed) is False
        dumpvars(function=inspect.currentframe().f_code.co_name, raw=raw, hashed=hashed)

    def test_empty_password(self):
        raw = b""
        hashed = hash_string(raw)
        assert verify_hash(raw, hashed) is True
        dumpvars(function=inspect.currentframe().f_code.co_name, raw=raw, hashed=hashed)

    def test_empty_password_wrong_input_returns_false(self):
        raw = b""
        hashed = hash_string(raw)
        assert verify_hash(b"notempty", hashed) is False
        dumpvars(function=inspect.currentframe().f_code.co_name, raw=raw, hashed=hashed)
