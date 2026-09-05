import re


from services.feedback import feedback_adjustment_for


TECH_WEIGHTS = {
    "python": 18,
    "machine learning": 14,
    "artificial intelligence": 12,
    "ai": 10,
    "backend": 12,
    "fastapi": 10,
    "django": 8,
    "flask": 8,
    "sql": 9,
    "data": 8,
    "c#": 8,
    "javascript": 7,
    "developer": 5,
    "yazilim": 5,
    "yazılım": 5,
}

ROLE_WEIGHTS = {
    "staj": 20,
    "stajyer": 20,
    "intern": 20,
    "junior": 18,
    "entry level": 16,
    "new grad": 16,
    "yeni mezun": 16,
    "ogrenci": 12,
    "öğrenci": 12,
}

LOCATION_WEIGHTS = {
    "sivas": 18,
    "erzurum": 18,
    "kayseri": 14,
    "malatya": 12,
    "konya": 12,
    "remote": 14,
    "uzaktan": 14,
    "hibrit": 10,
    "turkiye": 8,
    "türkiye": 8,
    "global": 5,
}

HARD_NEGATIVE_KEYWORDS = [
    "senior",
    "sr",
    "lead",
    "principal",
    "staff engineer",
    "manager",
    "director",
    "muhasebe",
    "accounting",
    "sales",
    "satış",
    "satis",
    "marketing",
    "pazarlama",
    "call center",
    "customer support",
]


def _normalize(value) -> str:
    return str(value or "").casefold()


def _keyword_in_text(keyword: str, text: str) -> bool:
    pattern = rf"(?<![\w#+]){re.escape(keyword.casefold())}(?![\w#+])"
    return re.search(pattern, text) is not None


def _collect_weighted_matches(weight_map: dict[str, int], text: str) -> tuple[list[str], int]:
    matches = [keyword for keyword in weight_map if _keyword_in_text(keyword, text)]
    score = sum(weight_map[keyword] for keyword in matches)
    return matches, score


def score_job_suitability(
    job,
    profile,
    feedback_index: dict[str, str] | None = None,
    feedback_keyword_weights: dict[str, int] | None = None,
):
    """
    Ilanin aday yetenek profiline, kariyer kademesine ve
    lokasyon kriterlerine uyumunu hesaplar.
    """
    feedback_adjustment, feedback_reason = feedback_adjustment_for(job, feedback_index or {})
    if feedback_adjustment <= -100:
        return 0, feedback_reason or "Elendi: kullanici geri bildirimi"

    title = _normalize(job.get("title"))
    desc = _normalize(job.get("description"))
    location = _normalize(job.get("location"))
    tags = [_normalize(tag) for tag in job.get("tags", [])]
    full_text = f"{title} {desc} {location} {' '.join(tags)}"

    negative_matches = [keyword for keyword in HARD_NEGATIVE_KEYWORDS if _keyword_in_text(keyword, full_text)]
    if negative_matches:
        return 0, f"Elendi: negatif filtre ({', '.join(sorted(set(negative_matches[:3])))})"

    tech_matches, tech_score = _collect_weighted_matches(TECH_WEIGHTS, full_text)
    role_matches, role_score = _collect_weighted_matches(ROLE_WEIGHTS, full_text)
    location_matches, location_score = _collect_weighted_matches(LOCATION_WEIGHTS, full_text)

    candidate_skills = {_normalize(skill) for skill in profile.get("core_skills", [])}
    profile_skill_bonus = 0
    for skill in candidate_skills:
        if skill and _keyword_in_text(skill, full_text):
            profile_skill_bonus += 3

    keyword_adjustment = 0
    feedback_keyword_matches = []
    for keyword, weight in (feedback_keyword_weights or {}).items():
        normalized_keyword = _normalize(keyword)
        if normalized_keyword and _keyword_in_text(normalized_keyword, full_text):
            keyword_adjustment += int(weight)
            feedback_keyword_matches.append(normalized_keyword)
    keyword_adjustment = max(-25, min(15, keyword_adjustment))

    score = min(
        98,
        max(0, tech_score + role_score + location_score + min(profile_skill_bonus, 12) + feedback_adjustment + keyword_adjustment),
    )

    analysis_parts = []
    if feedback_reason:
        analysis_parts.append(feedback_reason)
    if role_matches:
        role_label = " / ".join(match.title() for match in sorted(set(role_matches[:2])))
        analysis_parts.append(f"Kariyer Kademesi: {role_label}")
    if tech_matches:
        tech_label = ", ".join(sorted({match.upper() for match in tech_matches[:4]}))
        analysis_parts.append(f"Teknoloji Eşleşmesi: {tech_label}")
    if location_matches:
        loc_label = " / ".join(sorted({match.capitalize() for match in location_matches[:3]}))
        analysis_parts.append(f"Lokasyon Uyumu: {loc_label}")
    if keyword_adjustment and feedback_keyword_matches:
        keyword_label = ", ".join(sorted(set(feedback_keyword_matches[:3])))
        analysis_parts.append(f"Feedback Öğrenimi: {keyword_label} ({keyword_adjustment:+d})")

    if analysis_parts:
        return score, " • ".join(analysis_parts)

    return score, "Zayif sinyal: belirgin teknoloji, seviye veya lokasyon eslesmesi bulunamadi"
