import sys
import io
import datetime

# Windows terminalleri icin UTF-8 destegi
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from services.profile_analyzer.analyzer import get_mock_profile
from services.memory import load_seen_jobs, add_seen_jobs
from services.job_collector import fetch_jobs, fetch_tech_news, fetch_hackathons
from services.matcher import score_job_suitability
from services.notification_and_meta.notifier import build_html_newsletter, send_email_newsletter

def main():
    print("🚀 Deterministik JobHunt-Auto Baslatiliyor... (Sifir AI Bagimliligi, %100 Kararli)\n")

    # 1. Profil ve Hafizayi Yukle
    profile = get_mock_profile()
    seen_jobs = set(load_seen_jobs())
    print(f"[Memory] Toplam {len(seen_jobs)} daha once gorulmus ilan hafizada.")

    # 2. Canli Verileri Topla (Yontem A, B, C)
    print("\n🔍 1/3: Guncel is/staj ilanlari toplaniyor (Remotive, Arbeitnow, Web)...")
    raw_jobs = fetch_jobs()
    print(f"-> Toplam {len(raw_jobs)} ham ilan bulundu.")

    print("🔍 2/3: Trend teknoloji haberleri toplaniyor (HackerNews, Dev.to)...")
    news = fetch_tech_news()
    print(f"-> {len(news)} haber derlendi.")

    print("🔍 3/3: Aktif hackathon ve yarismalar toplaniyor...")
    hackathons = fetch_hackathons()
    print(f"-> {len(hackathons)} yarisma platformu hazirlandi.")

    # 3. Filtreleme ve Uyum Puanlamasi
    matched_jobs = []
    new_urls = []

    for job in raw_jobs:
        url = job.get("url", "").strip()
        if not url or url in seen_jobs:
            continue

        score, reason = score_job_suitability(job, profile)
        job["score"] = score
        job["match_reason"] = reason

        # %50 ve uzeri uygunluktaki ilanlari al
        if score >= 50:
            matched_jobs.append(job)
            new_urls.append(url)

    # Puana gore en iyiden en aza sirala
    matched_jobs.sort(key=lambda x: x["score"], reverse=True)
    print(f"\n🎯 Profiline Uyumlu {len(matched_jobs)} Yeni Fırsat Seçildi!")

    # 4. HTML E-posta Bultenini Olustur
    html_report = build_html_newsletter(matched_jobs, hackathons, news, profile)

    # 5. E-Postayi Gonder
    sent = send_email_newsletter(html_report, len(matched_jobs))

    # 6. Hafizayi Guncelle
    if sent and new_urls:
        add_seen_jobs(new_urls)
        print(f"[Memory] {len(new_urls)} yeni ilan linki seen_jobs.json dosyasina kaydedildi.")

    print("\n🎉 Gunluk bulten hazirlama ve gonderim islemi basariyla tamamlandi!")

if __name__ == "__main__":
    main()
