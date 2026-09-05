from services.url_utils import canonicalize_url, clean_url


def test_clean_url_removes_markdown_artifacts():
    assert clean_url("https://example.com/job?x=1)**") == "https://example.com/job?x=1"


def test_canonicalize_url_removes_tracking_params_and_fragment():
    url = "HTTPS://Example.COM/job/?utm_source=newsletter&b=2&a=1#section"

    assert canonicalize_url(url) == "https://example.com/job?a=1&b=2"
