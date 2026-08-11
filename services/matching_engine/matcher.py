import json

class MatchingEngine:
    def __init__(self):
        pass

    def calculate_match_score(self, profile, job):
        """
        Gelen iş ilanı ile adayın (Meryem'in) profili arasındaki eşleşme oranını hesaplar.
        Gerçek senaryoda bu işlem Gemini veya GPT-4 ile semantic (anlamsal) analiz edilerek yapılır.
        """
        score = 0
        reasons = []

        # Basit bir Keyword Matching algoritması (Gerçeğinde Vektör DB kullanılacak)
        job_desc = job["description"].lower()
        job_title = job["title"].lower()

        for skill in profile["core_skills"]:
            if skill.lower() in job_desc or skill.lower() in job_title:
                score += 20
                reasons.append(f"'{skill}' yeteneği ilanla eşleşti.")

        # Eşleşme skoru 100'ü geçmesin
        final_score = min(score, 100)
        
        return {
            "job_id": job["id"],
            "score": final_score,
            "reasons": reasons
        }

if __name__ == "__main__":
    from services.profile_analyzer.analyzer import get_mock_profile
    from services.job_scraper.scraper import JobScraper
    
    profile = get_mock_profile()
    scraper = JobScraper()
    jobs = scraper.scrape_linkedin_jobs(["AI", "Frontend"])
    
    engine = MatchingEngine()
    
    for job in jobs:
        match_result = engine.calculate_match_score(profile, job)
        print(f"İlan: {job['title']} -> Eşleşme Puanı: %{match_result['score']}")
        for reason in match_result['reasons']:
            print(f"  - {reason}")
