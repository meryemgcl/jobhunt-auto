import contextvars
import logging
import os
import sys
import uuid


_RUN_ID = contextvars.ContextVar("jobhunt_run_id", default="-")
_BASE_FACTORY = logging.getLogRecordFactory()
_FACTORY_INSTALLED = False


def _record_factory(*args, **kwargs):
    record = _BASE_FACTORY(*args, **kwargs)
    record.run_id = _RUN_ID.get()
    return record


def configure_logging(run_id: str | None = None) -> str:
    """Configure process-wide structured logging and return the active run id."""
    global _FACTORY_INSTALLED

    active_run_id = run_id or os.getenv("JOBHUNT_RUN_ID") or uuid.uuid4().hex[:12]
    _RUN_ID.set(active_run_id)

    if not _FACTORY_INSTALLED:
        logging.setLogRecordFactory(_record_factory)
        _FACTORY_INSTALLED = True

    level_name = os.getenv("JOBHUNT_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [run_id=%(run_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
        force=True,
    )
    return active_run_id
