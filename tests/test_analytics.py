"""
tests/test_analytics.py
========================
Analytics sınıfı ve analyze_market_skill_gap fonksiyonu için kapsamlı testler.
Geçici SQLite DB (tmp_path fixture) kullanılır.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from services.analytics import Analytics, analyze_market_skill_gap


# ─────────────────────────────────────────────
# Yardımcı: Geçici DB hazırla
# ─────────────────────────────────────────────

def _make_analytics(tmp_path: Path) -> Analytics:
    """tmp_path içinde gerçek bir SQLite DB oluşturup Analytics döndürür."""
    db_file = tmp_path / "test_jobhunt.db"
    return Analytics(db_path=str(db_file))


def _insert_opportunity(db_path: str, **kwargs):
    """Test verisi eklemek için yardımcı fonksiyon."""
    defaults = {
        "canonical_url": "https://example.com/job/1",
        "url": "https://example.com/job/1",
        "title": "Test Job",
        "company": "TestCo",
        "source": "TestSource",
        "category": "job",
        "first_seen_at": "2026-01-01T00:00:00+00:00",
        "last_seen_at": "2026-01-01T00:00:00+00:00",
        "latest_score": 75.0,
        "latest_match_reason": "Test reason",
        "source_reliability": 70,
        "freshness_score": 50,
        "status": "seen",
        "metadata_json": "{}",
    }
    defaults.update(kwargs)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """INSERT OR REPLACE INTO opportunities
           (canonical_url, url, title, company, source, category,
            first_seen_at, last_seen_at, latest_score, latest_match_reason,
            source_reliability, freshness_score, status, metadata_json)
           VALUES (:canonical_url, :url, :title, :company, :source, :category,
                   :first_seen_at, :last_seen_at, :latest_score, :latest_match_reason,
                   :source_reliability, :freshness_score, :status, :metadata_json)""",
        defaults,
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# 1. summary_report — boş DB
# ─────────────────────────────────────────────

def test_summary_report_empty_db(tmp_path):
    """Boş DB'de summary_report() hata vermeden çalışmalı."""
    a = _make_analytics(tmp_path)
    report = a.summary_report()

    assert isinstance(report, dict)
    assert "generated_at" in report
    assert report["total_opportunities"] == 0
    assert report["status_breakdown"] == {}
    assert report["last_run"] is None


# ─────────────────────────────────────────────
# 2. all_opportunities — min_score filtresi
# ─────────────────────────────────────────────

def test_all_opportunities_filtering(tmp_path):
    """min_score filtresi sadece eşik üzerindeki ilanları getirmeli."""
    a = _make_analytics(tmp_path)
    db_path = str(tmp_path / "test_jobhunt.db")

    _insert_opportunity(db_path, canonical_url="https://ex.com/1", latest_score=80.0)
    _insert_opportunity(db_path, canonical_url="https://ex.com/2", latest_score=30.0)
    _insert_opportunity(db_path, canonical_url="https://ex.com/3", latest_score=55.0)

    results = a.all_opportunities(min_score=50)

    scores = [r["latest_score"] for r in results]
    assert all(s >= 50 for s in scores), f"Eşik altı ilanlar döndü: {scores}"
    assert len(results) == 2


def test_all_opportunities_no_filter_returns_all(tmp_path):
    """Filtre olmadan tüm ilanlar gelmeli."""
    a = _make_analytics(tmp_path)
    db_path = str(tmp_path / "test_jobhunt.db")

    for i in range(5):
        _insert_opportunity(
            db_path,
            canonical_url=f"https://ex.com/{i}",
            latest_score=float(10 * i),
        )

    results = a.all_opportunities()
    assert len(results) == 5


# ─────────────────────────────────────────────
# 3. analyze_market_skill_gap — Python içeren ilanlar
# ─────────────────────────────────────────────

def test_analyze_market_skill_gap_with_jobs():
    """Python içeren ilanlardan 'PYTHON' demand çıkmalı."""
    jobs = [
        {"title": "Python Developer", "description": "Build with Python and Django", "tags": []},
        {"title": "Data Scientist", "description": "Machine learning using Python", "tags": ["python"]},
        {"title": "Frontend Dev", "description": "React and TypeScript UI", "tags": []},
    ]
    result = analyze_market_skill_gap(jobs, ["Python"])

    assert isinstance(result, dict)
    assert "top_market_demands" in result
    assert result["total_analyzed"] == 3

    techs = [d["tech"] for d in result["top_market_demands"]]
    assert "PYTHON" in techs, f"PYTHON beklendi ama bulunamadı. Dönen: {techs}"


def test_analyze_market_skill_gap_demand_count_correct():
    """PYTHON demand_count değeri gerçek frekansı yansıtmalı."""
    jobs = [
        {"title": "Python Engineer", "description": "Python backend", "tags": []},
        {"title": "Python Intern", "description": "Python internship", "tags": []},
        {"title": "Java Developer", "description": "Spring Boot Java", "tags": []},
    ]
    result = analyze_market_skill_gap(jobs, [])

    python_demand = next(
        (d for d in result["top_market_demands"] if d["tech"] == "PYTHON"), None
    )
    assert python_demand is not None
    assert python_demand["demand_count"] == 2


def test_analyze_market_skill_gap_summary_text_not_empty_when_has_data():
    """Eşleşme varsa summary_text dolu olmalı."""
    jobs = [{"title": "Python Developer", "description": "Python SQL", "tags": []}]
    result = analyze_market_skill_gap(jobs, [])
    assert result["summary_text"] != ""


# ─────────────────────────────────────────────
# 4. analyze_market_skill_gap — boş liste
# ─────────────────────────────────────────────

def test_analyze_market_skill_gap_empty():
    """Boş liste verilince patlamamalı, boş sonuç dönmeli."""
    result = analyze_market_skill_gap([], ["Python", "SQL"])

    assert isinstance(result, dict)
    assert result["top_market_demands"] == []
    assert result["total_analyzed"] == 0
    assert result["summary_text"] == ""


# ─────────────────────────────────────────────
# 5. export_to_csv — dosya yolu verilmezse string döner
# ─────────────────────────────────────────────

def test_export_to_csv_returns_string(tmp_path):
    """export_to_csv() yol verilmezse CSV içerikli string döndürmeli."""
    a = _make_analytics(tmp_path)
    db_path = str(tmp_path / "test_jobhunt.db")
    _insert_opportunity(db_path, canonical_url="https://ex.com/csv-test", latest_score=70.0)

    csv_content = a.export_to_csv()  # output_path yok

    assert isinstance(csv_content, str)
    # CSV başlık satırı içermeli
    assert "canonical_url" in csv_content or "url" in csv_content


def test_export_to_csv_empty_db_returns_empty_string(tmp_path):
    """Boş DB'de export_to_csv() boş string döndürmeli."""
    a = _make_analytics(tmp_path)
    csv_content = a.export_to_csv()
    assert csv_content == ""


def test_export_to_csv_writes_file_when_path_given(tmp_path):
    """output_path verilince dosyaya yazılmalı."""
    a = _make_analytics(tmp_path)
    db_path = str(tmp_path / "test_jobhunt.db")
    _insert_opportunity(db_path, canonical_url="https://ex.com/file-test", latest_score=65.0)

    out_file = tmp_path / "output.csv"
    result = a.export_to_csv(output_path=str(out_file))

    assert out_file.exists()
    assert out_file.read_text(encoding="utf-8") == result


# ─────────────────────────────────────────────
# 6. run_success_rate — veri yoksa
# ─────────────────────────────────────────────

def test_run_success_rate_no_data(tmp_path):
    """Veri yoksa run_success_rate() 0.0 veya {} dönmeli, hata vermemeli."""
    a = _make_analytics(tmp_path)

    result = a.run_success_rate()

    # Boş DB'de row döner ama total_runs=0; fonksiyon 0.0 veya {} döndürmeli
    assert isinstance(result, dict)
    # Hata fırlatmamış olması yeterli, ama içerik de kontrol edelim
    if result:
        # total_runs sıfır, success_rate_pct hesaplaması için 1 kullanılıyor (zero division koruması)
        assert "success_rate_pct" in result


def test_run_success_rate_does_not_raise(tmp_path):
    """run_success_rate() hiçbir koşulda exception fırlatmamalı."""
    a = _make_analytics(tmp_path)
    try:
        a.run_success_rate()
    except Exception as exc:
        pytest.fail(f"run_success_rate() exception fırlattı: {exc}")
