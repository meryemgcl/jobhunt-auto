import sys
import io
# Windows terminalleri için emoji destekli UTF-8 çıktısını zorla
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from crewai import Crew, Process
from agents import JobHuntAgents
from tasks import JobHuntTasks
from services.profile_analyzer.analyzer import get_mock_profile
from dotenv import load_dotenv

# .env dosyasını yükle
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

    # Görevleri Ajanlara Ata
    search_task = tasks.search_jobs_task(scout)
    eval_task = tasks.evaluate_jobs_task(critic, profile)
    email_task = tasks.draft_email_task(colleague)
    
    # 3. Konseyi (Crew) Kur
    job_hunt_crew = Crew(
        agents=[scout, critic, colleague],
        tasks=[search_task, eval_task, email_task],
        process=Process.sequential,  # Scout -> Critic -> Colleague sırasıyla çalışır
        verbose=True
    )
    
    print("Konsey işbaşı yaptı! Ajanlar kendi aralarında anlaşıp raporu hazırlıyor...\n")
    
    import time
    max_retries = 3
    result = None
    for attempt in range(max_retries):
        try:
            print(f"Görevi Başlatılıyor... (Deneme {attempt + 1}/{max_retries})")
            result = job_hunt_crew.kickoff()
            break
        except Exception as e:
            error_str = str(e)
            print(f"HATA: API İsteği başarısız oldu: {error_str}")
            if "503" in error_str or "UNAVAILABLE" in error_str:
                if attempt < max_retries - 1:
                    print("Google Gemini API şu an aşırı yoğun (503). 30 saniye bekleniyor...")
                    time.sleep(30)
                else:
                    print("Maksimum deneme sayısına ulaşıldı. Lütfen daha sonra tekrar deneyin.")
                    sys.exit(1)
            else:
                # Beklenmeyen başka bir hataysa direkt çık
                raise e
                
    print("\n--- CREWAI FINAL RAPORU ---")
    print(result)
    
    # Raporu E-Posta olarak gönder
    from services.notification_and_meta.notifier import send_email_report
    
    # result objesi CrewOutput türündedir, string formatına çevirip yolluyoruz
    send_email_report(str(result))
    
    print("\n[MOCK] Ajanlar aralarında konuştu, ilanları filtreledi ve mail metnini hazırladı.")
    print("Tüm süreç CrewAI mimarisiyle otonom olarak (AutoGPT mantığı) kurgulandı ve rapor yollandı.")

if __name__ == "__main__":
    main()
