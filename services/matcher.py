def score_job_suitability(job, profile):
    """
    Ilanin aday yetenek profiline, kariyer kademesine ve 
    lokasyon kriterlerine (Sivas, Erzurum, Uzaktan/Remote Turkiye) 
    uyumunu kurumsal metriklerle hesaplar.
    """
    title = job.get("title", "").lower()
    desc = job.get("description", "").lower()
    location = job.get("location", "").lower()
    tags = [t.lower() for t in job.get("tags", [])]
    full_text = f"{title} {desc} {location} {' '.join(tags)}"

    tech_keywords = ["python", "ai", "artificial intelligence", "machine learning", "backend", "c#", "sql", "data", "developer", "yazilim"]
    role_keywords = ["staj", "stajyer", "intern", "junior", "yeni mezun", "ogrenci"]
    loc_keywords = ["sivas", "erzurum", "remote", "uzaktan", "turkiye", "türkiye", "hibrit"]

    matched_tech = [kw.upper() for kw in tech_keywords if kw in full_text]
    matched_role = [kw.capitalize() for kw in role_keywords if kw in full_text]
    matched_loc = [kw.capitalize() for kw in loc_keywords if kw in full_text]

    # Temel taban puani
    score = 50

    if matched_tech:
        score += min(len(matched_tech) * 7, 25)
    if matched_role:
        score += 15
    if matched_loc:
        score += 10

    final_score = min(score, 98)

    # Kurumsal Sistem Analiz Raporu
    analysis_parts = []
    if matched_role:
        analysis_parts.append(f"Kariyer Kademesi: {' / '.join(set(matched_role[:2]))}")
    if matched_tech:
        analysis_parts.append(f"Teknoloji Eşleşmesi: {', '.join(set(matched_tech[:3]))}")
    if matched_loc:
        analysis_parts.append(f"Lokasyon Uyumu: {' / '.join(set(matched_loc[:2]))}")

    if analysis_parts:
        reason = " • ".join(analysis_parts)
    else:
        reason = "Genel Yazılım / Teknoloji Pozisyonu"

    return final_score, reason
