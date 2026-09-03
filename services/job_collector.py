import requests
import datetime
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

def fetch_jobs():
    """
    Turkiye Odakli (Sivas, Erzurum, Uzaktan/Remote Turkiye) 
    ve Global API'lerden staj ve junior is ilanlarini ceker.
    """
    jobs = []
    
    # 1. Turkiye & Bolgesel Odakli Arama (Sivas, Erzurum, Remote TR, Youthall, Kariyer, Techcareer)
    try:
        ddgs = DDGS()
        regional_queries = [
            "site:youthall.com Python OR AI OR Backend staj remote",
            "site:kariyer.net Python stajyer remote OR Sivas OR Erzurum",
            "site:techcareer.net is ilanlari Python OR junior",
            "Sivas Cumhuriyet Teknokent yazilim staj OR is ilani",
            "Erzurum Ata Teknokent yazilim staj OR remote",
            "Turkiye remote junior python backend developer linkedin"
        ]
        for q in regional_queries:
            try:
                results = list(ddgs.text(q, max_results=2))
                for res in results:
                    title = res.get("title", "")
                    if not title or "..." == title.strip():
                        continue
                    jobs.append({
                        "title": title,
                        "company": "Kariyer / Teknokent / Youthall",
                        "url": res.get("href", ""),
                        "location": "Türkiye / Sivas / Erzurum / Uzaktan",
                        "tags": ["Türkiye", "Staj/İş", "Python/AI"],
                        "description": res.get("body", "")[:350],
                        "published_at": datetime.datetime.now().strftime('%Y-%m-%d'),
                        "source": "TR Yerel & Uzaktan Arama"
                    })
            except Exception as e:
                print(f"[Collector] Sorgu hatasi ({q}): {e}")
    except Exception as e:
        print(f"[Collector] DDG Yerel arama hatasi: {e}")

    # 2. Global Remotive API (Uzaktan / Remote Software)
    try:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=15"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for item in r.json().get('jobs', []):
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", "Bilinmiyor"),
                    "url": item.get("url", ""),
                    "location": item.get("candidate_required_location", "Global Remote"),
                    "tags": item.get("tags", []),
                    "description": item.get("description", "")[:350],
                    "published_at": item.get("publication_date", "")[:10],
                    "source": "Remotive API"
                })
    except Exception as e:
        print(f"[Collector] Remotive API hatasi: {e}")

    # 3. Arbeitnow API (Remote Software)
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for item in r.json().get('data', [])[:15]:
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", "Bilinmiyor"),
                    "url": item.get("url", ""),
                    "location": item.get("location", "Remote"),
                    "tags": item.get("tags", []),
                    "description": item.get("description", "")[:350],
                    "published_at": datetime.datetime.fromtimestamp(item.get("created_at", 0)).strftime('%Y-%m-%d') if item.get("created_at") else "",
                    "source": "Arbeitnow API"
                })
    except Exception as e:
        print(f"[Collector] Arbeitnow API hatasi: {e}")

    return jobs

def fetch_bootcamps_and_camps():
    """Ucretsiz egitim kamplari, bootcamp ve akademi programlarini ceker."""
    camps = []
    try:
        ddgs = DDGS()
        camp_queries = [
            "site:techcareer.net/bootcamp basvuru",
            "site:patika.dev bootcamp egitim basvuru acik",
            "YetGen basvuru egitim programi",
            "Google Oyun ve Uygulama Akademisi basvuru"
        ]
        for q in camp_queries:
            try:
                results = list(ddgs.text(q, max_results=1))
                for res in results:
                    camps.append({
                        "title": res.get("title", "Yazılım / AI Bootcamp"),
                        "url": res.get("href", "https://techcareer.net/bootcamp"),
                        "platform": "Techcareer / Patika / Akademi",
                        "status": "Ücretsiz / Başvuruya Açık"
                    })
            except Exception:
                pass
    except Exception as e:
        print(f"[Collector] Bootcamp arama hatasi: {e}")
        
    # Standart ve garantili sabit platformlar (Fallback)
    camps.append({
        "title": "Techcareer.net Ücretsiz Yazılım & AI Bootcampleri",
        "url": "https://www.techcareer.net/bootcamp",
        "platform": "Techcareer.net",
        "status": "Sürekli Güncel"
    })
    camps.append({
        "title": "Patika.dev & Kodluyoruz Ücretsiz Kariyer Yolları",
        "url": "https://www.patika.dev/bootcamp",
        "platform": "Patika.dev",
        "status": "Online / Aktif"
    })
    return camps

def fetch_r_and_d_projects():
    """TÜBİTAK 2209 ve Teknokent AR-GE Proje Destek ve Fırsatlarını ceker."""
    projects = []
    try:
        ddgs = DDGS()
        results = list(ddgs.text("TUBITAK 2209 universite ogrencileri arastirma projeleri destekleme", max_results=2))
        for res in results:
            projects.append({
                "title": res.get("title", "TÜBİTAK 2209 Öğrenci Araştırma Projeleri"),
                "url": res.get("href", "https://tubitak.gov.tr/tr/burslar/lisans-onlisans/destek-programlari"),
                "organization": "TÜBİTAK",
                "type": "Lisans / Ön Lisans AR-GE Proje Desteği"
            })
    except Exception as e:
        print(f"[Collector] AR-GE arama hatasi: {e}")

    # Garantili sabit AR-GE portallari
    projects.append({
        "title": "TÜBİTAK 2209-A Üniversite Öğrencileri Araştırma Projeleri Çağrısı",
        "url": "https://tubitak.gov.tr/tr/burslar/lisans-onlisans/destek-programlari/2209-universite-ogrencileri-arastirma-projeleri-destekleme-programi",
        "organization": "TÜBİTAK BİDEB",
        "type": "Öğrenci Hibe ve AR-GE Desteği"
    })
    projects.append({
        "title": "Cumhuriyet & Ata Teknokent AR-GE ve Girişimcilik Programları",
        "url": "https://www.cumhuriyetteknokent.com.tr/",
        "organization": "Teknokentler (Sivas/Erzurum)",
        "type": "Yerel AR-GE ve Kuluçka Desteği"
    })
    return projects

def fetch_podcasts():
    """Haftanin gelistirici ve teknoloji podcastlerini derler."""
    podcasts = [
        {
            "title": "Geliştirici Muhabbetleri (Yazılım & Kariyer)",
            "url": "https://open.spotify.com/show/2F5d8WjTf1L2FjV9U0wTq7",
            "host": "Spotify / Podcast",
            "topic": "Yazılım Kariyeri, Python ve Teknoloji Deneyimleri"
        },
        {
            "title": "Üretim Bandı (Teknoloji Ürünleri & Yazılım Dünyası)",
            "url": "https://open.spotify.com/show/3D2bBhyFvVpU12e5XQ8o1e",
            "host": "Üretim Bandı Ekibi",
            "topic": "Yazılım Mimarisi, Ürün Geliştirme ve AI Trendleri"
        },
        {
            "title": "Kod Gemisi (Yazılım, Açık Kaynak & Yapay Zeka)",
            "url": "https://open.spotify.com/show/0d8n7Oq9b9g3B5o7Lq3f7A",
            "host": "Kod Gemisi",
            "topic": "Python, Açık Kaynak ve Güncel Geliştirici Sohbetleri"
        }
    ]
    return podcasts

def fetch_hackathons():
    """Yarışma ve Hackathon platformlarını derler."""
    hackathons = [
        {
            "title": "Devpost Online & Global Hackathons 2026",
            "url": "https://devpost.com/hackathons?challenge_type[]=online",
            "platform": "Devpost",
            "status": "Online / Aktif Katılım"
        },
        {
            "title": "TEKNOFEST Teknoloji ve Yazılım Yarışmaları",
            "url": "https://www.teknofest.org/tr/competitions/",
            "platform": "TEKNOFEST",
            "status": "Ödüllü Yarışmalar"
        },
        {
            "title": "Kaggle AI & Veri Bilimi Yarışmaları",
            "url": "https://www.kaggle.com/competitions",
            "platform": "Kaggle",
            "status": "Veri Bilimi & ML"
        }
    ]
    return hackathons

def fetch_tech_news():
    """HackerNews ve Dev.to üzerinden en taze haberleri çeker."""
    news = []
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
