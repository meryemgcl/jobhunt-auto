import datetime as dt
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

from services.models import freshness_label
from services.url_utils import clean_url


load_dotenv()
logger = logging.getLogger(__name__)


def _safe_url(value) -> str:
    url = clean_url(value)
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
    payload["source_reliability"] = max(0, min(100, _int(payload.get("source_reliability"), 70)))
    payload["freshness_score"] = max(0, min(100, _int(payload.get("freshness_score"), 50)))
    payload["freshness_label"] = payload.get("freshness_label") or freshness_label(payload["freshness_score"])
    if include_score:
        payload["score"] = max(0, min(100, _int(payload.get("score"), 0)))
    return payload


def build_html_newsletter(matched_jobs, camps, rd_projects, podcasts, hackathons, news, github_issues, skill_gap, profile):
    """Render the executive briefing from the Jinja2 HTML template."""
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
    )


def send_email_newsletter(html_content, total_jobs_count):
    """Send the rendered newsletter over SMTP."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    user_email_to = os.getenv("USER_EMAIL_TO")

    if not smtp_user or not smtp_pass or not user_email_to:
        logger.error("E-posta ayarlari eksik. SMTP_USER, SMTP_PASS ve USER_EMAIL_TO degiskenlerini kontrol edin.")
        return False

    current_date_str = dt.datetime.now().strftime("%d.%m.%Y")
    logger.info("Rapor hedef adrese iletiliyor. recipient=%s", user_email_to)

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("JobHunt-Auto Platform Intelligence", smtp_user))
    msg["To"] = user_email_to
    msg["Reply-To"] = "no-reply@jobhunt.auto"
    msg["Subject"] = (
        f"JobHunt-Auto Raporu | {total_jobs_count} Doğrulanmış Pozisyon, "
        f"GitHub Fırsatları & AR-GE Çağrısı ({current_date_str})"
    )
    msg["X-Auto-Response-Suppress"] = "All"
    msg["X-Entity-Ref-ID"] = f"JOBHUNT-AUTO-{dt.datetime.now().strftime('%Y%m%d%H%M')}"

    msg.attach(MIMEText("Lütfen HTML destekleyen bir e-posta istemcisi kullanın.", "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception as exc:
        logger.error("E-posta iletim hatasi: %s", exc)
        return False

    logger.info("Kurumsal sistem raporu basariyla iletildi.")
    return True
