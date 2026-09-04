import sys
import io

# Windows terminalleri icin UTF-8 destegi
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from config import FEATURE_FLAGS
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
from services.github_radar import fetch_good_first_issues
from services.analytics import analyze_market_skill_gap
from services.matcher import score_job_suitability
from services.tracker import update_career_dashboard
from services.notification_and_meta.notifier import build_html_newsletter, send_email_newsletter

def main():
    print("🚀 JobHunt-Auto Gelismis Deterministik Motor Baslatiliyor...\n")

    # 1. Profil ve Hafizayi Yukle
    profile = get_mock_profile()
    seen_jobs = set(load_seen_jobs())
    print(f"[Memory] Toplam {len(seen_jobs)} daha once gorulmus ilan hafizada.")

    # 2. Tum Kategorilerde Canli Veri Topla
    print("\n🔍 1/7: Türkiye (Sivas/Erzurum/Kayseri/Malatya/Konya/Uzaktan) & Global İlanlar Toplanıyor...")
    raw_jobs = fetch_jobs()
    print(f"-> Toplam {len(raw_jobs)} pozisyon tarandı.")

    print("🔍 2/7: GitHub Good First Issue & Açık Kaynak Radarı Taranıyor...")
    github_issues = fetch_good_first_issues() if FEATURE_FLAGS.get("ENABLE_GITHUB_RADAR", True) else []
    print(f"-> {len(github_issues)} açık kaynak katkı fırsatı bulundu.")

    print("🔍 3/7: Ücretsiz Bootcampler & Eğitim Kampları Derleniyor...")
    camps = fetch_bootcamps_and_camps()
    print(f"-> {len(camps)} kamp ve akademi programı hazırlandı.")

    print("🔍 4/7: AR-GE & TÜBİTAK 2209 Öğrenci Projeleri Kontrol Ediliyor...")
    rd_projects = fetch_r_and_d_projects()
    print(f"-> {len(rd_projects)} AR-GE fırsatı eklendi.")

    print("🔍 5/7: Haftalık Geliştirici & Teknoloji Podcast'leri Derleniyor...")
    podcasts = fetch_podcasts()
    print(f"-> {len(podcasts)} podcast derlendi.")

    print("🔍 6/7: Aktif Yarışma & Hackathon Platformları Listeleniyor...")
    hackathons = fetch_hackathons()
    print(f"-> {len(hackathons)} yarışma platformu hazırlandı.")

    print("🔍 7/7: Güncel Teknoloji & Python Haberleri Çekiliyor...")
    news = fetch_tech_news()
    print(f"-> {len(news)} haber eklendi.")

    # 3. Piyasa Yetenek Acigi (Skill Gap) Analizi (Adim 1)
    skill_gap = {}
    if FEATURE_FLAGS.get("ENABLE_SKILL_GAP_ANALYSIS", True):
        skill_gap = analyze_market_skill_gap(raw_jobs, profile.get("core_skills", []))
        print(f"\n📊 {skill_gap.get('summary_text', '')}")

    # 4. İlanları Filtreleme ve Uyum Puanlaması
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
    print(f"\n🎯 Profil Kriterlerine Uyumlu {len(matched_jobs)} Yeni Fırsat Seçildi!")

    # 5. DASHBOARD.md ve applications.json Guncelle (Adim 4)
    if FEATURE_FLAGS.get("ENABLE_DASHBOARD_TRACKING", True):
        update_career_dashboard(len(raw_jobs), len(matched_jobs), skill_gap)

    # 6. Zengin Kurumsal HTML E-posta Bültenini Oluştur
    html_report = build_html_newsletter(
        matched_jobs=matched_jobs,
        camps=camps,
        rd_projects=rd_projects,
        podcasts=podcasts,
        hackathons=hackathons,
        news=news,
        github_issues=github_issues,
        skill_gap=skill_gap,
        profile=profile
    )

    # 7. E-Postayı Gönder
    sent = send_email_newsletter(html_report, len(matched_jobs))

    # 8. Hafızayı Güncelle
    if sent and new_urls:
        add_seen_jobs(new_urls)
        print(f"[Memory] {len(new_urls)} yeni ilan linki seen_jobs.json dosyasina kaydedildi.")

    print("\n🎉 Kurumsal kariyer istihbarat bülteni başarıyla derlendi ve gönderildi!")

if __name__ == "__main__":
    main()
