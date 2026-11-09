import logging
import os
import sys
from pathlib import Path

def _configure_stdout_encoding() -> None:
    """Best-effort UTF-8 output for Windows terminals without disturbing imports."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from config import FEATURE_FLAGS, MAX_MATCHES_PER_COMPANY, MIN_MATCH_SCORE
from services.profile_analyzer.analyzer import get_profile
from services.memory import add_seen_jobs, load_seen_canonical_urls, load_seen_jobs
from services.job_collector import (
    fetch_jobs, 
    fetch_bootcamps_and_camps, 
    fetch_r_and_d_projects, 
    fetch_podcasts, 
    fetch_hackathons, 
    fetch_tech_news,
    get_source_errors,
    reset_source_errors,
)
from services.github_radar import fetch_good_first_issues
from services.analytics import analyze_market_skill_gap
from services.matcher import score_job_suitability, select_diverse_matches
from services.tracker import update_career_dashboard
from services.notification_and_meta.notifier import build_html_newsletter, send_email_newsletter
from services.logging_config import configure_logging
from services.url_utils import canonicalize_url, clean_url
from services.database import (
    enqueue_email_outbox,
    init_database,
    load_pending_email_outbox,
    load_seen_canonical_urls_from_db,
    record_email_outbox_attempt,
    record_run_summary,
    record_score_history,
    upsert_opportunities,
    utc_now_iso,
)
from services.feedback import load_feedback_index, load_feedback_keyword_weights
from services.observability import (
    build_run_summary,
    detect_source_alerts,
    summarize_job_quality,
    summarize_sources,
    write_daily_summary,
)
from services.state_io import atomic_write_text


logger = logging.getLogger(__name__)


def _check_required_env_vars(*, dry_run: bool = False) -> bool:
    """Kritik env degiskenlerinin varligini kontrol eder; degerlerini asla loglamaz."""
    if dry_run:
        return True
    required = ["SMTP_USER", "SMTP_PASS", "USER_EMAIL_TO"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        logger.warning("Eksik e-posta env degiskenleri: %s. E-posta gonderimi basarisiz olabilir.", ", ".join(missing))
        return False
    logger.info("Env kontrolu basarili. zorunlu_degiskenler=%d", len(required))
    return True


def _main_impl(*, dry_run: bool = False) -> bool:
    run_id = configure_logging()
    started_at = utc_now_iso()
    logger.info(
        "JobHunt-Auto deterministik motor baslatiliyor. run_id=%s dry_run=%s",
        run_id,
        dry_run,
    )

    # 1. Profil ve kalici state'i yukle
    feedback_index = {}
    feedback_keyword_weights = {}
    pending_before_run = []
    try:
        profile = get_profile()
        seen_jobs = load_seen_canonical_urls()
        if not dry_run:
            init_database()
            pending_before_run = load_pending_email_outbox(limit=1)
            db_seen_jobs = load_seen_canonical_urls_from_db()
            json_backfill_count = 0

            json_seen_records = load_seen_jobs()
            missing_json_records = [
                record for record in json_seen_records
                if record["canonical_url"] not in db_seen_jobs
            ]
            if missing_json_records:
                json_backfill_count = upsert_opportunities(missing_json_records, status="sent")
                db_seen_jobs = load_seen_canonical_urls_from_db()

            feedback_index = load_feedback_index()
            feedback_keyword_weights = load_feedback_keyword_weights()
            seen_jobs = seen_jobs | db_seen_jobs
            logger.info(
                "Durable state loaded. json_backfill=%s db_seen=%s feedback_records=%s feedback_terms=%s",
                json_backfill_count,
                len(db_seen_jobs),
                len(feedback_index),
                len(feedback_keyword_weights),
            )
        else:
            logger.info("Preview mode: only JSON memory is read; database and feedback state are untouched.")
    except Exception as exc:
        logger.error("Kritik Hata: Profil, veritabanı veya hafıza başlatılamadı. error=%s", exc)
        return False  # Sessizce devam edersek filtreler boş olduğu için 1000'lerce mail atar. Kapatmak zorundayız.

    logger.info("Toplam %s daha once gorulmus ilan hafizada.", len(seen_jobs))

    # 2. Tum Kategorilerde Canli Veri Topla
    reset_source_errors()
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
    source_errors = get_source_errors()
    for alert in detect_source_alerts(source_counts, source_errors=source_errors):
        logger.warning("Kaynak alarmi: %s", alert)

    # 3. Piyasa Yetenek Acigi (Skill Gap) Analizi (Adim 1)
    skill_gap = {}
    if FEATURE_FLAGS.get("ENABLE_SKILL_GAP_ANALYSIS", True):
        skill_gap = analyze_market_skill_gap(raw_jobs, profile.get("core_skills", []))
        logger.info("Skill gap analizi: %s", skill_gap.get('summary_text', ''))

    # 4. Ilanlari ve diger kaynaklari tekillestirme (Deduplication Pipeline)
    eligible_jobs = []
    scored_jobs = []
    new_items_for_memory = []
    seen_this_run = set()
    duplicate_count = 0
    invalid_url_count = 0

    def generate_dedup_key(item: dict) -> str:
        return canonicalize_url(item.get("url"))

    def _filter_and_track(items_list):
        nonlocal duplicate_count, invalid_url_count
        new_items = []
        for item in items_list:
            url = clean_url(item.get("url"))
            canonical_url = canonicalize_url(url)
            if not canonical_url:
                invalid_url_count += 1
                continue

            item["url"] = url
            
            dedup_key = generate_dedup_key(item)
            item["canonical_url"] = canonical_url

            if dedup_key in seen_jobs or dedup_key in seen_this_run:
                duplicate_count += 1
                continue

            seen_this_run.add(dedup_key)
            new_items.append(item)
            new_items_for_memory.append(item)  # SIFIR PUANLI OLSA BİLE TÜM YENİ VERİLER HAFIZAYA YAZILIR
        return new_items

    # 4.1 Tum diger kaynaklari (haberler, kamplar, issue'lar vb.) filtrele
    new_github_issues = _filter_and_track(github_issues)
    new_camps = _filter_and_track(camps)
    new_rd_projects = _filter_and_track(rd_projects)
    new_podcasts = _filter_and_track(podcasts)
    new_hackathons = _filter_and_track(hackathons)
    new_news = _filter_and_track(news)

    # 4.2 Is ilanlarini filtrele ve puanla
    new_raw_jobs = _filter_and_track(raw_jobs)

    for job in new_raw_jobs:
        score, reason = score_job_suitability(
            job,
            profile,
            feedback_index=feedback_index,
            feedback_keyword_weights=feedback_keyword_weights,
        )
        job["score"] = score
        job["match_reason"] = reason
        scored_jobs.append(job)

    scored_jobs.sort(key=lambda x: x["score"], reverse=True)
    eligible_jobs = [job for job in scored_jobs if job["score"] >= MIN_MATCH_SCORE]
    matched_jobs = select_diverse_matches(
        eligible_jobs,
        minimum_score=MIN_MATCH_SCORE,
        max_per_company=MAX_MATCHES_PER_COMPANY,
    )
    job_source_quality = summarize_job_quality(
        raw_jobs,
        matched_urls={
            str(job.get("canonical_url") or job.get("url") or "")
            for job in matched_jobs
        },
    )
    run_stats = {
        "total_scanned": len(raw_jobs),
        "dedup_filtered": duplicate_count,
        "negative_filtered": sum(1 for j in scored_jobs if j["score"] == 0),
        "low_score_filtered": sum(1 for j in scored_jobs if 0 < j["score"] < MIN_MATCH_SCORE),
        "job_source_quality": job_source_quality,
    }

    logger.info(
        "Deduplication & Skorlama tamamlandi. matched=%s duplicates=%s invalid_urls=%s total_new_items=%s",
        len(matched_jobs),
        duplicate_count,
        invalid_url_count,
        len(new_items_for_memory)
    )

    if dry_run:
        html_report = build_html_newsletter(
            matched_jobs=matched_jobs,
            camps=new_camps,
            rd_projects=new_rd_projects,
            podcasts=new_podcasts,
            hackathons=new_hackathons,
            news=new_news,
            github_issues=new_github_issues,
            skill_gap=skill_gap,
            profile=profile,
            run_stats=run_stats,
        )
        preview_path = Path(os.getenv("JOBHUNT_PREVIEW_PATH", "data/newsletter_preview.html"))
        try:
            atomic_write_text(preview_path, html_report)
        except OSError as exc:
            logger.error("Newsletter preview could not be written. path=%s error=%s", preview_path, exc)
            return False

        logger.info(
            "Preview complete; no email, database, memory, dashboard, or run-summary changes were made. "
            "path=%s jobs=%s sources=%s",
            preview_path,
            len(matched_jobs),
            len(source_counts),
        )
        return True

    html_report = build_html_newsletter(
        matched_jobs=matched_jobs,
        camps=new_camps,
        rd_projects=new_rd_projects,
        podcasts=new_podcasts,
        hackathons=new_hackathons,
        news=new_news,
        github_issues=new_github_issues,
        skill_gap=skill_gap,
        profile=profile,
        run_stats=run_stats,
    )
    logger.info("HTML bulten derlendi. content_length=%s", len(html_report))

    queued = False
    if new_items_for_memory and not pending_before_run:
        try:
            queued = enqueue_email_outbox(
                run_id,
                html_report,
                len(matched_jobs),
                new_items_for_memory,
            )
            if not queued:
                logger.error("Newsletter was not added to the delivery outbox; persistent state was not updated.")
                return False
        except Exception as exc:
            logger.error("Newsletter could not be persisted to the delivery outbox. error=%s", exc)
            return False
    elif pending_before_run:
        logger.info(
            "An older newsletter is still pending; current discoveries will be rescanned after it is delivered."
        )

    memory_added_count = 0
    if not pending_before_run:
        try:
            upserted_count = upsert_opportunities(
                scored_jobs + new_github_issues + new_camps + new_rd_projects + new_podcasts + new_hackathons + new_news,
                status="seen",
            )
            history_count = record_score_history(scored_jobs, run_id=run_id)
            memory_added_count = add_seen_jobs(new_items_for_memory)
            logger.info("Durable score state updated. opportunities=%s score_history=%s", upserted_count, history_count)
            logger.info("%s yeni kayit tarama sonrasinda hafizaya eklendi.", memory_added_count)
        except Exception as exc:
            logger.error("Taranan fırsatlar kalici state'e yazilamadi; e-posta gonderimi durduruldu. error=%s", exc)
            return False
    else:
        logger.info("Current discoveries were not marked seen because the previous digest is awaiting delivery.")

    # 5. DASHBOARD.md ve applications.json Guncelle (Adim 4)
    dashboard_updated = False
    if not pending_before_run and FEATURE_FLAGS.get("ENABLE_DASHBOARD_TRACKING", True):
        dashboard_updated = update_career_dashboard(len(raw_jobs), len(matched_jobs), skill_gap)
    logger.info("State/dashboard guncelleme sonucu: updated=%s", dashboard_updated)

    pending_batches = load_pending_email_outbox(limit=1)
    delivery_attempted = bool(pending_batches)
    sent = True
    if pending_batches:
        pending_batch = pending_batches[0]
        try:
            sent = send_email_newsletter(
                pending_batch["html_content"],
                pending_batch["total_job_count"],
                message_id=pending_batch["id"],
            )
            attempt_recorded = record_email_outbox_attempt(
                pending_batch["id"],
                success=sent,
                error="" if sent else "SMTP delivery failed; see run logs for details.",
            )
            if not attempt_recorded:
                logger.error(
                    "Email outbox state was not updated after delivery attempt. outbox_id=%s",
                    pending_batch["id"],
                )
                sent = False
        except Exception as exc:
            logger.error("Email outbox delivery failed. outbox_id=%s error=%s", pending_batch["id"], exc)
            sent = False
            try:
                attempt_recorded = record_email_outbox_attempt(
                    pending_batch["id"],
                    success=False,
                    error=str(exc),
                )
                if not attempt_recorded:
                    logger.error(
                        "Failed delivery could not be recorded in the outbox. outbox_id=%s",
                        pending_batch["id"],
                    )
            except Exception as state_exc:
                logger.error(
                    "Email outbox retry state could not be updated. outbox_id=%s error=%s",
                    pending_batch["id"],
                    state_exc,
                )
        logger.info(
            "Outbox delivery attempt completed. outbox_id=%s sent=%s queued_this_run=%s",
            pending_batch["id"],
            sent,
            queued,
        )
    else:
        logger.info("No new newsletter to deliver; email sending skipped.")

    run_summary = build_run_summary(
        run_id=run_id,
        started_at=started_at,
        total_collected=len(collected_opportunities),
        matched_count=len(matched_jobs),
        duplicate_count=duplicate_count,
        invalid_url_count=invalid_url_count,
        email_sent=sent and delivery_attempted,
        dashboard_updated=bool(dashboard_updated),
        memory_added_count=memory_added_count,
        source_counts=source_counts,
        source_errors=source_errors,
        job_source_quality=job_source_quality,
    )
    try:
        record_run_summary(run_summary)
        write_daily_summary(run_summary)
    except Exception as exc:
        logger.error("Run gozlemlenebilirlik state'i kaydedilemedi. error=%s", exc)

    if sent:
        logger.info("Run completed. email_sent=%s", delivery_attempted)
        return True

    logger.error("Bülten e-posta ile iletilemedi; daha sonra denenmek üzere outbox'ta bekliyor.")
    return False

def main(*, dry_run: bool = False) -> bool:
    """JobHunt-Auto ana calistirma girisi (global exception handling ile sarmalanmis)."""
    try:
        _check_required_env_vars(dry_run=dry_run)
        return _main_impl(dry_run=dry_run)
    except KeyboardInterrupt:
        logger.info("Kullanici tarafindan durduruldu (KeyboardInterrupt).")
        return False
    except Exception as exc:
        logger.critical(
            "Beklenmeyen kritik hata olustu. error=%s",
            exc,
            exc_info=True,
        )
        return False


if __name__ == "__main__":
    _configure_stdout_encoding()
    import argparse

    parser = argparse.ArgumentParser(description="Run the deterministic JobHunt-Auto engine.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and score listings, write an HTML preview, and leave persistent state unchanged (default).",
    )
    mode.add_argument(
        "--send",
        action="store_true",
        help="Persist scanned listings and send the newsletter by email.",
    )
    arguments = parser.parse_args()
    raise SystemExit(0 if main(dry_run=not arguments.send) else 1)
