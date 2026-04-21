from contextlib import contextmanager
import traceback
from src.modules.application.application import ApplicationContext, ProcessStatus
from src.modules.helper.helper import unixtime_ms, uuid_hex


@contextmanager
def process_scope(ctx: ApplicationContext):
    try:
        yield
        ctx.process_status = ProcessStatus.SUCCESS
    except Exception as e:
        ctx.error(f"Process {ctx.process_id} failed with error: {e}")
        ctx.error(traceback.format_exc())
        ctx.process_status = ProcessStatus.FAILURE
        raise
    finally:
        ctx.end_utms = unixtime_ms()
        ctx.elapsed_ms = ctx.end_utms - ctx.start_utms
        ctx.info(f"Process {ctx.process_id} completed in {ctx.elapsed_ms} ms")
