import os
import json

def extract_profile_with_gemini(cv_text: str) -> dict:
    """
    Kullanıcının CV metnini alır ve Gemini kullanarak yapılandırılmış
    bir JSON formatına dönüştürür. (Test modunda mock veri döner)
    """
    return get_mock_profile()

def get_mock_profile():
    return {
        "name": "Meryem Güçlü",
        "title": "Yazılım Geliştirici & Bilişim Sistemleri Öğrencisi",
        "core_skills": [
            "Python", "C#", "JavaScript", "SQL", "Google Gemini API", 
            "Pandas", "Machine Learning", "CNN", "Unity", "Serverless"
        ],
        "experience_level": "Junior/Intern",
        "job_roles": [
            "AI Engineer Intern", "Data Analyst", "Junior Backend Developer", 
            "Frontend Developer", "AR Developer"
        ],
        "github_url": "https://github.com/meryemgcl",
        "linkedin_url": "https://www.linkedin.com/in/meryemgüçlü/"
    }

if __name__ == "__main__":
    profile = get_mock_profile()
    print(json.dumps(profile, indent=2, ensure_ascii=False))
