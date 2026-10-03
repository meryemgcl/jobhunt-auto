#!/usr/bin/env python3
"""
scripts/data_explorer.py
=========================
JobHunt-Auto Veri Keşif CLI Aracı

Kullanım:
    python scripts/data_explorer.py [komut] [seçenekler]

Komutlar:
    report          → Kapsamlı özet raporu
    jobs            → İş ilanlarını listele (filtrelenebilir)
    runs            → Koşu geçmişi
    score-trend     → Puan trendi (son 30 gün)
    companies       → En çok ilan açan şirketler
    feedback        → Geri bildirim geçmişi
    unread          → Henüz değerlendirilmemiş ilanlar
    export-csv      → CSV dışa aktarım
    export-json     → JSON dışa aktarım

Örnekler:
    python scripts/data_explorer.py report
    python scripts/data_explorer.py jobs --status sent --min-score 60
    python scripts/data_explorer.py jobs --since-days 7 --category job
    python scripts/data_explorer.py runs --last 10
    python scripts/data_explorer.py export-csv --output exports/jobs.csv
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Windows terminali için UTF-8 zorla
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Proje kökünü Python yoluna ekle
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.analytics import Analytics


def _divider(title: str = "", width: int = 70):
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{'─' * pad} {title} {'─' * pad}")
    else:
        print(f"{'─' * width}")


def _fmt_score(score) -> str:
    if score is None:
        return "—"
    s = int(score)
    if s >= 85:
        return f"\033[35m{s:>3}\033[0m"   # Mor
    if s >= 70:
        return f"\033[34m{s:>3}\033[0m"   # Mavi
    if s >= 50:
        return f"\033[32m{s:>3}\033[0m"   # Yeşil
    if s > 0:
        return f"\033[33m{s:>3}\033[0m"   # Sarı
    return f"\033[31m{s:>3}\033[0m"       # Kırmızı


def cmd_report(a: Analytics, args):
    """Kapsamlı özet raporu yazar."""
    report = a.summary_report()
    _divider("JOBHUNT-AUTO VERİ RAPORU")
    print(f"Rapor Tarihi : {report['generated_at'][:19].replace('T', ' ')} UTC")
    print(f"Toplam Kayıt : {report['total_opportunities']}")

    _divider("DURUM DAĞILIMI")
    for status, count in report["status_breakdown"].items():
        bar = "█" * min(count, 40)
        print(f"  {status:<12} {count:>5}  {bar}")

    _divider("PUAN DAĞILIMI (İş İlanları)")
    for band, count in report["score_distribution"].items():
        bar = "█" * min(count, 40)
        print(f"  {band:<18} {count:>5}  {bar}")

    _divider("SİSTEM İSTATİSTİKLERİ")
    sys_data = report["system"]
    print(f"  Toplam Koşu           : {sys_data['total_runs']}")
    print(f"  E-posta Başarı Oranı  : %{sys_data['email_success_rate_pct']}")
    print(f"  Toplam Taranan (ever) : {sys_data['total_items_ever_collected']}")
    print(f"  Toplam Eşleşen (ever) : {sys_data['total_matched_ever']}")

    _divider("GERİ BİLDİRİM ÖZETİ")
    if report["feedback"]:
        for fb, count in report["feedback"].items():
            print(f"  {fb:<12} : {count}")
    else:
        print("  Henüz geri bildirim yok.")

    if report["last_run"]:
        _divider("SON KOŞU")
        lr = report["last_run"]
        print(f"  Run ID       : {lr['run_id']}")
        print(f"  Tarih        : {lr['started_at'][:19].replace('T', ' ')} UTC")
        print(f"  Toplanan     : {lr['total_collected']}")
        print(f"  Eşleşen      : {lr['matched_count']}")
        print(f"  E-posta      : {'✅ Gönderildi' if lr['email_sent'] else '❌ Gönderilemedi'}")
    _divider()


def cmd_jobs(a: Analytics, args):
    """İş ilanlarını filtreli listeler."""
    jobs = a.all_opportunities(
        status=args.status,
        category=args.category or "job",
        min_score=args.min_score,
        source=args.source,
        since_days=args.since_days,
        limit=args.limit,
    )
    _divider(f"İŞ İLANLARI ({len(jobs)} sonuç)")

    if not jobs:
        print("  Filtrelere uygun ilan bulunamadı.")
        return

    print(f"  {'PUAN':>4}  {'DURUM':<10}  {'BAŞLIK':<40}  {'ŞİRKET':<25}  KAYNAK")
    _divider()
    for job in jobs:
        score_str = _fmt_score(job.get("latest_score"))
        title = (job.get("title") or "—")[:40]
        company = (job.get("company") or "—")[:25]
        source = (job.get("source") or "—")[:20]
        status = (job.get("status") or "—")[:10]
        print(f"  {score_str}  {status:<10}  {title:<40}  {company:<25}  {source}")
    _divider()


def cmd_runs(a: Analytics, args):
    """Koşu geçmişini gösterir."""
    runs = a.run_history(last_n=args.last)
    _divider(f"KOŞU GEÇMİŞİ (Son {len(runs)})")

    if not runs:
        print("  Kayıtlı koşu bulunamadı.")
        return

    print(f"  {'TARİH':<20}  {'TOPLANAN':>9}  {'EŞLEŞİ':>7}  {'TEKRAR':>7}  E-POSTA")
    _divider()
    for run in runs:
        date = run.get("started_at", "—")[:19].replace("T", " ")
        collected = run.get("total_collected", 0)
        matched = run.get("matched_count", 0)
        dedup = run.get("duplicate_count", 0)
        email = "✅" if run.get("email_sent") else "❌"
        print(f"  {date:<20}  {collected:>9}  {matched:>7}  {dedup:>7}  {email}")
    _divider()


def cmd_score_trend(a: Analytics, args):
    """Günlük puan trendini gösterir."""
    trend = a.average_score_trend(days=args.days)
    _divider(f"PUAN TRENDİ (Son {args.days} Gün)")

    if not trend:
        print("  Puan geçmişi bulunamadı.")
        return

    print(f"  {'TARİH':<12}  {'ORT. PUAN':>10}  {'MAX PUAN':>9}  {'TOPLAM':>7}")
    _divider()
    for row in trend:
        bar_len = int((row.get("avg_score") or 0) / 3)
        bar = "▪" * bar_len
        print(f"  {row['day']:<12}  {row['avg_score']:>10}  {row['max_score']:>9}  {row['total_scored']:>7}  {bar}")
    _divider()


def cmd_companies(a: Analytics, args):
    """En çok ilan açan şirketleri gösterir."""
    companies = a.top_companies_by_frequency(limit=args.limit)
    _divider("EN ÇOK İLAN AÇAN ŞİRKETLER")

    if not companies:
        print("  Şirket verisi bulunamadı.")
        return

    print(f"  {'ŞİRKET':<35}  {'TOPLAM':>7}  {'ORT. PUAN':>10}")
    _divider()
    for row in companies:
        company = (row.get("company") or "—")[:35]
        total = row.get("total", 0)
        avg = row.get("avg_score") or "—"
        print(f"  {company:<35}  {total:>7}  {str(avg):>10}")
    _divider()


def cmd_feedback(a: Analytics, args):
    """Geri bildirim geçmişini gösterir."""
    feedbacks = a.feedback_history()
    summary = a.feedback_summary()
    _divider("GERİ BİLDİRİM GEÇMİŞİ")

    print("  Özet:")
    for fb, count in summary.items():
        print(f"    {fb:<12} : {count}")

    if feedbacks:
        _divider()
        print(f"  {'TARİH':<12}  {'TİP':<12}  {'PUAN':>5}  {'BAŞLIK'}")
        _divider()
        for fb in feedbacks[:50]:
            date = (fb.get("created_at") or "—")[:10]
            fb_type = fb.get("feedback", "—")
            score = _fmt_score(fb.get("latest_score"))
            title = (fb.get("title") or "—")[:50]
            print(f"  {date:<12}  {fb_type:<12}  {score}  {title}")
    _divider()


def cmd_unread(a: Analytics, args):
    """Henüz değerlendirilmemiş ilanları gösterir."""
    jobs = a.unread_opportunities()
    _divider(f"DEĞERLENDİRİLMEMİŞ İLANLAR (Son 7 Gün, {len(jobs)} adet)")

    if not jobs:
        print("  Bekleyen ilan bulunamadı.")
        return

    for job in jobs:
        score = _fmt_score(job.get("latest_score"))
        title = (job.get("title") or "—")
        company = (job.get("company") or "—")
        url = job.get("url") or "—"
        print(f"\n  [{score}] {title}")
        print(f"        Şirket: {company}")
        print(f"        URL   : {url}")
    _divider()


def cmd_export_csv(a: Analytics, args):
    output = args.output or "exports/opportunities_export.csv"
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    a.export_to_csv(
        output_path=output,
        status=args.status,
        min_score=args.min_score,
        since_days=args.since_days,
    )
    print(f"✅ CSV dışa aktarıldı: {output}")


def cmd_export_json(a: Analytics, args):
    output = args.output or "exports/opportunities_export.json"
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    a.export_to_json(
        output_path=output,
        status=args.status,
        min_score=args.min_score,
        since_days=args.since_days,
    )
    print(f"✅ JSON dışa aktarıldı: {output}")


def main():
    parser = argparse.ArgumentParser(
        description="JobHunt-Auto Veri Keşif Aracı",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # report
    subparsers.add_parser("report", help="Kapsamlı özet raporu")

    # jobs
    p_jobs = subparsers.add_parser("jobs", help="İş ilanlarını listele")
    p_jobs.add_argument("--status", help="Durum filtresi (sent, seen, applied, fit, irrelevant)")
    p_jobs.add_argument("--category", help="Kategori filtresi (job, github, camp, rd...)")
    p_jobs.add_argument("--min-score", type=float, help="Minimum puan")
    p_jobs.add_argument("--source", help="Kaynak adı")
    p_jobs.add_argument("--since-days", type=int, help="Son N gün")
    p_jobs.add_argument("--limit", type=int, default=50, help="Maksimum satır sayısı")

    # runs
    p_runs = subparsers.add_parser("runs", help="Koşu geçmişi")
    p_runs.add_argument("--last", type=int, default=20, help="Son N koşu")

    # score-trend
    p_trend = subparsers.add_parser("score-trend", help="Puan trendi")
    p_trend.add_argument("--days", type=int, default=30, help="Son N gün")

    # companies
    p_comp = subparsers.add_parser("companies", help="En çok ilan açan şirketler")
    p_comp.add_argument("--limit", type=int, default=15)

    # feedback
    subparsers.add_parser("feedback", help="Geri bildirim geçmişi")

    # unread
    subparsers.add_parser("unread", help="Değerlendirilmemiş ilanlar")

    # export-csv
    p_csv = subparsers.add_parser("export-csv", help="CSV dışa aktarım")
    p_csv.add_argument("--output", help="Çıktı dosya yolu")
    p_csv.add_argument("--status", help="Durum filtresi")
    p_csv.add_argument("--min-score", type=float)
    p_csv.add_argument("--since-days", type=int)

    # export-json
    p_json = subparsers.add_parser("export-json", help="JSON dışa aktarım")
    p_json.add_argument("--output", help="Çıktı dosya yolu")
    p_json.add_argument("--status", help="Durum filtresi")
    p_json.add_argument("--min-score", type=float)
    p_json.add_argument("--since-days", type=int)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    a = Analytics()
    commands = {
        "report": cmd_report,
        "jobs": cmd_jobs,
        "runs": cmd_runs,
        "score-trend": cmd_score_trend,
        "companies": cmd_companies,
        "feedback": cmd_feedback,
        "unread": cmd_unread,
        "export-csv": cmd_export_csv,
        "export-json": cmd_export_json,
    }
    commands[args.command](a, args)


if __name__ == "__main__":
    main()
