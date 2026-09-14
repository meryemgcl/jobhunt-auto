import re

from config import (
    EXCLUDED_COMPANIES,
    EXCLUDED_KEYWORDS,
    HARD_NEGATIVE_KEYWORDS,
    LOCATION_WEIGHTS,
    ROLE_WEIGHTS,
    TECH_WEIGHTS,
)
from services.feedback import feedback_adjustment_for


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
    company = _normalize(job.get("company"))
    location = _normalize(job.get("location"))
    tags = [_normalize(tag) for tag in job.get("tags", [])]
    full_text = f"{title} {desc} {location} {' '.join(tags)}"

    # Kullanici tarafindan tanimlanmis sirket kara listesi (config.EXCLUDED_COMPANIES)
    if EXCLUDED_COMPANIES:
        for excluded_company in EXCLUDED_COMPANIES:
            if excluded_company.casefold() and excluded_company.casefold() in company:
                return 0, f"Elendi: kara listedeki sirket ({excluded_company})"

    # Kullanici tarafindan tanimlanmis kelime kara listesi (config.EXCLUDED_KEYWORDS)
    if EXCLUDED_KEYWORDS:
        for excluded_kw in EXCLUDED_KEYWORDS:
            normalized_kw = excluded_kw.casefold()
            if normalized_kw and _keyword_in_text(normalized_kw, full_text):
                return 0, f"Elendi: kara listedeki kelime ({excluded_kw})"

    # Yerlesik sabit negatif filtreler (HARD_NEGATIVE_KEYWORDS)
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
