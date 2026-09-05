import datetime
import logging

from config import SEARCH_PROMPTS, FEATURE_FLAGS
from services.adapters import (
    ArbeitnowAdapter,
    DevToAdapter,
    DuckDuckGoAdapter,
    HackerNewsAdapter,
    RemotiveAdapter,
    StaticOpportunityAdapter,
)

CURRENT_DATE = datetime.datetime.now().strftime('%Y-%m-%d')
logger = logging.getLogger(__name__)


def _collect_from_adapters(adapters):
    opportunities = []
    for adapter in adapters:
        items = adapter.fetch()
        logger.info("Adapter tamamlandi. adapter=%s count=%s", adapter.__class__.__name__, len(items))
        opportunities.extend(items)
    return opportunities


def _regional_job_mapper(result, _prompt):
    return {
        "title": result.get("title", ""),
        "company": "Kariyer.net / Teknokent / Youthall",
        "url": result.get("href", ""),
        "location": "Türkiye / Sivas / Erzurum / Kayseri / Uzaktan",
        "tags": ["Türkiye", "Staj / İş", "Python / AI"],
        "description": result.get("body", "")[:350],
        "published_at": CURRENT_DATE,
        "source": "Anadolu Teknokentleri & TR Uzaktan Ağ",
        "source_reliability": 68,
    }


def _bootcamp_mapper(result, _prompt):
    return {
        "title": result.get("title", "Yazılım & AI Bootcamp Programı"),
        "url": result.get("href", "https://techcareer.net/bootcamp"),
        "platform": "Techcareer / Patika / Akademi",
        "status": "Aktif Başvuru",
        "source": "Bootcamp Search",
        "source_reliability": 65,
    }


def _rd_project_mapper(result, _prompt):
    return {
        "title": result.get("title", "TÜBİTAK 2209 Öğrenci Araştırma Projeleri"),
        "url": result.get("href", "https://tubitak.gov.tr/tr/burslar/lisans-onlisans/destek-programlari"),
        "organization": "TÜBİTAK",
        "type": "Lisans / Ön Lisans AR-GE Proje Hibe Programı",
        "source": "AR-GE Search",
        "source_reliability": 65,
    }

def fetch_jobs():
    """
    Turkiye Odakli (Sivas, Erzurum, Kayseri, Malatya, Konya, Uzaktan/Remote TR) 
    ve Global API'lerden guncel staj ve junior is ilanlarini ceker.
    """
    adapters = []
    if FEATURE_FLAGS.get("ENABLE_EXTENDED_TECHNOPARKS", True):
        adapters.append(
            DuckDuckGoAdapter(
                prompts=SEARCH_PROMPTS.get("REGIONAL_TECHNO_PARKS", []),
                category="job",
                max_results=2,
                result_mapper=_regional_job_mapper,
            )
        )

    adapters.extend([RemotiveAdapter(), ArbeitnowAdapter()])
    return _collect_from_adapters(adapters)

def fetch_bootcamps_and_camps():
    """Ucretsiz egitim kamplari, bootcamp ve akademi programlarini ceker."""
    adapters = [
        DuckDuckGoAdapter(
            prompts=SEARCH_PROMPTS.get("BOOTCAMPS", []),
            category="bootcamp",
            max_results=1,
            result_mapper=_bootcamp_mapper,
        ),
        StaticOpportunityAdapter(
            [
                {
                    "title": "Techcareer.net Ücretsiz Yazılım, Veri & AI Bootcampleri",
                    "url": "https://www.techcareer.net/bootcamp",
                    "platform": "Techcareer.net",
                    "status": "Sürekli Güncel",
                },
                {
                    "title": "Patika.dev & Kodluyoruz Ücretsiz Kariyer Yolları",
                    "url": "https://www.patika.dev/bootcamp",
                    "platform": "Patika.dev",
                    "status": "Online / Aktif",
                },
            ],
            category="bootcamp",
        ),
    ]
    return _collect_from_adapters(adapters)

def fetch_r_and_d_projects():
    """TÜBİTAK 2209 ve Teknokent AR-GE Proje Destek ve Fırsatlarını ceker."""
    adapters = [
        DuckDuckGoAdapter(
            prompts=SEARCH_PROMPTS.get("RD_PROJECTS", []),
            category="rd_project",
            max_results=1,
            result_mapper=_rd_project_mapper,
        ),
        StaticOpportunityAdapter(
            [
                {
                    "title": "TÜBİTAK 2209-A Üniversite Öğrencileri Araştırma Projeleri Çağrısı",
                    "url": "https://tubitak.gov.tr/tr/burslar/lisans-onlisans/destek-programlari/2209-universite-ogrencileri-arastirma-projeleri-destekleme-programi",
                    "organization": "TÜBİTAK BİDEB",
                    "type": "Öğrenci AR-GE ve Proje Bütçe Desteği",
                },
                {
                    "title": "Cumhuriyet & Ata Teknokent AR-GE Kuluçka ve Girişimcilik Fırsatları",
                    "url": "https://www.cumhuriyetteknokent.com.tr/",
                    "organization": "Teknokentler (Sivas / Erzurum)",
                    "type": "Bölgesel AR-GE ve Kuluçka Desteği",
                },
            ],
            category="rd_project",
        ),
    ]
    return _collect_from_adapters(adapters)

def fetch_podcasts():
    """Haftanin teknoloji ve yazilim podcastlerini derler."""
    adapter = StaticOpportunityAdapter(
        [
            {
                "title": "Geliştirici Muhabbetleri (Yazılım Mimarisi & Kariyer)",
                "url": "https://open.spotify.com/show/2F5d8WjTf1L2FjV9U0wTq7",
                "platform": "Spotify Podcasts",
                "metadata": {"topic": "Yazılım Sektörü, Python ve Geliştirici Deneyimleri"},
            },
            {
                "title": "Üretim Bandı (Teknoloji Ürünleri & Yazılım Dünyası)",
                "url": "https://open.spotify.com/show/3D2bBhyFvVpU12e5XQ8o1e",
                "platform": "Üretim Bandı Platformu",
                "metadata": {"topic": "Yazılım Mimarisi, Ürün Yönetimi ve AI Trendleri"},
            },
            {
                "title": "Kod Gemisi (Açık Kaynak & Yapay Zeka Sohbetleri)",
                "url": "https://open.spotify.com/show/0d8n7Oq9b9g3B5o7Lq3f7A",
                "platform": "Kod Gemisi Ekibi",
                "metadata": {"topic": "Python, Açık Kaynak ve Güncel Geliştirici Tartışmaları"},
            },
        ],
        category="podcast",
    )
    podcasts = adapter.fetch()
    for podcast in podcasts:
        podcast["host"] = podcast.get("platform", "")
        podcast["topic"] = podcast.get("metadata", {}).get("topic", "")
    return podcasts

def fetch_hackathons():
    """Yarışma ve Hackathon platformlarını derler."""
    adapter = StaticOpportunityAdapter(
        [
            {
                "title": "Devpost Global & Online Hackathons 2026",
                "url": "https://devpost.com/hackathons?challenge_type[]=online",
                "platform": "Devpost",
                "status": "Online / Aktif Katılım",
            },
            {
                "title": "TEKNOFEST Teknoloji ve Yazılım Yarışmaları",
                "url": "https://www.teknofest.org/tr/competitions/",
                "platform": "TEKNOFEST",
                "status": "Resmi Yarışma Portalı",
            },
            {
                "title": "Kaggle AI & Makine Öğrenimi Yarışmaları",
                "url": "https://www.kaggle.com/competitions",
                "platform": "Kaggle",
                "status": "Veri Bilimi & AI",
            },
        ],
        category="hackathon",
    )
    return adapter.fetch()

def fetch_tech_news():
    """HackerNews ve Dev.to üzerinden en taze haberleri çeker."""
    news = _collect_from_adapters([DevToAdapter(), HackerNewsAdapter()])
    for item in news:
        item["date"] = item.get("metadata", {}).get("readable_publish_date") or item.get("published_at", "")
    return news
