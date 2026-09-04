import json
import os
import datetime

DASHBOARD_PATH = "DASHBOARD.md"
APPLICATIONS_PATH = "applications.json"

def update_career_dashboard(total_analyzed, matched_count, skill_gap_data):
    """
    Kariyer takip panosunu (DASHBOARD.md ve applications.json) 
    en son istatistiklerle otonom olarak gunceller.
    """
    now_str = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    
    # applications.json yukle veya olustur
    data = {
        "last_updated": now_str,
        "total_jobs_analyzed": total_analyzed,
        "matched_jobs_count": matched_count,
        "top_market_demands": skill_gap_data.get("top_market_demands", [])
    }
    
    try:
        with open(APPLICATIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Tracker] applications.json yazma hatasi: {e}")

    # DASHBOARD.md olustur
    demands_list = "\n".join([f"- **{d['tech']}**: {d['demand_count']} ilanda talep edildi" for d in skill_gap_data.get('top_market_demands', [])])
    
    md_content = f"""# 📊 JobHunt-Auto Kariyer & İstihbarat Panosu

> **Son Güncelleme:** `{now_str}`  
> **Sistem Durumu:** ⚡ Aktif & Otonom Çalışıyor

---

## 📈 Genel İstatistikler

| Metrik | Değer |
|---|---|
| **Son Taramada Analiz Edilen Pozisyon** | `{total_analyzed}` |
| **Profil Uyumlu Seçilen Fırsat** | `{matched_count}` |
| **Takip Edilen Teknokent Sayısı** | `6 (Sivas, Erzurum, Kayseri, Malatya, Konya, Ankara)` |
| **Açık Kaynak Radarı** | `Aktif (GitHub Good First Issue API)` |

---

## 🔍 Piyasa Yetenek Açığı (Skill Gap) Analizi

Piyasadaki iş ilanlarında en çok aranan ve CV'ye eklenmesi tavsiye edilen teknolojiler:

{demands_list if demands_list else "- *Veri toplanıyor...*"}

---

## 🏛️ Takip Edilen Bölgesel Ağlar
- **Sivas Cumhuriyet Teknokent:** Yazılım, Bilişim ve AR-GE İlanları
- **Erzurum Ata Teknokent:** Uzaktan & Yerel Yazılım Pozisyonları
- **Kayseri Erciyes Teknokent:** Web & Mobil Geliştirme Stajları
- **Malatya Teknokent & Konya Teknokent:** Girişimcilik & Kuluçka İlanları
- **Türkiye Geneli Uzaktan Ağ:** Youthall, Kariyer.net, Techcareer.net, LinkedIn TR

---
*Bu pano JobHunt-Auto tarafından her çalıştırmada otomatik olarak güncellenir.*
"""

    try:
        with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
            f.write(md_content)
        print("✅ DASHBOARD.md panosu basariyla guncellendi!")
    except Exception as e:
        print(f"[Tracker] DASHBOARD.md yazma hatasi: {e}")
