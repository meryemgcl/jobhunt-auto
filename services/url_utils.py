from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "ref",
    "ref_src",
    "source",
}


def clean_url(url: str | None) -> str:
    """Remove common markdown/email artifacts around discovered URLs."""
    cleaned = str(url or "").strip().strip("<>\"'")
    return cleaned.rstrip(" \t\r\n)]}*,.")


def canonicalize_url(url: str | None) -> str:
    """Normalize URLs so duplicate sources collapse to a stable key."""
    cleaned = clean_url(url)
    if not cleaned:
        return ""

    parsed = urlsplit(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return cleaned

    query_params = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in TRACKING_PARAMS:
            continue
        query_params.append((key, value))

    query = urlencode(sorted(query_params), doseq=True)
    path = parsed.path.rstrip("/") or "/"
    netloc = parsed.netloc.lower()

    if parsed.scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif parsed.scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    return urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))
