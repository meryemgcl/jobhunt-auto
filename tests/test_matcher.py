from services.matcher import score_job_suitability, select_diverse_matches


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


def test_matcher_uses_profile_roles_locations_and_experience_level():
    job = {
        "title": "Junior Backend Developer",
        "description": "Build internal services",
        "location": "Ankara",
        "tags": [],
    }
    baseline_score, _ = score_job_suitability(job, {"core_skills": []})
    profile_score, reason = score_job_suitability(
        job,
        {
            "core_skills": [],
            "job_roles": ["Junior Backend Developer"],
            "preferred_locations": ["Ankara"],
            "experience_level": "Junior/Intern",
        },
    )

    assert profile_score > baseline_score
    assert "Profil Uyumu" in reason


def test_matcher_does_not_penalize_a_junior_job_for_senior_mentorship_in_description():
    job = {
        "title": "Junior Python Developer",
        "description": "Work with senior engineers and learn from the team.",
        "location": "Remote",
        "tags": [],
    }

    score, reason = score_job_suitability(job, PROFILE)

    assert score > 0
    assert "Uyarı" not in reason


def test_matcher_rejects_explicit_experience_requirement_for_junior_profile():
    score, reason = score_job_suitability(
        {
            "title": "Python Developer",
            "description": "Requires 5 years of professional experience.",
            "location": "Remote",
            "tags": ["Python"],
        },
        {"core_skills": ["Python"], "experience_level": "Junior/Intern"},
    )

    assert score == 0
    assert "5+ yıl" in reason


def test_matcher_enforces_countries_only_when_profile_is_explicit():
    job = {
        "title": "Python Engineer",
        "description": "Build backend services.",
        "location": "Remote, France",
        "metadata": {"country": "FR", "eligible_countries": ["FR"]},
        "tags": ["Python"],
    }

    unrestricted_score, _ = score_job_suitability(job, {"core_skills": ["Python"]})
    restricted_score, reason = score_job_suitability(
        job,
        {"core_skills": ["Python"], "eligible_countries": ["Türkiye"]},
    )

    assert unrestricted_score > 0
    assert restricted_score == 0
    assert "çalışma ülkeleriyle eşleşmiyor" in reason


def test_matcher_does_not_mistake_global_remote_for_country_restriction():
    score, _ = score_job_suitability(
        {
            "title": "Python Engineer",
            "description": "Remote anywhere",
            "location": "Remote, Global",
            "tags": ["Python"],
        },
        {"core_skills": ["Python"], "eligible_countries": ["Türkiye"]},
    )

    assert score > 0


def test_match_selection_limits_company_concentration_and_drops_low_scores():
    jobs = [
        {"company": "One", "score": 95, "freshness_score": 100},
        {"company": "One", "score": 90, "freshness_score": 95},
        {"company": "One", "score": 80, "freshness_score": 90},
        {"company": "Two", "score": 70, "freshness_score": 80},
        {"company": "Three", "score": 49, "freshness_score": 100},
    ]

    selected = select_diverse_matches(jobs, minimum_score=50, max_per_company=2)

    assert [job["score"] for job in selected] == [95, 90, 70]
