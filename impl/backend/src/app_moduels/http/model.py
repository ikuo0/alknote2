from ctypes import sizeof
from dataclasses import dataclass
from fileinput import filename
from http import cookies
from fastapi.responses import JSONResponse

@dataclass
class FilePart:
    origin_file_name: str = ""  # アップロードされたファイルの元のファイル名
    extension: str = ""  # 拡張子（例: "jpg", "png", "pdf" など）。origin_file_name から抽出する想定
    save_path: str = ""  # /tmp/upload/uuid.ext みたいな感じで保存される想定
    content_type: str = ""  # MIMEタイプ（例: "image/jpeg", "application/pdf" など）
    size: int = 0  # ファイルのサイズ（バイト単位）


@dataclass
class HttpRequestContext:
    create_utms: int
    client_ip: str
    method: str
    path: str
    query_string: str
    url: str
    headers: list[tuple[str, str]]
    cookies: list[tuple[str, str]]
    # body: str
    query_params: list[tuple[str, str]]
    form_params: list[tuple[str, str]]
    has_json_content_type: bool
    parsed_json: dict
    files: list[FilePart]

@dataclass
class HttpResponseContext:
    status_code: int
    # headers: list[tuple[str, str]]
    # cookies: list[tuple[str, str]]
    meta: dict
    data: dict
    errors: list[str]

    def to_tuple(self):
        return (
            self.status_code,
            {
                "meta": self.meta,
                "data": self.data,
                "errors": self.errors,
            }
        )

    def json_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content={
                "meta": self.meta,
                "data": self.data,
                "errors": self.errors,
            }
        )
