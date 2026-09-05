from services.notification_and_meta.notifier import build_html_newsletter


def test_newsletter_escapes_external_content_and_rejects_unsafe_urls():
    malicious = '<img src=x onerror="alert(1)">'

    html = build_html_newsletter(
        matched_jobs=[
            {
                "title": malicious,
                "company": "Bad <Company>",
                "url": "javascript:alert(1)",
                "location": "Remote <script>",
                "tags": [],
                "description": malicious,
                "published_at": "2026-09-05",
                "source": "Injected & Source",
                "score": "90",
                "match_reason": malicious,
            }
        ],
        camps=[],
        rd_projects=[],
        podcasts=[],
        hackathons=[],
        news=[],
        github_issues=[],
        skill_gap={
            "summary_text": malicious,
            "top_market_demands": [{"tech": malicious, "demand_count": 3}],
        },
        profile={},
    )

    assert "<img src=x" not in html
    assert "&lt;img src=x" in html
    assert "javascript:alert" not in html
    assert 'href="#"' in html
