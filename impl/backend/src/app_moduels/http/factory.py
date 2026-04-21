from pathlib import Path

from fastapi import Request
from src.app_moduels.http.model import (FilePart, HttpRequestContext,
                                        HttpResponseContext)
from src.modules.application.application import ApplicationContext
from src.modules.helper.helper import unixtime_ms, uuid_hex
from starlette.datastructures import FormData


async def get_request_form(request: Request) -> FormData:
    return await request.form()

async def _processing_uploaded_files(form_data: FormData, tmp_dir: str) -> list[FilePart]:
    tmp_dir_path = Path(tmp_dir)
    tmp_dir_path.mkdir(parents=True, exist_ok=True)

    results: list[FilePart] = []

    for field_name, value in form_data.multi_items():
        if not hasattr(value, "filename"):
            continue

        original_filename = value.filename or ""
        original_suffix = Path(original_filename).suffix
        save_filename = f"{unixtime_ms()}.{uuid_hex()}{original_suffix}"
        save_path = tmp_dir_path / save_filename

        total_size = 0
        with open(save_path, "wb") as f:
            while True:
                chunk = await value.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                total_size += len(chunk)

        await value.close()

        results.append(
            FilePart(
                origin_file_name=original_filename,
                extension=original_suffix,
                content_type=getattr(value, "content_type", None),
                size=total_size,
                save_path=str(save_path),
            )
        )

    return results


async def request_factory(request: Request, tmp_dir: str) -> HttpRequestContext:
    form_data = await get_request_form(request)
    file_parts = await _processing_uploaded_files(form_data, tmp_dir=tmp_dir)
    return HttpRequestContext(
        create_utms=unixtime_ms(),
        client_ip=request.client.host,
        method=request.method,
        path=request.url.path,
        query_string=request.url.query,
        url=str(request.url),
        headers=list(request.headers.items()),
        cookies=list(request.cookies.items()),
        query_params=list(request.query_params.multi_items()),
        form_params=list(form_data.multi_items()),
        has_json_content_type=request.headers.get("Content-Type", "").startswith("application/json"),
        parsed_json=await request.json() if request.headers.get("Content-Type", "").startswith("application/json") else {},
        files=file_parts,
    )

def response_factory(ctx: ApplicationContext, ok: bool, status_code: int, body: dict, errors: list[str]) -> HttpResponseContext:
    response_ctx = HttpResponseContext(
        status_code=status_code,
        meta={
            "process_id": ctx.process_id,
            "ok": ok,
            "elapsed_ms": ctx.elapsed_ms,
        },
        data=body,
        errors=errors,
    )
    return response_ctx
