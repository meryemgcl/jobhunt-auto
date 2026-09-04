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

# Deterministik Arama Promptları ve Negatif Filtreleme (False Exclusions)
# 'False' Filtreleri: Alakasız, senior veya satış odaklı ilanları sistemden eler.
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
