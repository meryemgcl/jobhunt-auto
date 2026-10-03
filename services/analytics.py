"""
services/analytics.py
======================
JobHunt-Auto Analytics & Data Access Layer

SQLite veritabanı üzerinde profesyonel veri sorgulama,
raporlama ve dışa aktarma fonksiyonları.

Kullanım:
    from services.analytics import Analytics, analyze_market_skill_gap
    a = Analytics()
    df = a.all_opportunities()
    report = a.summary_report()
    skill_gap = analyze_market_skill_gap(raw_jobs, core_skills)
"""
from __future__ import annotations

import collections
import csv
import io
import json
import datetime as dt
from pathlib import Path
from typing import Any

from services.database import connect, init_database


def analyze_market_skill_gap(jobs: list[dict], core_skills: list[str]) -> dict:
    """Taranan ilanlardan piyasanın en çok talep ettiği teknolojileri çıkarır.

    Args:
        jobs:        Ham iş ilanı listesi (title, description, tags alanlarıyla).
        core_skills: Kullanıcının mevcut beceri listesi (profilden).

    Returns:
        Piyasa analizi özeti; top_market_demands ve summary_text içerir.
    """
    if not jobs:
        return {"top_market_demands": [], "summary_text": "", "total_analyzed": 0}

    COMMON_TECH_TERMS = [
        "python", "javascript", "typescript", "java", "kotlin", "swift",
        "go", "golang", "rust", "c#", "c++", "ruby", "php", "scala",
        "react", "angular", "vue", "nextjs", "nodejs", "django", "flask",
        "fastapi", "spring", "express", "tensorflow", "pytorch", "keras",
        "pandas", "numpy", "scikit", "sql", "postgresql", "mysql", "mongodb",
        "redis", "elasticsearch", "docker", "kubernetes", "aws", "azure",
        "gcp", "git", "linux", "rest", "graphql", "machine learning",
        "deep learning", "nlp", "generative ai", "llm", "data science",
        "devops", "ci/cd", "agile", "scrum",
    ]

    skill_counter: dict[str, int] = collections.Counter()
    for job in jobs:
        text = " ".join([
            str(job.get("title") or ""),
            str(job.get("description") or ""),
            " ".join(str(t) for t in job.get("tags", [])),
        ]).lower()

        for term in COMMON_TECH_TERMS:
            if term in text:
                skill_counter[term.upper()] += 1

    skill_gaps = [
        {"tech": tech, "demand_count": count}
        for tech, count in skill_counter.most_common(3)
    ]

    total_analyzed = len(jobs)
    summary_text = ""
    if skill_gaps:
        summary_text = (
            f"Taranan {total_analyzed} pozisyonun analizinde en çok talep edilen "
            "ve portfolyona eklemen önerilen teknolojiler: "
            + ", ".join(f"{g['tech']} ({g['demand_count']} ilanda)" for g in skill_gaps)
            + "."
        )

    return {
        "top_market_demands": skill_gaps,
        "total_analyzed": total_analyzed,
        "summary_text": summary_text,
    }


class Analytics:
    """Tüm tarihsel verilere erişim için yüksek seviyeli API."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = db_path
        init_database(self.db_path)

    # ─────────────────────────────────────────────
    # 1. FIRSATLAR (Opportunities)
    # ─────────────────────────────────────────────

    def all_opportunities(
        self,
        status: str | None = None,
        category: str | None = None,
        min_score: float | None = None,
        source: str | None = None,
        since_days: int | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Tüm fırsatları filtreli olarak getirir.

        Args:
            status:     'seen', 'sent', 'fit', 'irrelevant', 'applied'
            category:   'job', 'github', 'camp', 'rd', 'podcast', 'hackathon', 'news'
            min_score:  Minimum uygunluk puanı (0–98)
            source:     Kaynak adı (örn. 'Remotive', 'DuckDuckGo Search')
            since_days: Son N günün verisi
            limit:      Maksimum satır sayısı
        """
        query = "SELECT * FROM opportunities WHERE 1=1"
        params: list[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if category:
            query += " AND category = ?"
            params.append(category)
        if min_score is not None:
            query += " AND latest_score >= ?"
            params.append(min_score)
        if source:
            query += " AND source = ?"
            params.append(source)
        if since_days is not None:
            cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=since_days)).isoformat()
            query += " AND first_seen_at >= ?"
            params.append(cutoff)

        query += " ORDER BY latest_score DESC NULLS LAST, last_seen_at DESC"
        query += f" LIMIT {int(limit)}"

        with connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def matched_jobs(self, min_score: float = 50, limit: int = 100) -> list[dict[str, Any]]:
        """Eşleşme eşiğini geçen iş ilanlarını getirir."""
        return self.all_opportunities(
            category="job", min_score=min_score, limit=limit
        )

    def applied_jobs(self) -> list[dict[str, Any]]:
        """Başvurulan ilanları getirir."""
        return self.all_opportunities(status="applied")

    def top_jobs_by_score(self, n: int = 10) -> list[dict[str, Any]]:
        """Tüm zamanların en yüksek puanlı n ilanını getirir."""
        return self.matched_jobs(limit=n)

    def opportunities_by_source(self) -> dict[str, int]:
        """Her kaynak için toplam ilan sayısını döndürür."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT source, COUNT(*) as cnt FROM opportunities GROUP BY source ORDER BY cnt DESC"
            ).fetchall()
        return {row["source"]: row["cnt"] for row in rows}

    def opportunities_by_status(self) -> dict[str, int]:
        """Her durum için toplam sayıyı döndürür."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM opportunities GROUP BY status ORDER BY cnt DESC"
            ).fetchall()
        return {row["status"]: row["cnt"] for row in rows}

    # ─────────────────────────────────────────────
    # 2. PUAN GEÇMİŞİ (Score History)
    # ─────────────────────────────────────────────

    def score_history(
        self,
        canonical_url: str | None = None,
        run_id: str | None = None,
        since_days: int | None = None,
    ) -> list[dict[str, Any]]:
        """Tüm veya belirli bir ilanın puan geçmişini getirir."""
        query = "SELECT * FROM score_history WHERE 1=1"
        params: list[Any] = []

        if canonical_url:
            query += " AND canonical_url = ?"
            params.append(canonical_url)
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if since_days is not None:
            cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=since_days)).isoformat()
            query += " AND observed_at >= ?"
            params.append(cutoff)

        query += " ORDER BY observed_at DESC"

        with connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def average_score_trend(self, days: int = 30) -> list[dict[str, Any]]:
        """Son N güne göre günlük ortalama puan trendini verir."""
        cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).isoformat()
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    DATE(observed_at) as day,
                    ROUND(AVG(score), 1) as avg_score,
                    MAX(score) as max_score,
                    COUNT(*) as total_scored
                FROM score_history
                WHERE observed_at >= ?
                GROUP BY day
                ORDER BY day ASC
                """,
                (cutoff,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ─────────────────────────────────────────────
    # 3. KOŞU ÖZETLERİ (Run History)
    # ─────────────────────────────────────────────

    def run_history(self, last_n: int = 30) -> list[dict[str, Any]]:
        """Son N koşunun özetini getirir."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT run_id, started_at, finished_at,
                       total_collected, matched_count, duplicate_count,
                       email_sent, memory_added_count, source_counts_json
                FROM run_summaries
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (last_n,),
            ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["source_counts"] = json.loads(d.pop("source_counts_json", "{}"))
            result.append(d)
        return result

    def last_run(self) -> dict[str, Any] | None:
        """En son koşunun özetini getirir."""
        history = self.run_history(last_n=1)
        return history[0] if history else None

    def run_success_rate(self) -> dict[str, Any]:
        """E-posta gönderim başarı oranını hesaplar."""
        with connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) as total_runs,
                    SUM(email_sent) as successful_sends,
                    SUM(total_collected) as total_items_ever,
                    SUM(matched_count) as total_matched_ever,
                    SUM(memory_added_count) as total_saved_ever
                FROM run_summaries
                """
            ).fetchone()
        if not row:
            return {}
        d = dict(row)
        total = d["total_runs"] or 1
        d["success_rate_pct"] = round(d["successful_sends"] / total * 100, 1)
        return d

    # ─────────────────────────────────────────────
    # 4. GERİ BİLDİRİM (Feedback)
    # ─────────────────────────────────────────────

    def feedback_history(self) -> list[dict[str, Any]]:
        """Verilen tüm geri bildirimleri ilan detaylarıyla getirir."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    f.id, f.feedback, f.note, f.created_at,
                    o.title, o.company, o.source, o.latest_score, o.url
                FROM feedback f
                JOIN opportunities o ON f.canonical_url = o.canonical_url
                ORDER BY f.created_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def feedback_summary(self) -> dict[str, int]:
        """Geri bildirim tiplerinin özet sayımını döndürür."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT feedback, COUNT(*) as cnt FROM feedback GROUP BY feedback"
            ).fetchall()
        return {row["feedback"]: row["cnt"] for row in rows}

    # ─────────────────────────────────────────────
    # 5. GELİŞMİŞ ANALİTİK
    # ─────────────────────────────────────────────

    def top_companies_by_frequency(self, limit: int = 20) -> list[dict[str, Any]]:
        """En çok ilan açan şirketleri listeler."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT company, COUNT(*) as total, ROUND(AVG(latest_score), 1) as avg_score
                FROM opportunities
                WHERE category = 'job' AND company != ''
                GROUP BY company
                ORDER BY total DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def score_distribution(self) -> dict[str, int]:
        """Puanların dağılımını bantlar halinde döndürür (0-20, 20-40 vb.)."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    CASE
                        WHEN latest_score IS NULL THEN 'Puansız'
                        WHEN latest_score = 0     THEN 'Elendi (0)'
                        WHEN latest_score < 20    THEN '1-19'
                        WHEN latest_score < 40    THEN '20-39'
                        WHEN latest_score < 50    THEN '40-49'
                        WHEN latest_score < 70    THEN '50-69'
                        WHEN latest_score < 85    THEN '70-84'
                        ELSE '85-98 (Yüksek)'
                    END as band,
                    COUNT(*) as cnt
                FROM opportunities
                WHERE category = 'job'
                GROUP BY band
                ORDER BY MIN(COALESCE(latest_score, -1)) ASC
                """
            ).fetchall()
        return {row["band"]: row["cnt"] for row in rows}

    def daily_collection_stats(self, days: int = 30) -> list[dict[str, Any]]:
        """Son N gün için günlük toplama istatistiklerini döndürür."""
        cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).isoformat()
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    DATE(started_at) as day,
                    COUNT(*) as runs,
                    SUM(total_collected) as collected,
                    SUM(matched_count) as matched,
                    SUM(email_sent) as emails_sent
                FROM run_summaries
                WHERE started_at >= ?
                GROUP BY day
                ORDER BY day ASC
                """,
                (cutoff,),
            ).fetchall()
        return [dict(row) for row in rows]

    def unread_opportunities(self) -> list[dict[str, Any]]:
        """Son 7 günde gelen, henüz geri bildirim verilmemiş ilanları getirir."""
        cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=7)).isoformat()
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT o.*
                FROM opportunities o
                LEFT JOIN feedback f ON o.canonical_url = f.canonical_url
                WHERE o.status IN ('sent', 'seen')
                  AND o.category = 'job'
                  AND o.latest_score >= 40
                  AND o.first_seen_at >= ?
                  AND f.id IS NULL
                ORDER BY o.latest_score DESC
                """,
                (cutoff,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ─────────────────────────────────────────────
    # 6. ÖZET RAPOR
    # ─────────────────────────────────────────────

    def summary_report(self) -> dict[str, Any]:
        """Sistemin tüm zamanlarına ait kapsamlı özet raporu."""
        status_counts = self.opportunities_by_status()
        source_counts = self.opportunities_by_source()
        fb_summary = self.feedback_summary()
        run_stats = self.run_success_rate()
        dist = self.score_distribution()
        last = self.last_run()

        return {
            "generated_at": dt.datetime.now(dt.UTC).isoformat(),
            "total_opportunities": sum(status_counts.values()),
            "status_breakdown": status_counts,
            "top_sources": dict(list(source_counts.items())[:5]),
            "score_distribution": dist,
            "feedback": fb_summary,
            "system": {
                "total_runs": run_stats.get("total_runs", 0),
                "email_success_rate_pct": run_stats.get("success_rate_pct", 0),
                "total_items_ever_collected": run_stats.get("total_items_ever", 0),
                "total_matched_ever": run_stats.get("total_matched_ever", 0),
            },
            "last_run": last,
        }

    # ─────────────────────────────────────────────
    # 7. DIŞA AKTARIM (Export)
    # ─────────────────────────────────────────────

    def export_to_csv(
        self,
        output_path: str | Path | None = None,
        **filter_kwargs: Any,
    ) -> str:
        """Fırsatları CSV dosyasına aktarır. Yol verilmezse string döndürür."""
        rows = self.all_opportunities(**filter_kwargs)
        if not rows:
            return ""

        output = io.StringIO()
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        csv_content = output.getvalue()

        if output_path:
            Path(output_path).write_text(csv_content, encoding="utf-8")

        return csv_content

    def export_to_json(
        self,
        output_path: str | Path | None = None,
        **filter_kwargs: Any,
    ) -> str:
        """Fırsatları JSON dosyasına aktarır. Yol verilmezse string döndürür."""
        rows = self.all_opportunities(**filter_kwargs)
        json_content = json.dumps(rows, ensure_ascii=False, indent=2)

        if output_path:
            Path(output_path).write_text(json_content, encoding="utf-8")

        return json_content
