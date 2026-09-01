import os
import sys
import io
import time
import re

# Windows terminalleri için emoji destekli UTF-8 çıktısını zorla
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from crewai import Crew, Process
from agents import JobHuntAgents, get_working_llm
from tasks import JobHuntTasks
from services.profile_analyzer.analyzer import get_mock_profile
from dotenv import load_dotenv

load_dotenv()


def main():
    print("🤖 AutoGPT (CrewAI) Tabanlı JobHunt-Auto Başlatılıyor...\n")
    
    # 1. Meryem'in Profilini Al (Gerçekte PDF'ten okunacak)
    profile = get_mock_profile()
    
    # 2. Ajanları ve Görevleri Başlat
    agents = JobHuntAgents()
    tasks = JobHuntTasks()
    
    scout = agents.scout_agent()
    critic = agents.critic_agent()
    colleague = agents.colleague_agent()
    
    # Meta ajan şimdilik döngü dışı (gözlemci)
    # meta_boss = agents.meta_boss_agent() 

    # 3. Hafızayı (Memory) Yükle
    from services.memory import load_seen_jobs
    seen_jobs = load_seen_jobs()
    # Hafızanın şişmesini engellemek için son 30 linki ajana gönderelim
    seen_jobs_str = ", ".join(seen_jobs[-30:]) if seen_jobs else "Yok"

    # Görevleri Ajanlara Ata (Rate Limit önlemek için tek kapsamlı arama görevi)
    search_task = tasks.search_jobs_task(scout)
    eval_task = tasks.evaluate_jobs_task(critic, profile, seen_jobs_str)
    email_task = tasks.draft_email_task(colleague)
    
    # 3. Konseyi (Crew) Kur — Hiyerarşik Süreç
    # Manager LLM görev dağıtımını otonom yönetir;
    # Scout kötü ilan getirirse Manager onu tekrar arama yapması için yönlendirebilir.
    job_hunt_crew = Crew(
        agents=[scout, critic, colleague],
        tasks=[search_task, eval_task, email_task],
        process=Process.hierarchical,
        manager_llm=get_working_llm(),
        verbose=True
    )

    print("Konsey işbaşı yaptı! Ajanlar kendi aralarında anlaşıp raporu hazırlıyor...\n")

    # Görevi Başlat — 503/429 için exponential-backoff retry mekanizması
    max_retries = 5
    result = None
    for attempt in range(max_retries):
        try:
            print(f"Görevi Başlatılıyor... (Deneme {attempt + 1}/{max_retries})")
            result = job_hunt_crew.kickoff()
            print(f"✅ {attempt + 1}. denemede başarılı.")
            break
        except Exception as e:
            error_str = str(e)
            print(f"HATA: API İsteği başarısız oldu: {error_str}")
            if "503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str:
                if attempt < max_retries - 1:
                    wait = 60 * (attempt + 1)
                    print(f"Google Gemini API şu an aşırı yoğun. {wait} saniye bekleniyor...")
                    time.sleep(wait)
                else:
                    print("Maksimum deneme sayısına ulaşıldı.")
                    sys.exit(1)
            else:
                raise

    print("\n--- CREWAI FINAL RAPORU ---")
    print(result)

    # Raporu E-Posta olarak gönder
    from services.notification_and_meta.notifier import send_email_report
    from services.n8n_client import send_to_n8n

    report_str = str(result)
    send_email_report(report_str)
    send_to_n8n(report_str)

    # Hafızayı Güncelle — rapora düşen URL'leri kaydet
    from services.memory import add_seen_jobs
    found_urls = re.findall(r'(https?://\S+)', report_str)
    if found_urls:
        add_seen_jobs(found_urls)

    print("\nTüm süreç CrewAI mimarisiyle otonom olarak tamamlandı ve rapor yollandı.")

if __name__ == "__main__":
    main()
