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
