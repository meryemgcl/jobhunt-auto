from services.notification_and_meta.notifier import build_html_newsletter, send_email_newsletter


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


def test_email_sender_rejects_non_numeric_port(monkeypatch):
    monkeypatch.setenv("SMTP_PORT", "invalid")

    assert send_email_newsletter("<html></html>", 0) is False


def test_newsletter_shows_hacker_news_and_safe_company_application_links():
    html = build_html_newsletter(
        matched_jobs=[
            {
                "title": "Junior Python Engineer",
                "url": "https://news.ycombinator.com/item?id=123",
                "metadata": {"application_url": "https://example.com/careers"},
                "source": "Hacker News Hiring",
                "published_at": "",
                "freshness_score": 50,
                "score": 75,
            }
        ],
        camps=[],
        rd_projects=[],
        podcasts=[],
        hackathons=[],
        news=[],
        github_issues=[],
        skill_gap={},
        profile={},
    )

    assert 'href="https://news.ycombinator.com/item?id=123"' in html
    assert 'href="https://example.com/careers"' in html
    assert "Tarih bilinmiyor" in html
    assert "Hacker News Hiring" in html
