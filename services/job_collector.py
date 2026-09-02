import requests
import datetime
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

def fetch_jobs():
    """Yontem A: Remotive ve Arbeitnow ucretsiz API'lerinden taze yazilim ve staj ilanlarini ceker."""
    jobs = []
    
    # 1. Remotive API
    try:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=25"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for item in r.json().get('jobs', []):
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", "Bilinmiyor"),
                    "url": item.get("url", ""),
                    "location": item.get("candidate_required_location", "Remote"),
                    "tags": item.get("tags", []),
                    "description": item.get("description", "")[:400],
                    "published_at": item.get("publication_date", "")[:10],
                    "source": "Remotive"
                })
    except Exception as e:
        print(f"[Collector] Remotive API hatasi: {e}")

    # 2. Arbeitnow API
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for item in r.json().get('data', [])[:25]:
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", "Bilinmiyor"),
                    "url": item.get("url", ""),
                    "location": item.get("location", "Remote"),
                    "tags": item.get("tags", []),
                    "description": item.get("description", "")[:400],
                    "published_at": datetime.datetime.fromtimestamp(item.get("created_at", 0)).strftime('%Y-%m-%d') if item.get("created_at") else "",
                    "source": "Arbeitnow"
                })
    except Exception as e:
        print(f"[Collector] Arbeitnow API hatasi: {e}")

    # 3. DuckDuckGo ile Turkiye yerel staj/is aramalari (Yontem C)
    try:
        queries = ["Python staj ilani Kariyer net", "Junior Python developer LinkedIn Turkiye"]
        ddgs = DDGS()
        for q in queries:
            results = list(ddgs.text(q, max_results=3))
            for res in results:
                jobs.append({
                    "title": res.get("title", ""),
                    "company": "Kariyer / LinkedIn",
                    "url": res.get("href", ""),
                    "location": "Turkiye / Remote",
                    "tags": ["Python", "Staj", "Junior"],
                    "description": res.get("body", "")[:300],
                    "published_at": datetime.datetime.now().strftime('%Y-%m-%d'),
                    "source": "Web Arama"
                })
    except Exception as e:
        print(f"[Collector] DDG arama hatasi: {e}")

    return jobs

def fetch_tech_news():
    """Yontem B: HackerNews ve Dev.to API'lerinden en taze yapay zeka ve Python haberlerini ceker."""
    news = []
    
    # 1. Dev.to API (Python ve AI makaleleri)
    try:
        url = "https://dev.to/api/articles?tag=python&top=1"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for item in r.json()[:3]:
                news.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "source": f"Dev.to ({item.get('user', {}).get('name', 'Yazar')})",
                    "date": item.get("readable_publish_date", "")
                })
    except Exception as e:
        print(f"[Collector] Dev.to haber hatasi: {e}")

    # 2. HackerNews Top Stories API
    try:
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:3]
        for tid in top_ids:
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{tid}.json", timeout=10).json()
            if item and item.get("url"):
                news.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "source": "HackerNews",
                    "date": datetime.datetime.now().strftime('%d %b')
                })
    except Exception as e:
        print(f"[Collector] HackerNews hatasi: {e}")

    return news

def fetch_hackathons():
    """Yontem C: Devpost ve Teknoloji yarismalarini ceker."""
    hackathons = [
        {
            "title": "Global AI & Python Hackathons 2026",
            "url": "https://devpost.com/hackathons?challenge_type[]=online",
            "platform": "Devpost",
            "status": "Aktif / Online"
        },
        {
            "title": "Kaggle Aktif Makine Ogrenimi Yarismalari",
            "url": "https://www.kaggle.com/competitions",
            "platform": "Kaggle",
            "status": "Aktif Odullu Yarismalar"
        },
        {
            "title": "Teknofest & Turkiye Kodlama Yarismalari",
            "url": "https://www.teknofest.org/tr/competitions/",
            "platform": "Teknofest",
            "status": "Yarismalar"
        }
    ]
    return hackathons
