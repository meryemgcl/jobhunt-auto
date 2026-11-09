import datetime as dt
import logging
import os
import re
import smtplib

def _sanitize_header(value: str) -> str:
    """E-posta baslik injection saldirisini onler: CRLF karakterlerini temizler."""
    return " ".join(str(value or "").split())

import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

from services.models import freshness_label
from services.url_utils import canonicalize_url


load_dotenv()
logger = logging.getLogger(__name__)


def _safe_url(value) -> str:
    url = canonicalize_url(value)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "#"
    return url


def _int(value, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _template_environment() -> Environment:
    template_dir = Path(__file__).resolve().parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _prepare_newsletter_item(item: dict, *, include_score: bool = False) -> dict:
    payload = dict(item or {})
    payload["url"] = _safe_url(payload.get("url"))
    metadata = payload.get("metadata") or {}
    application_url = _safe_url(metadata.get("application_url"))
    if application_url != "#":
        payload["application_url"] = application_url
    payload["source_reliability"] = max(0, min(100, _int(payload.get("source_reliability"), 70)))
    payload["freshness_score"] = max(0, min(100, _int(payload.get("freshness_score"), 50)))
    payload["freshness_label"] = payload.get("freshness_label") or freshness_label(payload["freshness_score"])
    if include_score:
        payload["score"] = max(0, min(100, _int(payload.get("score"), 0)))
    return payload


def build_html_newsletter(matched_jobs, camps, rd_projects, podcasts, hackathons, news, github_issues, skill_gap, profile, run_stats=None):
    """Render the executive briefing from the Jinja2 HTML template."""
    from config import FEATURE_FLAGS  # Inline import: circular-import riskini onler

    template = _template_environment().get_template("newsletter.html.j2")
    return template.render(
        current_date=dt.datetime.now().strftime("%d.%m.%Y"),
        matched_jobs=[_prepare_newsletter_item(job, include_score=True) for job in matched_jobs],
        camps=[_prepare_newsletter_item(item) for item in camps],
        rd_projects=[_prepare_newsletter_item(item) for item in rd_projects],
        podcasts=[_prepare_newsletter_item(item) for item in podcasts],
        hackathons=[_prepare_newsletter_item(item) for item in hackathons],
        news=[_prepare_newsletter_item(item) for item in news],
        github_issues=[_prepare_newsletter_item(issue) for issue in github_issues],
        skill_gap=skill_gap or {},
        profile=profile or {},
        feature_flags=FEATURE_FLAGS,
        run_stats=run_stats or {},
    )


def send_email_newsletter(html_content, total_jobs_count, *, message_id: str | None = None):
    """Send the rendered newsletter over SMTP."""
    smtp_host = os.getenv("SMTP_HOST") or "smtp.gmail.com"
    try:
        smtp_port = int(os.getenv("SMTP_PORT") or "587")
    except ValueError:
        logger.error("SMTP_PORT sayisal bir port degeri olmalidir.")
        return False
    if not 1 <= smtp_port <= 65535:
        logger.error("SMTP_PORT 1 ile 65535 arasinda olmalidir.")
        return False
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    user_email_to = os.getenv("USER_EMAIL_TO")

    if not smtp_user or not smtp_pass or not user_email_to:
        logger.error("E-posta ayarlari eksik. SMTP_USER, SMTP_PASS ve USER_EMAIL_TO degiskenlerini kontrol edin.")
        return False

    current_date_str = dt.datetime.now().strftime("%d.%m.%Y")
    logger.info("Rapor hedef adrese iletiliyor. recipient=%s", user_email_to)

    msg = MIMEMultipart("alternative")
    safe_from = _sanitize_header(smtp_user)
    safe_to = _sanitize_header(user_email_to)
    subject_raw = (
        f"JobHunt-Auto Raporu | {total_jobs_count} Eslesen Pozisyon, "
        f"GitHub Firsatlari & AR-GE Cagrisi ({current_date_str})"
    )
    safe_subject = _sanitize_header(subject_raw)

    msg["From"] = formataddr(("JobHunt-Auto Platform Intelligence", safe_from))
    msg["To"] = safe_to
    msg["Reply-To"] = "no-reply@jobhunt.auto"
    msg["Subject"] = safe_subject
    msg["X-Auto-Response-Suppress"] = "All"
    msg["X-Entity-Ref-ID"] = f"JOBHUNT-AUTO-{dt.datetime.now().strftime('%Y%m%d%H%M')}"
    if message_id:
        normalized_id = "".join(char for char in message_id if char.isalnum() or char in "-_")
        msg["X-JobHunt-Outbox-ID"] = normalized_id
        msg["Message-ID"] = f"<{normalized_id}@jobhunt-auto>"

    msg.attach(MIMEText("Lütfen HTML destekleyen bir e-posta istemcisi kullanın.", "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception as exc:
        logger.error("E-posta iletim hatasi: %s", exc)
        return False

    logger.info("Kurumsal sistem raporu basariyla iletildi.")
    return True
