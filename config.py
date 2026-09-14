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
    "REGIONAL_TECHNO_PARKS": [
        "site:youthall.com Python OR AI OR Backend staj remote -senior -lead",
        "site:kariyer.net Python stajyer remote OR Sivas OR Erzurum OR Kayseri -senior",
        "site:techcareer.net is ilanlari Python OR junior -senior",
        "Sivas Cumhuriyet Teknokent yazilim staj OR is ilani -muhasebe",
        "Erzurum Ata Teknokent yazilim staj OR remote -muhasebe",
        "Kayseri Erciyes Teknokent yazilim staj OR remote -muhasebe",
        "Malatya Teknokent yazilim staj OR junior -muhasebe",
        "Konya Teknokent yazilim staj OR remote -muhasebe",
        "Turkiye remote junior python backend developer linkedin -senior"
    ],
    "BOOTCAMPS": [
        "site:techcareer.net/bootcamp basvuru 2026 -ucretli",
        "site:patika.dev bootcamp egitim basvuru acik -ucretli",
        "YetGen basvuru egitim programi 2026",
        "Google Oyun ve Uygulama Akademisi basvuru"
    ],
    "RD_PROJECTS": [
        "TUBITAK 2209 universite ogrencileri arastirma projeleri destekleme 2026",
        "Teknokent universite ogrenci arastirmaci stajyer arge projesi"
    ]
}
