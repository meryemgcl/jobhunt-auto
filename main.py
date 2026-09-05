import logging
import sys

def _configure_stdout_encoding() -> None:
    """Best-effort UTF-8 output for Windows terminals without disturbing imports."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from config import FEATURE_FLAGS
from services.profile_analyzer.analyzer import get_mock_profile
from services.memory import add_seen_jobs, load_seen_canonical_urls, load_seen_jobs
from services.job_collector import (
    fetch_jobs, 
    fetch_bootcamps_and_camps, 
    fetch_r_and_d_projects, 
    fetch_podcasts, 
    fetch_hackathons, 
    fetch_tech_news
)
from services.github_radar import fetch_good_first_issues
from services.analytics import analyze_market_skill_gap
from services.matcher import score_job_suitability
from services.tracker import update_career_dashboard
from services.notification_and_meta.notifier import build_html_newsletter, send_email_newsletter
from services.logging_config import configure_logging
from services.url_utils import canonicalize_url, clean_url
from services.database import (
    init_database,
    load_seen_canonical_urls_from_db,
    record_run_summary,
    record_score_history,
    upsert_opportunities,
    utc_now_iso,
)
from services.feedback import load_feedback_index, load_feedback_keyword_weights
from services.observability import build_run_summary, detect_source_alerts, summarize_sources, write_daily_summary


logger = logging.getLogger(__name__)


def main() -> bool:
    run_id = configure_logging()
    started_at = utc_now_iso()
    logger.info("JobHunt-Auto gelismis deterministik motor baslatiliyor. run_id=%s", run_id)

    # 1. Profil ve Hafizayi Yukle
    profile = get_mock_profile()
    seen_jobs = load_seen_canonical_urls()
    feedback_index = {}
    feedback_keyword_weights = {}
    try:
        init_database()
        json_seen_records = load_seen_jobs()
        if json_seen_records:
            upsert_opportunities(json_seen_records, status="sent")
        db_seen_jobs = load_seen_canonical_urls_from_db()
        feedback_index = load_feedback_index()
        feedback_keyword_weights = load_feedback_keyword_weights()
        seen_jobs = seen_jobs | db_seen_jobs
        logger.info(
            "SQLite hafizasi yuklendi. json_backfill=%s db_seen=%s feedback_records=%s feedback_terms=%s",
            len(json_seen_records),
            len(db_seen_jobs),
            len(feedback_index),
            len(feedback_keyword_weights),
        )
    except Exception as exc:
        logger.error("SQLite state hazirlanamadi; JSON hafiza ile devam ediliyor. error=%s", exc)
    logger.info("Toplam %s daha once gorulmus ilan hafizada.", len(seen_jobs))

    # 2. Tum Kategorilerde Canli Veri Topla
    logger.info("1/7: Turkiye ve global ilanlar toplaniyor.")
    raw_jobs = fetch_jobs()
    logger.info("Toplam %s pozisyon tarandi.", len(raw_jobs))

    logger.info("2/7: GitHub Good First Issue ve acik kaynak radari taraniyor.")
    github_issues = fetch_good_first_issues() if FEATURE_FLAGS.get("ENABLE_GITHUB_RADAR", True) else []
    logger.info("%s acik kaynak katki firsati bulundu.", len(github_issues))

    logger.info("3/7: Ucretsiz bootcamp ve egitim kamplari derleniyor.")
    camps = fetch_bootcamps_and_camps()
    logger.info("%s kamp ve akademi programi hazirlandi.", len(camps))

    logger.info("4/7: AR-GE ve TUBITAK 2209 ogrenci projeleri kontrol ediliyor.")
    rd_projects = fetch_r_and_d_projects()
    logger.info("%s AR-GE firsati eklendi.", len(rd_projects))

    logger.info("5/7: Haftalik gelistirici ve teknoloji podcastleri derleniyor.")
    podcasts = fetch_podcasts()
    logger.info("%s podcast derlendi.", len(podcasts))

    logger.info("6/7: Aktif yarisma ve hackathon platformlari listeleniyor.")
    hackathons = fetch_hackathons()
    logger.info("%s yarisma platformu hazirlandi.", len(hackathons))

    logger.info("7/7: Guncel teknoloji ve Python haberleri cekiliyor.")
    news = fetch_tech_news()
    logger.info("%s haber eklendi.", len(news))

    collected_opportunities = raw_jobs + github_issues + camps + rd_projects + podcasts + hackathons + news
    source_counts = summarize_sources(collected_opportunities)
    for alert in detect_source_alerts(source_counts):
        logger.warning("Kaynak alarmi: %s", alert)

    # 3. Piyasa Yetenek Acigi (Skill Gap) Analizi (Adim 1)
    skill_gap = {}
    if FEATURE_FLAGS.get("ENABLE_SKILL_GAP_ANALYSIS", True):
        skill_gap = analyze_market_skill_gap(raw_jobs, profile.get("core_skills", []))
        logger.info("Skill gap analizi: %s", skill_gap.get('summary_text', ''))

    # 4. Ilanlari canonical URL ile tekillestirme ve uyum puanlamasi
    matched_jobs = []
    scored_jobs = []
    new_jobs_for_memory = []
    seen_this_run = set()
    duplicate_count = 0
    invalid_url_count = 0

    for job in raw_jobs:
        url = clean_url(job.get("url"))
        canonical_url = canonicalize_url(url)
        if not canonical_url:
            invalid_url_count += 1
            continue

        job["url"] = url
        job["canonical_url"] = canonical_url

        if canonical_url in seen_jobs or canonical_url in seen_this_run:
            duplicate_count += 1
            continue

        seen_this_run.add(canonical_url)

        score, reason = score_job_suitability(
            job,
            profile,
            feedback_index=feedback_index,
            feedback_keyword_weights=feedback_keyword_weights,
        )
        job["score"] = score
        job["match_reason"] = reason
        scored_jobs.append(job)

        # %50 ve uzeri uygunluktaki ilanlari listeye al
        if score >= 50:
            matched_jobs.append(job)
            new_jobs_for_memory.append(job)

    matched_jobs.sort(key=lambda x: x["score"], reverse=True)
    logger.info(
        "Skorlama tamamlandi. matched=%s duplicates=%s invalid_urls=%s",
        len(matched_jobs),
        duplicate_count,
        invalid_url_count,
    )

    try:
        upserted_count = upsert_opportunities(
            scored_jobs + github_issues + camps + rd_projects + podcasts + hackathons + news,
            status="seen",
        )
        history_count = record_score_history(scored_jobs, run_id=run_id)
        logger.info("SQLite skor state guncellendi. opportunities=%s score_history=%s", upserted_count, history_count)
    except Exception as exc:
        logger.error("SQLite skor state guncellenemedi. error=%s", exc)

    # 5. DASHBOARD.md ve applications.json Guncelle (Adim 4)
    dashboard_updated = False
    if FEATURE_FLAGS.get("ENABLE_DASHBOARD_TRACKING", True):
        dashboard_updated = update_career_dashboard(len(raw_jobs), len(matched_jobs), skill_gap)
    logger.info("State/dashboard guncelleme sonucu: updated=%s", dashboard_updated)

    # 6. Zengin Kurumsal HTML E-posta Bültenini Oluştur
    html_report = build_html_newsletter(
        matched_jobs=matched_jobs,
        camps=camps,
        rd_projects=rd_projects,
        podcasts=podcasts,
        hackathons=hackathons,
        news=news,
        github_issues=github_issues,
        skill_gap=skill_gap,
        profile=profile
    )
    logger.info("HTML bulten derlendi. content_length=%s", len(html_report))

    # 7. E-Postayı Gönder
    sent = send_email_newsletter(html_report, len(matched_jobs))
    logger.info("Rapor gonderim sonucu: sent=%s", sent)

    # 8. Hafızayı Güncelle
    memory_added_count = 0
    if sent and new_jobs_for_memory:
        memory_added_count = add_seen_jobs(new_jobs_for_memory)
        logger.info("%s yeni ilan/firsat structured memory formatinda kaydedildi.", memory_added_count)
        try:
            upsert_opportunities(new_jobs_for_memory, status="sent")
        except Exception as exc:
            logger.error("SQLite sent state guncellenemedi. error=%s", exc)

    run_summary = build_run_summary(
        run_id=run_id,
        started_at=started_at,
        total_collected=len(collected_opportunities),
        matched_count=len(matched_jobs),
        duplicate_count=duplicate_count,
        invalid_url_count=invalid_url_count,
        email_sent=sent,
        dashboard_updated=bool(dashboard_updated),
        memory_added_count=memory_added_count,
        source_counts=source_counts,
    )
    try:
        record_run_summary(run_summary)
        write_daily_summary(run_summary)
    except Exception as exc:
        logger.error("Run gozlemlenebilirlik state'i kaydedilemedi. error=%s", exc)

    if sent:
        logger.info("Kurumsal kariyer istihbarat bulteni basariyla derlendi ve gonderildi.")
        return True

    logger.error("Bulten derlendi ancak e-posta gonderilemedi; hafiza guncellenmedi.")
    return False

if __name__ == "__main__":
    _configure_stdout_encoding()
    raise SystemExit(0 if main() else 1)
