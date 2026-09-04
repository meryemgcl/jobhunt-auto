import requests
import datetime
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from config import SEARCH_PROMPTS, FEATURE_FLAGS

CURRENT_DATE = datetime.datetime.now().strftime('%Y-%m-%d')

def fetch_jobs():
    """
    Turkiye Odakli (Sivas, Erzurum, Kayseri, Malatya, Konya, Uzaktan/Remote TR) 
    ve Global API'lerden guncel staj ve junior is ilanlarini ceker.
    """
    jobs = []
    
    # 1. Turkiye & Bolgesel Teknokent Odakli Arama (config.py icindeki promptlar)
    if FEATURE_FLAGS.get("ENABLE_EXTENDED_TECHNOPARKS", True):
        try:
            ddgs = DDGS()
            prompts = SEARCH_PROMPTS.get("REGIONAL_TECHNO_PARKS", [])
            for q in prompts:
                try:
                    results = list(ddgs.text(q, max_results=2))
                    for res in results:
                        title = res.get("title", "")
                        if not title or "..." == title.strip():
                            continue
                        jobs.append({
                            "title": title,
                            "company": "Kariyer.net / Teknokent / Youthall",
                            "url": res.get("href", ""),
                            "location": "Türkiye / Sivas / Erzurum / Kayseri / Uzaktan",
                            "tags": ["Türkiye", "Staj / İş", "Python / AI"],
                            "description": res.get("body", "")[:350],
                            "published_at": CURRENT_DATE,
                            "source": "Anadolu Teknokentleri & TR Uzaktan Ağ"
                        })
                except Exception as e:
                    print(f"[Collector] Arama uyarisi ({q}): {e}")
        except Exception as e:
            print(f"[Collector] DDG Yerel arama hatasi: {e}")

    # 2. Global Remotive API (Uzaktan / Remote Software)
    try:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=20"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for item in r.json().get('jobs', []):
                pub_date = item.get("publication_date", "")[:10] or CURRENT_DATE
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", "Doğrulanmış Şirket"),
                    "url": item.get("url", ""),
                    "location": item.get("candidate_required_location", "Global Remote"),
                    "tags": item.get("tags", []),
                    "description": item.get("description", "")[:350],
                    "published_at": pub_date,
                    "source": "Remotive Global API"
                })
    except Exception as e:
        print(f"[Collector] Remotive API hatasi: {e}")

    # 3. Arbeitnow API (Remote Software)
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for item in r.json().get('data', [])[:20]:
                created_ts = item.get("created_at", 0)
                pub_date = datetime.datetime.fromtimestamp(created_ts).strftime('%Y-%m-%d') if created_ts else CURRENT_DATE
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", "Doğrulanmış Şirket"),
                    "url": item.get("url", ""),
                    "location": item.get("location", "Remote"),
                    "tags": item.get("tags", []),
                    "description": item.get("description", "")[:350],
                    "published_at": pub_date,
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
        camp_prompts = SEARCH_PROMPTS.get("BOOTCAMPS", [])
        for q in camp_prompts:
            try:
                results = list(ddgs.text(q, max_results=1))
                for res in results:
                    camps.append({
                        "title": res.get("title", "Yazılım & AI Bootcamp Programı"),
                        "url": res.get("href", "https://techcareer.net/bootcamp"),
                        "platform": "Techcareer / Patika / Akademi",
                        "status": "Aktif Başvuru"
                    })
            except Exception:
                pass
    except Exception as e:
        print(f"[Collector] Bootcamp arama hatasi: {e}")
        
    # Standart ve garantili kurumsal platformlar
    camps.append({
        "title": "Techcareer.net Ücretsiz Yazılım, Veri & AI Bootcampleri",
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
        rd_prompts = SEARCH_PROMPTS.get("RD_PROJECTS", [])
        for q in rd_prompts:
            results = list(ddgs.text(q, max_results=1))
            for res in results:
                projects.append({
                    "title": res.get("title", "TÜBİTAK 2209 Öğrenci Araştırma Projeleri"),
                    "url": res.get("href", "https://tubitak.gov.tr/tr/burslar/lisans-onlisans/destek-programlari"),
                    "organization": "TÜBİTAK",
                    "type": "Lisans / Ön Lisans AR-GE Proje Hibe Programı"
                })
    except Exception as e:
        print(f"[Collector] AR-GE arama hatasi: {e}")

    # Garantili sabit AR-GE portallari
    projects.append({
        "title": "TÜBİTAK 2209-A Üniversite Öğrencileri Araştırma Projeleri Çağrısı",
        "url": "https://tubitak.gov.tr/tr/burslar/lisans-onlisans/destek-programlari/2209-universite-ogrencileri-arastirma-projeleri-destekleme-programi",
        "organization": "TÜBİTAK BİDEB",
        "type": "Öğrenci AR-GE ve Proje Bütçe Desteği"
    })
    projects.append({
        "title": "Cumhuriyet & Ata Teknokent AR-GE Kuluçka ve Girişimcilik Fırsatları",
        "url": "https://www.cumhuriyetteknokent.com.tr/",
        "organization": "Teknokentler (Sivas / Erzurum)",
        "type": "Bölgesel AR-GE ve Kuluçka Desteği"
    })
    return projects

def fetch_podcasts():
    """Haftanin teknoloji ve yazilim podcastlerini derler."""
    return [
        {
            "title": "Geliştirici Muhabbetleri (Yazılım Mimarisi & Kariyer)",
            "url": "https://open.spotify.com/show/2F5d8WjTf1L2FjV9U0wTq7",
            "host": "Spotify Podcasts",
            "topic": "Yazılım Sektörü, Python ve Geliştirici Deneyimleri"
        },
        {
            "title": "Üretim Bandı (Teknoloji Ürünleri & Yazılım Dünyası)",
            "url": "https://open.spotify.com/show/3D2bBhyFvVpU12e5XQ8o1e",
            "host": "Üretim Bandı Platformu",
            "topic": "Yazılım Mimarisi, Ürün Yönetimi ve AI Trendleri"
        },
        {
            "title": "Kod Gemisi (Açık Kaynak & Yapay Zeka Sohbetleri)",
            "url": "https://open.spotify.com/show/0d8n7Oq9b9g3B5o7Lq3f7A",
            "host": "Kod Gemisi Ekibi",
            "topic": "Python, Açık Kaynak ve Güncel Geliştirici Tartışmaları"
        }
    ]

def fetch_hackathons():
    """Yarışma ve Hackathon platformlarını derler."""
    return [
        {
            "title": "Devpost Global & Online Hackathons 2026",
            "url": "https://devpost.com/hackathons?challenge_type[]=online",
            "platform": "Devpost",
            "status": "Online / Aktif Katılım"
        },
        {
            "title": "TEKNOFEST Teknoloji ve Yazılım Yarışmaları",
            "url": "https://www.teknofest.org/tr/competitions/",
            "platform": "TEKNOFEST",
            "status": "Resmi Yarışma Portalı"
        },
        {
            "title": "Kaggle AI & Makine Öğrenimi Yarışmaları",
            "url": "https://www.kaggle.com/competitions",
            "platform": "Kaggle",
            "status": "Veri Bilimi & AI"
        }
    ]

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
                    "date": CURRENT_DATE
                })
    except Exception as e:
        print(f"[Collector] HackerNews hatasi: {e}")

    return news
