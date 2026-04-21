"""
pytest -s -vv impl/backend/src/app_moduels/http/factory_test.py
"""
import io

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.app_moduels.http.factory import request_factory
from src.app_moduels.http.model import HttpRequestContext, FilePart
import inspect

# ─────────────────────────────────────────────
# テスト用 FastAPI アプリ
# ─────────────────────────────────────────────

app = FastAPI()

_last_ctx: HttpRequestContext | None = None


@app.get("/test")
async def handle_get(request: Request):
    global _last_ctx
    _last_ctx = await request_factory(request, tmp_dir="/tmp/factory_test")
    return {"ok": True}


@app.post("/test")
async def handle_post(request: Request):
    global _last_ctx
    _last_ctx = await request_factory(request, tmp_dir="/tmp/factory_test")
    return {"ok": True}

def dumpvars(**kwargs):
    print("\n" + "#" * 100)
    for name, value in kwargs.items():
        print(f"{name} = {value!r}")

client = TestClient(app, raise_server_exceptions=True)


# ─────────────────────────────────────────────
# GET テスト
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/app_moduels/http/factory_test.py::TestGet
"""
class TestGet:

    def test_GET_methodがGETである(self):
        client.get("/test")
        assert _last_ctx.method == "GET"

    def test_GET_pathが正しい(self):
        client.get("/test")
        assert _last_ctx.path == "/test"

    def test_GET_クエリパラメータが取得できる(self):
        client.get("/test?foo=bar&baz=qux")
        params = dict(_last_ctx.query_params)
        assert params.get("foo") == "bar"
        assert params.get("baz") == "qux"

    def test_GET_query_stringが取得できる(self):
        client.get("/test?foo=bar")
        assert "foo=bar" in _last_ctx.query_string
        dumpvars(function=inspect.currentframe().f_code.co_name, query_string=_last_ctx.query_string)

    def test_GET_filesが空リストである(self):
        client.get("/test")
        assert _last_ctx.files == []

    def test_GET_has_json_content_typeがFalseである(self):
        client.get("/test")
        assert _last_ctx.has_json_content_type is False

    def test_GET_create_utmsが正の整数である(self):
        client.get("/test")
        assert isinstance(_last_ctx.create_utms, int)
        assert _last_ctx.create_utms > 0


# ─────────────────────────────────────────────
# POST (form) テスト
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/app_moduels/http/factory_test.py::TestPost
"""
class TestPost:

    def test_POST_methodがPOSTである(self):
        client.post("/test", data={"key": "value"})
        assert _last_ctx.method == "POST"

    def test_POST_フォームパラメータが取得できる(self):
        client.post("/test", data={"username": "alice", "age": "30"})
        params = dict(_last_ctx.form_params)
        assert params.get("username") == "alice"
        assert params.get("age") == "30"
        dumpvars(function=inspect.currentframe().f_code.co_name, form_params=_last_ctx.form_params)

    def test_POST_filesが空リストである(self):
        client.post("/test", data={"key": "value"})
        assert _last_ctx.files == []

    def test_POST_has_json_content_typeがFalseである(self):
        client.post("/test", data={"key": "value"})
        assert _last_ctx.has_json_content_type is False


# ─────────────────────────────────────────────
# POST (添付ファイル 1件) テスト
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/app_moduels/http/factory_test.py::TestPostSingleFile
"""
class TestPostSingleFile:

    def test_添付ファイル1件_filesの件数が1である(self):
        file_content = b"hello file"
        client.post("/test", files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")})
        assert len(_last_ctx.files) == 1

    def test_添付ファイル1件_origin_file_nameが正しい(self):
        file_content = b"hello file"
        client.post("/test", files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")})
        assert _last_ctx.files[0].origin_file_name == "test.txt"

    def test_添付ファイル1件_extensionが正しい(self):
        file_content = b"hello file"
        client.post("/test", files={"file": ("photo.jpg", io.BytesIO(file_content), "image/jpeg")})
        assert _last_ctx.files[0].extension == ".jpg"
        dumpvars(function=inspect.currentframe().f_code.co_name, origin_file_name=_last_ctx.files[0].origin_file_name, extension=_last_ctx.files[0].extension)

    def test_添付ファイル1件_content_typeが正しい(self):
        file_content = b"hello file"
        client.post("/test", files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")})
        assert _last_ctx.files[0].content_type == "text/plain"

    def test_添付ファイル1件_sizeが正しい(self):
        file_content = b"hello file"
        client.post("/test", files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")})
        assert _last_ctx.files[0].size == len(file_content)

    def test_添付ファイル1件_save_pathが空でない(self):
        file_content = b"hello file"
        client.post("/test", files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")})
        assert _last_ctx.files[0].save_path != ""

    def test_添付ファイル1件_フォームフィールドとの併用(self):
        file_content = b"combined"
        client.post(
            "/test",
            data={"username": "bob"},
            files={"file": ("data.bin", io.BytesIO(file_content), "application/octet-stream")},
        )
        assert len(_last_ctx.files) == 1
        params = dict(_last_ctx.form_params)
        assert params.get("username") == "bob"


# ─────────────────────────────────────────────
# POST (添付ファイル 複数) テスト
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/app_moduels/http/factory_test.py::TestPostMultipleFiles
"""
class TestPostMultipleFiles:

    def test_添付ファイル複数_filesの件数が2である(self):
        client.post(
            "/test",
            files=[
                ("file", ("a.txt", io.BytesIO(b"aaa"), "text/plain")),
                ("file", ("b.png", io.BytesIO(b"bbb"), "image/png")),
            ],
        )
        assert len(_last_ctx.files) == 2

    def test_添付ファイル複数_各ファイル名が正しい(self):
        client.post(
            "/test",
            files=[
                ("file", ("a.txt", io.BytesIO(b"aaa"), "text/plain")),
                ("file", ("b.png", io.BytesIO(b"bbb"), "image/png")),
            ],
        )
        names = [f.origin_file_name for f in _last_ctx.files]
        assert "a.txt" in names
        assert "b.png" in names
        for f in _last_ctx.files:
            dumpvars(function=inspect.currentframe().f_code.co_name, origin_file_name=f.origin_file_name, extension=f.extension, content_type=f.content_type, size=f.size)

    def test_添付ファイル複数_各サイズが正しい(self):
        client.post(
            "/test",
            files=[
                ("file", ("a.txt", io.BytesIO(b"aaa"), "text/plain")),
                ("file", ("b.png", io.BytesIO(b"bbbbb"), "image/png")),
            ],
        )
        sizes = sorted([f.size for f in _last_ctx.files])
        assert sizes == [3, 5]

    def test_添付ファイル複数_各extensionが正しい(self):
        client.post(
            "/test",
            files=[
                ("file", ("doc.pdf", io.BytesIO(b"pdf"), "application/pdf")),
                ("file", ("img.jpg", io.BytesIO(b"jpg"), "image/jpeg")),
            ],
        )
        extensions = sorted([f.extension for f in _last_ctx.files])
        assert extensions == [".jpg", ".pdf"]


# ─────────────────────────────────────────────
# POST (JSON) テスト
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/app_moduels/http/factory_test.py::TestPostJson
"""
class TestPostJson:

    def test_JSON_has_json_content_typeがTrueである(self):
        client.post("/test", json={"name": "alice"})
        assert _last_ctx.has_json_content_type is True

    def test_JSON_parsed_jsonが正しくパースされる(self):
        client.post("/test", json={"name": "alice", "age": 30})
        assert _last_ctx.parsed_json == {"name": "alice", "age": 30}

    def test_JSON_methodがPOSTである(self):
        client.post("/test", json={"key": "value"})
        assert _last_ctx.method == "POST"

    def test_JSON_filesが空リストである(self):
        client.post("/test", json={"key": "value"})
        assert _last_ctx.files == []

    def test_JSON_ネストしたオブジェクトがパースされる(self):
        payload = {"user": {"name": "bob", "tags": ["a", "b"]}}
        client.post("/test", json=payload)
        assert _last_ctx.parsed_json == payload
