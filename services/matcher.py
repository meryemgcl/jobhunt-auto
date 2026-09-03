def score_job_suitability(job, profile):
    """
    Ilanin Meryem'in yeteneklerine, hedef pozisyonlarina ve
    Turkiye/Sivas/Erzurum/Remote lokasyon tercihlerine uygunlugunu hesaplar.
    """
    title = job.get("title", "").lower()
    desc = job.get("description", "").lower()
    location = job.get("location", "").lower()
    tags = [t.lower() for t in job.get("tags", [])]
    full_text = f"{title} {desc} {location} {' '.join(tags)}"

    # 1. Yetenek ve Pozisyon Kelimeleri
    tech_keywords = ["python", "ai", "artificial intelligence", "machine learning", "backend", "c#", "sql", "data", "developer", "yazilim"]
    intern_keywords = ["staj", "stajyer", "intern", "junior", "yeni mezun", "ogrenci"]
    
    # 2. Lokasyon Tercihleri (Sivas, Erzurum, Uzaktan/Remote, Turkiye)
    location_keywords = ["sivas", "erzurum", "remote", "uzaktan", "turkiye", "türkiye", "hibrit"]

    matched_tech = []
    matched_role = []
    matched_loc = []
    score = 45

    for kw in tech_keywords:
        if kw in full_text:
            matched_tech.append(kw.upper())
            score += 8

    for kw in intern_keywords:
        if kw in full_text:
            matched_role.append(kw.capitalize())
            score += 10

    for kw in location_keywords:
        if kw in full_text:
            matched_loc.append(kw.capitalize())
            score += 8

    # Maksimum 98 ile sinirla
    final_score = min(score, 98)

    # Aciklama olusturma
    reasons = []
    if matched_role:
        reasons.append(f"{'/'.join(set(matched_role[:2]))} seviyesinde")
    if matched_tech:
        reasons.append(f"{', '.join(set(matched_tech[:3]))} teknolojileriyle uyumlu")
    if matched_loc:
        reasons.append(f"📍 {'/'.join(set(matched_loc[:2]))} lokasyonuna uygun")

    if reasons:
        reason = " | ".join(reasons) + "."
    else:
        reason = "Yazılım ve teknoloji pozisyonu."

    return final_score, reason
