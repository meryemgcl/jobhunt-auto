# ==============================================================================
# JobHunt-Auto Sistem Yapılandırması ve Özellik Bayrakları (Feature Flags)
# ==============================================================================

# Modüler Özellik Yönetimi (Açık: True / Kapalı: False)
FEATURE_FLAGS = {
    "ENABLE_SKILL_GAP_ANALYSIS": True,       # 1. Adım: Piyasa Yetenek Açığı Analizi (Kabul)
    "ENABLE_GITHUB_RADAR": True,             # 2. Adım: GitHub Good First Issue Radarı (Kabul)
    "ENABLE_COVER_LETTER_GENERATOR": False,  # 3. Adım: Ön Yazı / Cover Letter Jeneratörü (KAPALI / FALSE)
    "ENABLE_DASHBOARD_TRACKING": True,       # 4. Adım: Başvuru & İstatistik Panosu DASHBOARD.md (Kabul)
    "ENABLE_EXTENDED_TECHNOPARKS": True,     # 5. Adım: Genişletilmiş Anadolu Teknokent Ağı (Kabul)
    "ENABLE_WEEKLY_DIGEST": True,            # 6. Adım: Haftalık Trend & Analiz Özeti (Kabul)
}

# ==============================================================================
# Puanlama Motoru Ağırlıkları (Matcher Weights)
# Kod değiştirmeden kalibrasyon yapabilmek için buradan yönetin.
# Yüksek değer = bu anahtar kelime eşleştiğinde daha fazla puan.
# ==============================================================================

TECH_WEIGHTS: dict[str, int] = {
    "python": 18,
    "machine learning": 14,
    "artificial intelligence": 12,
    "ai": 10,
    "backend": 12,
    "fastapi": 10,
    "django": 8,
    "flask": 8,
    "sql": 9,
    "data": 8,
    "c#": 8,
    "javascript": 7,
    "developer": 5,
    "yazilim": 5,
    "yazılım": 5,
}

ROLE_WEIGHTS: dict[str, int] = {
    "staj": 20,
    "stajyer": 20,
    "intern": 20,
    "junior": 18,
    "entry level": 16,
    "new grad": 16,
    "yeni mezun": 16,
    "ogrenci": 12,
    "öğrenci": 12,
}

LOCATION_WEIGHTS: dict[str, int] = {
    "sivas": 18,
    "erzurum": 18,
    "kayseri": 14,
    "malatya": 12,
    "konya": 12,
    "remote": 14,
    "uzaktan": 14,
    "hibrit": 10,
    "turkiye": 8,
    "türkiye": 8,
    "global": 5,
}

LOCATION_SYNONYMS: dict[str, str] = {
    "turkey": "türkiye",
    "tr": "türkiye",
    "remote - turkey": "remote",
    "istanbul (remote)": "remote",
    "uzaktan": "remote",
}

MIN_MATCH_SCORE = 55
MAX_MATCHES_PER_COMPANY = 2

# Kesinlikle 0 puan verilecek anahtar kelimeler (sabit sistem filtreleri).
# Kişisel tercihler için EXCLUDED_KEYWORDS kullanın.
HARD_NEGATIVE_KEYWORDS: list[str] = [
    "senior",
    "sr",
    "lead",
    "principal",
    "staff engineer",
    "manager",
    "director",
    "muhasebe",
    "accounting",
    "sales",
    "satış",
    "satis",
    "marketing",
    "pazarlama",
    "call center",
    "customer support",
]

# ==============================================================================
# Kullanıcı Tarafından Yönetilen Kara Listeler
# Aşağıdaki listeler matcher.py'daki yerleşik HARD_NEGATIVE_KEYWORDS listesinin
# ötesinde, kullanıcının kişisel tercihlerine göre özelleştirilir.
# Her değer büyük/küçük harf duyarsız karşılaştırılır (casefold).
# ==============================================================================

# Hiçbir ilanı iletilmesini istemediğiniz şirket adları.
# Örnek: sürekli açık ilan yayınlayan ajanslar veya olumsuz deneyimleriniz olan şirketler.
EXCLUDED_COMPANIES: list[str] = [
    # "Örnek Şirket A.Ş.",
    # "Spam Recruiting Ltd.",
]

# İlan başlığı veya açıklamasında geçtiğinde ilanın puanını sıfırlamasını
# istediğiniz anahtar kelimeler.
# Örnek: kariyer hedefinizle örtüşmeyen teknoloji veya roller.
EXCLUDED_KEYWORDS: list[str] = [
    "blockchain",
    "crypto",
    "nft",
    "web3",
    "solidity",
    "game designer",
    "sosyal medya uzmanı",
    "sosyal medya uzmani",
    "content creator",
    "influencer",
]

# ==============================================================================
# Deterministik Arama Promptları ve Negatif Filtreleme (False Exclusions)
# 'False' Filtreleri: Alakasız, senior veya satış odaklı ilanları sistemden eler.
# ==============================================================================
SEARCH_PROMPTS = {
    "BOOTCAMPS": [
        "site:techcareer.net/bootcamp basvuru acik",
        "site:patika.dev bootcamp egitim basvuru",
        "YetGen basvuru egitim programi",
        "Google Oyun ve Uygulama Akademisi basvuru"
    ],
    "RD_PROJECTS": [
        "TUBITAK 2209 universite ogrencileri arastirma projeleri cagri basvuru",
        "Teknokent universite ogrenci arastirmaci stajyer arge projesi"
    ]
}

GREENHOUSE_BOARDS = [
    "gitlab",
    "cloudflare",
    "stripe",
    "datadog",
    "reddit",
    "duolingo",
    "mongodb",
    "elastic",
    "figma",
    "anthropic",
    "mozilla",
    "twilio",
    "dreamgames",
]

LEVER_BOARDS = {
    "trendyol": "Trendyol",
    "iyzico": "iyzico",
    "peakgames": "Peak Games",
    "dreamgames": "Dream Games",
}

ASHBY_BOARDS = {
    "supabase": "Supabase",
    "posthog": "PostHog",
    "linear": "Linear",
    "ramp": "Ramp",
    "docker": "Docker",
    "replit": "Replit",
    "perplexity": "Perplexity",
    "openai": "OpenAI",
}
