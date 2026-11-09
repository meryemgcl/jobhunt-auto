import re
from collections import Counter
from collections.abc import Iterable

from config import (
    EXCLUDED_COMPANIES,
    EXCLUDED_KEYWORDS,
    HARD_NEGATIVE_KEYWORDS,
    LOCATION_WEIGHTS,
    LOCATION_SYNONYMS,
    ROLE_WEIGHTS,
    TECH_WEIGHTS,
)
from services.feedback import feedback_adjustment_for


def _normalize(value) -> str:
    return str(value or "").casefold()


def _normalize_location(location: str) -> str:
    loc = _normalize(location)
    return LOCATION_SYNONYMS.get(loc, loc)


def _keyword_in_text(keyword: str, text: str) -> bool:
    pattern = rf"(?<![\w#+]){re.escape(keyword.casefold())}(?![\w#+])"
    return re.search(pattern, text) is not None


def _collect_weighted_matches(weight_map: dict[str, int], text: str) -> tuple[list[str], int]:
    matches = [keyword for keyword in weight_map if _keyword_in_text(keyword, text)]
    score = sum(weight_map[keyword] for keyword in matches)
    return matches, score


def _profile_values(profile: dict, key: str) -> list[str]:
    value = profile.get(key, [])
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _required_experience_years(text: str) -> int | None:
    patterns = (
        r"\b(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+|relevant\s+)?experience\b",
        r"\b(?:minimum|min\.?)\s*(\d{1,2})\s*(?:years?|yrs?)\b",
        r"\bexperience\s*:\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b",
    )
    requirements = [
        int(match.group(1))
        for pattern in patterns
        if (match := re.search(pattern, text))
    ]
    return min(requirements) if requirements else None


def _country_tokens(values: Iterable[str]) -> set[str]:
    aliases = {
        "tr": "turkey",
        "fr": "france",
        "de": "germany",
        "gb": "united kingdom",
        "us": "united states",
        "ca": "canada",
        "au": "australia",
        "ae": "united arab emirates",
        "turkey": "turkey",
        "türkiye": "turkey",
        "turkiye": "turkey",
        "usa": "united states",
        "united states": "united states",
        "uk": "united kingdom",
        "united kingdom": "united kingdom",
        "uae": "united arab emirates",
        "emirates": "united arab emirates",
    }
    known = {
        "argentina", "australia", "austria", "belgium", "brazil", "bulgaria",
        "canada", "chile", "china", "colombia", "croatia", "cyprus", "czechia",
        "denmark", "egypt", "estonia", "finland", "france", "germany", "greece",
        "hong kong", "hungary", "india", "indonesia", "ireland", "israel", "italy",
        "japan", "kenya", "latvia", "lithuania", "luxembourg", "malaysia", "mexico",
        "netherlands", "new zealand", "nigeria", "norway", "pakistan", "philippines",
        "poland", "portugal", "romania", "saudi arabia", "singapore", "slovakia",
        "slovenia", "south africa", "south korea", "spain", "sweden", "switzerland",
        "taiwan", "thailand", "turkey", "united arab emirates", "united kingdom",
        "united states", "vietnam",
    }
    found = set()
    for value in values:
        text = _normalize(value)
        for country in known:
            if _keyword_in_text(country, text):
                found.add(aliases.get(country, country))
        for alias, canonical in aliases.items():
            if _keyword_in_text(alias, text):
                found.add(canonical)
    return found


def select_diverse_matches(
    jobs: list[dict],
    *,
    minimum_score: int = 50,
    max_per_company: int = 2,
) -> list[dict]:
    if max_per_company < 1:
        raise ValueError("max_per_company must be positive.")

    selected = []
    company_counts: Counter[str] = Counter()
    for job in sorted(
        jobs,
        key=lambda item: (int(item.get("score") or 0), int(item.get("freshness_score") or 0)),
        reverse=True,
    ):
        if int(job.get("score") or 0) < minimum_score:
            continue
        company = _normalize(job.get("company")).strip()
        if company and company_counts[company] >= max_per_company:
            continue
        if company:
            company_counts[company] += 1
        selected.append(job)
    return selected


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
    location = _normalize_location(job.get("location"))
    tags = [_normalize(tag) for tag in job.get("tags", [])]
    full_text = f"{title} {desc} {location} {' '.join(tags)}"
    metadata = job.get("metadata") if isinstance(job.get("metadata"), dict) else {}

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

    # Yerlesik negatif filtreler (HARD_NEGATIVE_KEYWORDS) - Context Aware
    negative_matches_title = [keyword for keyword in HARD_NEGATIVE_KEYWORDS if _keyword_in_text(keyword, title)]
    if negative_matches_title:
        return 0, f"Elendi: başlık/şirkette negatif filtre ({', '.join(sorted(set(negative_matches_title[:3])))})"

    profile_level = " ".join(_profile_values(profile, "experience_level")).casefold()
    is_early_career_profile = any(
        marker in profile_level
        for marker in ("intern", "staj", "junior", "entry", "new grad", "yeni mezun")
    )
    required_years = _required_experience_years(desc)
    if is_early_career_profile and required_years is not None and required_years >= 3:
        return 0, f"Elendi: açık deneyim şartı ({required_years}+ yıl)"

    eligible_countries = _country_tokens(_profile_values(profile, "eligible_countries"))
    job_country_values = [
        str(value)
        for value in (
            metadata.get("eligible_countries", [])
            if isinstance(metadata.get("eligible_countries"), list)
            else [metadata.get("eligible_countries", "")]
        )
        if value
    ]
    job_country_values.extend(
        str(metadata.get(key) or "")
        for key in ("country", "candidate_required_location")
    )
    job_country_values.append(str(job.get("location") or ""))
    restricted_countries = _country_tokens(job_country_values)
    if eligible_countries and restricted_countries and eligible_countries.isdisjoint(restricted_countries):
        return 0, (
            "Elendi: ilan ülkesi adayın izin verilen çalışma ülkeleriyle eşleşmiyor "
            f"({', '.join(sorted(restricted_countries))})"
        )
        
    tech_matches, tech_score = _collect_weighted_matches(TECH_WEIGHTS, full_text)
    role_matches, role_score = _collect_weighted_matches(ROLE_WEIGHTS, full_text)
    location_matches, location_score = _collect_weighted_matches(LOCATION_WEIGHTS, full_text)

    candidate_skills = {_normalize(skill) for skill in _profile_values(profile, "core_skills")}
    profile_skill_bonus = 0
    for skill in candidate_skills:
        if skill and _keyword_in_text(skill, full_text):
            profile_skill_bonus += 3

    profile_role_matches = [
        role for role in _profile_values(profile, "job_roles")
        if _keyword_in_text(role, full_text)
    ]
    profile_location_matches = [
        preferred for preferred in _profile_values(profile, "preferred_locations")
        if _keyword_in_text(_normalize_location(preferred), full_text)
    ]
    experience_levels = [
        level.strip()
        for value in _profile_values(profile, "experience_level")
        for level in re.split(r"[/,|]+", value)
        if level.strip()
    ]
    profile_experience_matches = [
        level for level in experience_levels
        if _keyword_in_text(level, full_text)
    ]
    profile_role_bonus = min(12, 5 * len(profile_role_matches))
    profile_location_bonus = min(12, 6 * len(profile_location_matches))
    profile_experience_bonus = min(6, 3 * len(profile_experience_matches))

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
        max(
            0,
            tech_score + role_score + location_score + min(profile_skill_bonus, 12)
            + profile_role_bonus + profile_location_bonus + profile_experience_bonus
            + feedback_adjustment + keyword_adjustment,
        ),
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
    profile_matches = profile_role_matches + profile_location_matches + profile_experience_matches
    if profile_matches:
        profile_label = ", ".join(sorted(set(profile_matches[:4])))
        analysis_parts.append(f"Profil Uyumu: {profile_label}")
    if keyword_adjustment and feedback_keyword_matches:
        keyword_label = ", ".join(sorted(set(feedback_keyword_matches[:3])))
        analysis_parts.append(f"Feedback Öğrenimi: {keyword_label} ({keyword_adjustment:+d})")
    if required_years is not None:
        analysis_parts.append(f"Deneyim şartı: {required_years}+ yıl")
    if not eligible_countries:
        analysis_parts.append("Çalışma ülkesi uygunluğu aday profilinde belirtilmemiş")
    elif restricted_countries:
        analysis_parts.append("İlan ülkesi profil kısıtıyla uyumlu; çalışma izni ayrıca doğrulanmalı")
    else:
        analysis_parts.append("İlan ülkesi ve çalışma izni kaynaktan doğrulanmadı")

    if analysis_parts:
        return score, " • ".join(analysis_parts)

    return score, "Zayif sinyal: belirgin teknoloji, seviye veya lokasyon eslesmesi bulunamadi"
