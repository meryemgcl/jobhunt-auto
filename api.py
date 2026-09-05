import os
import logging
from typing import Annotated

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from pydantic import BaseModel
import uvicorn
from main import main as run_jobhunt_engine
from services.database import init_database
from services.feedback import submit_feedback
from services.logging_config import configure_logging

app = FastAPI(
    title="JobHunt-Auto Trigger API",
    description="n8n veya HTTP istemcileri üzerinden deterministik kariyer istihbarat motorunu tetikler.",
    version="1.0"
)


logger = logging.getLogger(__name__)


class FeedbackRequest(BaseModel):
    url: str
    feedback: str
    note: str = ""


def _verify_api_token(x_jobhunt_token: str | None) -> None:
    expected_token = os.getenv("JOBHUNT_API_TOKEN")
    if expected_token and x_jobhunt_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid JobHunt-Auto API token.")


def jobhunt_background_task():
    """Arka planda JobHunt-Auto deterministik motorunu çalıştırır."""
    configure_logging()
    logger.info("n8n/API tetiklemesi alindi. JobHunt-Auto deterministik motoru baslatiliyor.")
    run_jobhunt_engine()


@app.api_route("/trigger-engine", methods=["GET", "POST"])
async def trigger_engine(
    background_tasks: BackgroundTasks,
    x_jobhunt_token: Annotated[str | None, Header()] = None,
):
    """
    n8n üzerinden HTTP POST ile bu endpoint'e istek atılarak
    JobHunt-Auto motoru asenkron olarak başlatılabilir.
    """
    _verify_api_token(x_jobhunt_token)
    background_tasks.add_task(jobhunt_background_task)
    return {"status": "success", "message": "JobHunt-Auto engine run queued."}


@app.api_route("/trigger-crew", methods=["GET", "POST"])
async def trigger_crew_legacy(
    background_tasks: BackgroundTasks,
    x_jobhunt_token: Annotated[str | None, Header()] = None,
):
    """Backward-compatible alias for older n8n workflows."""
    return await trigger_engine(background_tasks, x_jobhunt_token)


@app.get("/")
async def root():
    return {"message": "JobHunt-Auto API calisiyor. /trigger-engine adresine POST istegi atabilirsiniz."}


@app.get("/health")
async def health():
    try:
        db_path = init_database()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"JobHunt-Auto unhealthy: {exc}") from exc
    return {"status": "ok", "database": str(db_path)}


@app.post("/feedback")
async def feedback(
    payload: FeedbackRequest,
    x_jobhunt_token: Annotated[str | None, Header()] = None,
):
    _verify_api_token(x_jobhunt_token)
    try:
        canonical_url = submit_feedback(payload.url, payload.feedback, note=payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "success", "canonical_url": canonical_url, "feedback": payload.feedback}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
