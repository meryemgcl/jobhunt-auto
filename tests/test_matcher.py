from services.matcher import score_job_suitability


PROFILE = {"core_skills": ["Python", "SQL", "Machine Learning"]}


def test_matcher_scores_relevant_junior_remote_python_role_above_threshold():
    score, reason = score_job_suitability(
        {
            "title": "Junior Python Backend Developer",
            "description": "Machine learning and SQL internship tasks",
            "location": "Remote Turkey",
            "tags": ["Python"],
        },
        PROFILE,
    )

    assert score >= 50
    assert "Teknoloji" in reason


def test_matcher_rejects_senior_sales_roles():
    score, reason = score_job_suitability(
        {
            "title": "Senior Sales Manager",
            "description": "Marketing and sales operations",
            "location": "Remote",
            "tags": [],
        },
        PROFILE,
    )

    assert score == 0
    assert reason.startswith("Elendi")


def test_matcher_applies_exact_feedback_signal():
    score, reason = score_job_suitability(
        {
            "title": "Junior Python Developer",
            "description": "Python internship",
            "location": "Remote",
            "tags": ["Python"],
            "url": "https://example.com/job",
        },
        PROFILE,
        feedback_index={"https://example.com/job": "alakasız"},
    )

    assert score == 0
    assert "geri bildirimi" in reason


def test_matcher_applies_feedback_keyword_learning():
    score, reason = score_job_suitability(
        {
            "title": "Junior FastAPI Developer",
            "description": "Build backend services",
            "location": "Remote",
            "tags": ["FastAPI"],
        },
        PROFILE,
        feedback_keyword_weights={"fastapi": 6},
    )

    assert score >= 50
    assert "Feedback Öğrenimi" in reason


def test_matcher_rejects_excluded_keyword():
    """EXCLUDED_KEYWORDS (config.py) listesindeki kelime ilani elemeli."""
    score, reason = score_job_suitability(
        {
            "title": "Blockchain Developer",
            "description": "Solidity NFT smart contracts",
            "location": "Remote",
            "company": "CryptoFirm",
            "tags": [],
        },
        PROFILE,
    )
    assert score == 0
    assert "kara listedeki kelime" in reason


def test_matcher_rejects_excluded_company():
    """EXCLUDED_COMPANIES (config.py) listesindeki sirket ilani elemeli."""
    # Gecici olarak config'e test sirketi ekliyoruz, sonra temizliyoruz
    from config import EXCLUDED_COMPANIES as _ec
    original = list(_ec)
    _ec.append("TestSpamAgency")
    try:
        score, reason = score_job_suitability(
            {
                "title": "Junior Python Developer",
                "description": "Python internship remote",
                "location": "Remote",
                "company": "TestSpamAgency",
                "tags": [],
            },
            PROFILE,
        )
        assert score == 0
        assert "kara listedeki sirket" in reason
    finally:
        _ec.clear()
        _ec.extend(original)


def test_matcher_high_match_score_for_perfect_fit():
    """Python + staj + Sivas kombinasyonu yuksek puan vermeli."""
    score, reason = score_job_suitability(
        {
            "title": "Python Stajyer Backend Developer",
            "description": "FastAPI SQL machine learning internship",
            "location": "Sivas",
            "company": "TechCo",
            "tags": ["Python", "SQL"],
        },
        PROFILE,
    )
    assert score >= 85
    assert "Lokasyon" in reason

