import sys
import io

# Windows terminalleri icin UTF-8 destegi
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from services.profile_analyzer.analyzer import get_mock_profile
from services.memory import load_seen_jobs, add_seen_jobs
from services.job_collector import (
    fetch_jobs, 
    fetch_bootcamps_and_camps, 
    fetch_r_and_d_projects, 
    fetch_podcasts, 
    fetch_hackathons, 
    fetch_tech_news
)
from services.matcher import score_job_suitability
from services.notification_and_meta.notifier import build_html_newsletter, send_email_newsletter

def main():
    print("🚀 JobHunt-Auto Gelismis Deterministik Motor Baslatiliyor...\n")

    # 1. Profil ve Hafizayi Yukle
    profile = get_mock_profile()
    seen_jobs = set(load_seen_jobs())
    print(f"[Memory] Toplam {len(seen_jobs)} daha once gorulmus ilan hafizada.")

    # 2. Tum Kategorilerde Veri Topla
    print("\n🔍 1/6: Türkiye (Sivas/Erzurum/Uzaktan) & Global İş/Staj İlanları Toplanıyor...")
    raw_jobs = fetch_jobs()
    print(f"-> Toplam {len(raw_jobs)} ilan bulundu.")

    print("🔍 2/6: Ücretsiz Bootcampler & Eğitim Kampları Derleniyor...")
    camps = fetch_bootcamps_and_camps()
    print(f"-> {len(camps)} kamp ve program hazırlandı.")

    print("🔍 3/6: AR-GE & TÜBİTAK 2209 Öğrenci Projeleri Kontrol Ediliyor...")
    rd_projects = fetch_r_and_d_projects()
    print(f"-> {len(rd_projects)} AR-GE fırsatı eklendi.")

    print("🔍 4/6: Haftalık Geliştirici & Teknoloji Podcast'leri Derleniyor...")
    podcasts = fetch_podcasts()
    print(f"-> {len(podcasts)} podcast derlendi.")

    print("🔍 5/6: Aktif Yarışma & Hackathon Platformları Listeleniyor...")
    hackathons = fetch_hackathons()
    print(f"-> {len(hackathons)} yarışma platformu hazırlandı.")

    print("🔍 6/6: Güncel Teknoloji & Python Haberleri Çekiliyor...")
    news = fetch_tech_news()
    print(f"-> {len(news)} haber eklendi.")

    # 3. İlanları Filtreleme ve Uyum Puanlaması
    matched_jobs = []
    new_urls = []

    for job in raw_jobs:
        url = job.get("url", "").strip()
        if not url or url in seen_jobs:
            continue

        score, reason = score_job_suitability(job, profile)
        job["score"] = score
        job["match_reason"] = reason

        # %50 ve üzeri uygunluktaki ilanları listeye al
        if score >= 50:
            matched_jobs.append(job)
            new_urls.append(url)

    # Puana göre en iyiden en aza doğru sırala
    matched_jobs.sort(key=lambda x: x["score"], reverse=True)
    print(f"\n🎯 Profiline Uyumlu {len(matched_jobs)} Yeni Fırsat Seçildi!")

    # 4. Zengin HTML E-posta Bültenini Oluştur
    html_report = build_html_newsletter(
        matched_jobs=matched_jobs,
        camps=camps,
        rd_projects=rd_projects,
        podcasts=podcasts,
        hackathons=hackathons,
        news=news,
        profile=profile
    )

    # 5. E-Postayı Gönder
    sent = send_email_newsletter(html_report, len(matched_jobs))

    # 6. Hafızayı Güncelle
    if sent and new_urls:
        add_seen_jobs(new_urls)
        print(f"[Memory] {len(new_urls)} yeni ilan linki seen_jobs.json dosyasina kaydedildi.")

    print("\n🎉 Tüm kategorilerle zenginleştirilmiş bülten başarıyla gönderildi!")

if __name__ == "__main__":
    main()
