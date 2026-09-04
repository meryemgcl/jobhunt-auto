from collections import Counter

def analyze_market_skill_gap(jobs, candidate_skills):
    """
    Taranan ilanlardaki teknoloji taleplerini analiz eder ve 
    adayin CV'sinde olmayan ama piyasada en cok aranan ilk 3 beceriyi tespit eder.
    """
    candidate_skills_lower = {s.lower() for s in candidate_skills}
    
    # Takip edilen piyasa teknolojileri havuzu
    market_tracked_techs = [
        "docker", "fastapi", "django", "flask", "git", "linux", "aws", "azure", 
        "postgresql", "mongodb", "redis", "kubernetes", "rest api", "graphql", 
        "pytorch", "tensorflow", "scikit-learn", "nlp", "ci/cd", "celery"
    ]
    
    found_keywords = []
    
    for job in jobs:
        text = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('tags', []))}".lower()
        for tech in market_tracked_techs:
            if tech in text:
                found_keywords.append(tech)
                
    counts = Counter(found_keywords)
    
    # Adayin profilinde henuz listelenmemis olan yuksek talep goren teknolojiler
    skill_gaps = []
    for tech, count in counts.most_common():
        if tech not in candidate_skills_lower:
            skill_gaps.append({"tech": tech.upper(), "demand_count": count})
            if len(skill_gaps) >= 3:
                break
                
    # Eger tum teknolojiler adayin profilinde varsa en cok aranan ilk 3'u ver
    if not skill_gaps:
        for tech, count in counts.most_common(3):
            skill_gaps.append({"tech": tech.upper(), "demand_count": count})
            
    total_analyzed = len(jobs)
    return {
        "total_jobs_analyzed": total_analyzed,
        "top_market_demands": skill_gaps,
        "summary_text": f"Taranan {total_analyzed} pozisyonun analizinde en çok talep edilen ve portfolyona eklemen önerilen teknolojiler: " + 
                        ", ".join([f"{g['tech']} ({g['demand_count']} ilanda)" for g in skill_gaps]) + "."
    }
