"""
scripts/generate_static_dashboard.py
=====================================
JobHunt-Auto -- Statik Dashboard Betigi

Son 7 gunun verilerini jobhunt.db (SQLite) uzerinden okuyarak
hem terminal ciktisi hem de DASHBOARD_REPORT.md olarak ozet uretir.

Kullanim:
    python scripts/generate_static_dashboard.py
    python scripts/generate_static_dashboard.py --days 14
    python scripts/generate_static_dashboard.py --output reports/
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta, UTC
from pathlib import Path

# Proje koku src path'e ekleniyor (scripts/ icinden calisabilmek icin)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "jobhunt.db"
DEFAULT_OUTPUT = PROJECT_ROOT / "DASHBOARD_REPORT.md"


def _db_connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        print(f"[HATA] Veritabani bulunamadi: {DB_PATH}")
        print("  --> Once 'python main.py' calistirarak veritabanini olusturun.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_run_summaries(conn: sqlite3.Connection, days: int) -> list[sqlite3.Row]:
    cutoff = (datetime.now(tz=UTC) - timedelta(days=days)).isoformat()
    return conn.execute(
        """
        SELECT run_id, started_at, total_collected, matched_count,
               duplicate_count, invalid_url_count, email_sent, memory_added_count
        FROM run_summaries
        WHERE started_at >= ?
        ORDER BY started_at DESC
        """,
        (cutoff,),
    ).fetchall()


def fetch_top_opportunities(conn: sqlite3.Connection, days: int, limit: int = 10) -> list[sqlite3.Row]:
    cutoff = (datetime.now(tz=UTC) - timedelta(days=days)).isoformat()
    return conn.execute(
        """
        SELECT title, company, location, score, source, url, last_seen_at
        FROM opportunities
        WHERE last_seen_at >= ?
        ORDER BY score DESC
        LIMIT ?
        """,
        (cutoff, limit),
    ).fetchall()


def fetch_score_distribution(conn: sqlite3.Connection, days: int) -> dict[str, int]:
    cutoff = (datetime.now(tz=UTC) - timedelta(days=days)).isoformat()
    rows = conn.execute(
        """
        SELECT score FROM score_history
        WHERE recorded_at >= ?
        """,
        (cutoff,),
    ).fetchall()
    dist = {"0-49": 0, "50-69": 0, "70-84": 0, "85+": 0}
    for row in rows:
        s = row["score"] or 0
        if s < 50:
            dist["0-49"] += 1
        elif s < 70:
            dist["50-69"] += 1
        elif s < 85:
            dist["70-84"] += 1
        else:
            dist["85+"] += 1
    return dist


def fetch_source_stats(conn: sqlite3.Connection, days: int) -> list[sqlite3.Row]:
    cutoff = (datetime.now(tz=UTC) - timedelta(days=days)).isoformat()
    return conn.execute(
        """
        SELECT source, COUNT(*) as count, AVG(score) as avg_score
        FROM opportunities
        WHERE last_seen_at >= ?
        GROUP BY source
        ORDER BY count DESC
        """,
        (cutoff,),
    ).fetchall()


def build_terminal_report(
    runs: list,
    top_ops: list,
    score_dist: dict,
    source_stats: list,
    days: int,
) -> str:
    now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"\n{'='*60}",
        f"  JobHunt-Auto -- Son {days} Gun Dashboard",
        f"  Uretildi: {now}",
        f"{'='*60}",
    ]

    # Kosu ozeti
    lines.append("\n[KOSU OZETI]")
    if not runs:
        lines.append("  Bu donemde kayitli kosu bulunamadi.")
    else:
        total_collected = sum(r["total_collected"] or 0 for r in runs)
        total_matched = sum(r["matched_count"] or 0 for r in runs)
        total_sent = sum(1 for r in runs if r["email_sent"])
        lines += [
            f"  Kosu sayisi      : {len(runs)}",
            f"  Toplam taranan   : {total_collected}",
            f"  Toplam eslesen   : {total_matched}",
            f"  E-posta gonderim : {total_sent}/{len(runs)} basarili",
        ]

    # Skor dagilimi
    lines.append("\n[SKOR DAGILIMI]")
    total_scored = sum(score_dist.values())
    for band, count in score_dist.items():
        pct = (count / total_scored * 100) if total_scored else 0
        bar = "#" * int(pct / 5)
        lines.append(f"  {band:>5}  {bar:<20} {count:>4} ilan ({pct:.1f}%)")

    # En iyi ilanlar
    lines.append("\n[EN IYI 10 ESLESEN ILAN]")
    if not top_ops:
        lines.append("  Kayit bulunamadi.")
    else:
        for i, op in enumerate(top_ops, 1):
            lines.append(f"  {i:>2}. [{op['score']:>3}] {op['title']} -- {op['company']} ({op['location']})")

    # Kaynak istatistikleri
    lines.append("\n[KAYNAK ISTATISTIKLERI]")
    for src in source_stats:
        avg = src["avg_score"] or 0
        lines.append(f"  {src['source']:<30} {src['count']:>4} ilan   ort.puan: {avg:.1f}")

    lines.append(f"\n{'='*60}\n")
    return "\n".join(lines)


def build_markdown_report(
    runs: list,
    top_ops: list,
    score_dist: dict,
    source_stats: list,
    days: int,
) -> str:
    now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# JobHunt-Auto Dashboard Raporu",
        "",
        f"> Uretildi: **{now}** | Son **{days}** gun",
        "",
        "---",
        "",
        "## Kosu Ozeti",
        "",
    ]

    if not runs:
        lines.append("Bu donemde kayitli kosu bulunamadi.\n")
    else:
        total_collected = sum(r["total_collected"] or 0 for r in runs)
        total_matched = sum(r["matched_count"] or 0 for r in runs)
        total_sent = sum(1 for r in runs if r["email_sent"])
        lines += [
            "| Metrik | Deger |",
            "|--------|-------|",
            f"| Kosu sayisi | {len(runs)} |",
            f"| Toplam taranan ilan | {total_collected} |",
            f"| Toplam eslesen ilan | {total_matched} |",
            f"| Basarili e-posta | {total_sent}/{len(runs)} |",
            "",
        ]

    lines += [
        "## Skor Dagilimi",
        "",
        "| Aralik | Ilan Sayisi |",
        "|--------|-------------|",
    ]
    for band, count in score_dist.items():
        lines.append(f"| {band} | {count} |")

    lines += [
        "",
        "## En Yuksek Eslesen 10 Ilan",
        "",
        "| Skor | Pozisyon | Sirket | Konum | Kaynak |",
        "|------|----------|--------|-------|--------|",
    ]
    for op in top_ops:
        title_link = f"[{op['title']}]({op['url']})" if op["url"] else op["title"]
        lines.append(f"| {op['score']} | {title_link} | {op['company']} | {op['location']} | {op['source']} |")

    lines += [
        "",
        "## Kaynak Bazli Istatistikler",
        "",
        "| Kaynak | Ilan Sayisi | Ort. Puan |",
        "|--------|-------------|-----------|",
    ]
    for src in source_stats:
        avg = src["avg_score"] or 0
        lines.append(f"| {src['source']} | {src['count']} | {avg:.1f} |")

    lines += ["", "---", "", "*Bu rapor `scripts/generate_static_dashboard.py` tarafindan otomatik uretilmistir.*"]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="JobHunt-Auto Statik Dashboard Uretici")
    parser.add_argument("--days", type=int, default=7, help="Kac gunun verisi analiz edilecek (varsayilan: 7)")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT), help="Cikti dosyasi yolu")
    parser.add_argument("--no-file", action="store_true", help="Dosyaya yazma, yalnizca terminale yazdir")
    args = parser.parse_args()

    conn = _db_connect()
    try:
        runs = fetch_run_summaries(conn, args.days)
        top_ops = fetch_top_opportunities(conn, args.days)
        score_dist = fetch_score_distribution(conn, args.days)
        source_stats = fetch_source_stats(conn, args.days)
    finally:
        conn.close()

    terminal_report = build_terminal_report(runs, top_ops, score_dist, source_stats, args.days)
    print(terminal_report)

    if not args.no_file:
        md_report = build_markdown_report(runs, top_ops, score_dist, source_stats, args.days)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md_report, encoding="utf-8")
        print(f"[OK] Markdown raporu yazildi: {output_path}")


if __name__ == "__main__":
    main()
