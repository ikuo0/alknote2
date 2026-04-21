import traceback

from fastapi import APIRouter, Request
from src.app_moduels.http.factory import request_factory, response_factory
from src.modules.application.process import process_scope
from src.modules.factory.factory import create_app_context, file_to_process_identity
from src.modules.usecase.signup_verify_identity.model import (
    InvalidEmailError,
    InvalidPasswordError as SignupInvalidPasswordError,
)
from src.modules.usecase.signup_verify_identity.usecase import \
    execute as signup_verify_identity_usecase
from src.modules.usecase.issue_account_id.model import (
    InvalidTokenError, TooManyAttemptsError, TokenExpiredError, InvalidPasswordError as IssueAccountInvalidPasswordError, DatabaseError)
from src.modules.usecase.issue_account_id.usecase import \
    execute as issue_account_id_usecase

router = APIRouter()

@router.post("/signup_verify_identity")
async def signup_verify_identity(request: Request):
    ctx = create_app_context(file_to_process_identity(__file__))

    try:
        with process_scope(ctx):
            http_request_ctx = await request_factory(request, tmp_dir="/tmp")
            parsed_json = http_request_ctx.parsed_json

            email = parsed_json.get("email", None)
            password = parsed_json.get("password", None)
            if email is None or password is None:
                raise ValueError("email and password are required")

            result = signup_verify_identity_usecase(ctx, email, password)

        http_response_ctx = response_factory(
            ctx,
            True,
            200,
            {
                "create_utms": result.create_utms
            },
            []
        )
        return http_response_ctx.json_response()
    except (ValueError, InvalidEmailError, SignupInvalidPasswordError) as e:
        ctx.error(f"Invalid Input: {str(e)}")
        http_response_ctx = response_factory(
            ctx,
            False,
            400,
            {},
            [f"{type(e).__name__}: {str(e)}"]
        )
        return http_response_ctx.json_response()
    except Exception as e:
        ctx.error(f"Internal server error: {str(e)}\n{traceback.format_exc()}")
        http_response_ctx = response_factory(
            ctx,
            False,
            500,
            {},
            [f"{type(e).__name__}: {str(e)}"]
        )
        return http_response_ctx.json_response()

@router.post("/issue_account_id")
async def issue_account_id(request: Request):
    ctx = create_app_context(file_to_process_identity(__file__))

    try:
        with process_scope(ctx):
            http_request_ctx = await request_factory(request, tmp_dir="/tmp")
            parsed_json = http_request_ctx.parsed_json

            verify_token = parsed_json.get("verify_token", None)
            password = parsed_json.get("password", None)
            if verify_token is None or password is None:
                raise ValueError("verify_token and password are required")

            result = issue_account_id_usecase(ctx, verify_token, password)

        http_response_ctx = response_factory(
            ctx,
            True,
            200,
            {
                "account_id": result.account_id,
                "expiry_utms": result.expiry_utms,
            },
            []
        )
        return http_response_ctx.json_response()
    except ValueError as e:
        ctx.error(f"Invalid Input: {str(e)}")
        http_response_ctx = response_factory(
            ctx,
            False,
            400,
            {},
            [f"{type(e).__name__}: {str(e)}"]
        )
        return http_response_ctx.json_response()
    except (InvalidTokenError, TooManyAttemptsError, TokenExpiredError, IssueAccountInvalidPasswordError) as e:
        ctx.error(f"Verification failed: {str(e)}")
        http_response_ctx = response_factory(
            ctx,
            False,
            400,
            {},
            [f"{type(e).__name__}: {str(e)}"]
        )
        return http_response_ctx.json_response()
    except DatabaseError as e:
        ctx.error(f"Database error: {str(e)}\n{traceback.format_exc()}")
        http_response_ctx = response_factory(
            ctx,
            False,
            500,
            {},
            [f"{type(e).__name__}: {str(e)}"]
        )
        return http_response_ctx.json_response()
    except Exception as e:
        ctx.error(f"Internal server error: {str(e)}\n{traceback.format_exc()}")
        http_response_ctx = response_factory(
            ctx,
            False,
            500,
            {},
            [f"{type(e).__name__}: {str(e)}"]
        )
        return http_response_ctx.json_response()