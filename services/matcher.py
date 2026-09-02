import re

def score_job_suitability(job, profile):
    """
    Ilanin Meryem'in yetenek ve hedeflerine uygunlugunu % cinsinden hesaplar
    ve eslesen anahtar kelimeleri tespit eder.
    """
    title = job.get("title", "").lower()
    desc = job.get("description", "").lower()
    tags = [t.lower() for t in job.get("tags", [])]
    full_text = f"{title} {desc} {' '.join(tags)}"

    # Hedef yetenekler ve agirliklari
    high_value_keywords = ["python", "ai", "artificial intelligence", "machine learning", "backend", "c#", "junior", "intern", "staj"]
    medium_value_keywords = ["sql", "data", "developer", "software", "api", "remote", "javascript"]

    matched_keywords = []
    score = 40 # Temel yazilim skoru

    for kw in high_value_keywords:
        if kw in full_text:
            matched_keywords.append(kw.upper())
            score += 10

    for kw in medium_value_keywords:
        if kw in full_text:
            matched_keywords.append(kw.capitalize())
            score += 5

    # Skor sinirlamasi
    final_score = min(score, 98)
    
    # Uygunluk aciklamasi olustur
    if matched_keywords:
        reason = f"Profilindeki {', '.join(set(matched_keywords[:4]))} yetenekleriyle dogrudan eslesiyor."
    else:
        reason = "Genel yazilim ve teknoloji pozisyonu."

    return final_score, reason
