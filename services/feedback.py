from pathlib import Path
from typing import Any

from services.database import load_feedback_index, load_feedback_keyword_weights, record_feedback
from services.url_utils import canonicalize_url


def submit_feedback(
    url: str,
    feedback: str,
    *,
    note: str = "",
    path: str | Path | None = None,
) -> str:
    return record_feedback(url, feedback, note=note, path=path)


def feedback_adjustment_for(job: dict[str, Any], feedback_index: dict[str, str]) -> tuple[int, str | None]:
    canonical_url = canonicalize_url(job.get("canonical_url") or job.get("url"))
    if not canonical_url:
        return 0, None

    feedback = feedback_index.get(canonical_url)
    if feedback == "alakasız":
        return -100, "Elendi: kullanici geri bildirimi alakasiz olarak isaretledi"
    if feedback == "basvurdum":
        return -100, "Elendi: kullanici bu firsata daha once basvurdu"
    if feedback == "uygun":
        return 8, "Kullanici geri bildirimi: uygun sinyali"
    return 0, None


__all__ = ["feedback_adjustment_for", "load_feedback_index", "load_feedback_keyword_weights", "submit_feedback"]
