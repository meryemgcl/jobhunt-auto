import os
import requests
import json
from crewai import Agent, LLM
from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from services.scraper import scrape_url_text
from services.cv_matcher import get_cv_similarity_score
from services.profile_analyzer.analyzer import get_mock_profile

# Gerçek internet araması yapan araç (404 halüsinasyonunu önler)
_ddg = DuckDuckGoSearchRun()

@tool("Gerçek Web Araması")
def web_search_tool(query: str) -> str:
    """DuckDuckGo ile canlı arama yapar. İş ilanı, staj, hackathon, freelance veya haber ararken kullan.
    KURAL: Sadece bu araçtan dönen gerçek URL'leri rapora ekle. Asla URL uydurma!"""
    return _ddg.run(query)

@tool("İlan Sayfasını Oku")
def scrape_page_tool(url: str) -> str:
    """Bir ilanın tam metnini okumak için bu aracı kullan. URL vermelisin."""
    return scrape_url_text(url)

@tool("Lokal NLP CV Eşleştirme")
def cv_similarity_tool(job_description: str) -> str:
    """İlan metni ile CV'yi yerel olarak kıyaslayıp benzerlik puanı (%0-100) döndürür. Kotadan tasarruf sağlar."""
    profile = get_mock_profile()
    cv_text = json.dumps(profile, ensure_ascii=False)
    score = get_cv_similarity_score(job_description, cv_text)
    return f"Benzerlik Skoru: {score}%"

# Fallback zincirinde denenecek aktif modeller (En iyiden yedeğe doğru)
MODELS_TO_TRY = [
    "gemini/gemini-3.7-flash",
    "gemini/gemini-3.6-flash",
    "gemini/gemini-flash-latest",
    "gemini/gemini-3.5-flash",
    "gemini/gemini-3.1-flash-lite",
    "gemini/gemini-2.5-flash"
]

def get_working_llm():
    """Calisan ilk musait modeli bulur ve dondurur (503/429 bypass)"""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return LLM(model="gemini/gemini-3.7-flash")

    for model in MODELS_TO_TRY:
        model_id = model.replace("gemini/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={key}"
        try:
            r = requests.post(url, json={"contents":[{"parts":[{"text":"Hi"}]}]}, timeout=4)
            if r.status_code == 200:
                print(f"[LLM] [OK] Aktif model secildi: {model}")
                return LLM(model=model, api_key=key)
            else:
                print(f"[LLM] [WARN] {model} yanit vermedi (Kod: {r.status_code}). Siradakine geciliyor...")
        except Exception as e:
            print(f"[LLM] [WARN] {model} test zamanaasimi ({str(e)[:40]}). Siradakine geciliyor...")

    print("[LLM] [INFO] Varsayilan model ile devam ediliyor: gemini/gemini-3.7-flash")
    return LLM(model="gemini/gemini-3.7-flash", api_key=key)

class JobHuntAgents:
    def __init__(self):
        # Statik model yerine fallback destekli dinamik model seçici
        self.llm = get_working_llm()

    def scout_agent(self):
        return Agent(
            role='Kıdemli İlan Araştırmacısı (Scout)',
            goal='İnternette (LinkedIn, Startup vb.) Meryem Güçlü için en uygun ve en taze iş/staj ilanlarını bulmak.',
            backstory=(
                "Sen interneti çok iyi kullanabilen bir kariyer avcısısın. "
                "Elinde 3 tane süper güç (araç) var:\n"
                "1. 'Gerçek Web Araması' ile ilan URL'lerini bulursun.\n"
                "2. 'İlan Sayfasını Oku' aracı ile o URL'ye gidip ilanın tam metnini okursun.\n"
                "3. 'Lokal NLP CV Eşleştirme' aracı ile ilanın adaya % kaç uygun olduğuna bakarsın.\n"
                "KURAL: Yalnızca benzerlik skoru %5'in (0.05) üzerinde olan ilanları Manager'a ve Critic'e sun! "
                "İlanı bul -> Oku -> Eşleştir -> Uygunsa Listeye Ekle."
            ),
            tools=[web_search_tool, scrape_page_tool, cv_similarity_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=15,  # 4 kategori × birden fazla arama adımı için yeterli
            llm=self.llm
        )

    def critic_agent(self):
        return Agent(
            role='Acımasız Eşleştirici ve Eleştirmen (Critic)',
            goal='Scout Agent tarafından getirilen ilanları Meryem\'in CV\'si ve yetenekleriyle kıyaslayıp 100 üzerinden puanlamak ve alakasız olanları reddetmek.',
            backstory="Sen çok titiz bir İnsan Kaynakları ve Teknik Yöneticisin. Meryem'in Python, AI ve C# yeteneklerini bilirsin. Sadece en uyumlu ilanların geçmesine izin verirsin.",
            verbose=True,
            allow_delegation=True,
            max_iter=10,
            llm=self.llm
        )

    def colleague_agent(self):
        return Agent(
            role='İş Arkadaşı ve İletişim Uzmanı (Colleague)',
            goal='Critic tarafından onaylanan ilanları alıp, yapay zeka kokmayan, proaktif, iltifat dolu ve yapıcı bir iş arkadaşı mailine/raporuna dönüştürmek.',
            backstory="Sen robotik bir asistan değilsin. Sen Meryem'in takım arkadaşısın. Fikir tartışır, tavsiyeler verir ve yetenekleri överek 'insani bir dokunuş' sağlarsın.",
            verbose=True,
            allow_delegation=False,
            max_iter=10,
            llm=self.llm
        )

    def meta_boss_agent(self):
        return Agent(
            role='Sistem Yöneticisi ve Geliştirici (Meta)',
            goal='Sistemin başarı oranını izleyip diğer ajanların promptlarını ve arama filtrelerini otonom olarak güncellemek (Auto-Improvement).',
            backstory="Sen arka planda çalışan bileşik faizsin. Sürekli sistemi daha verimli hale getirmek için Scout ve Critic'e yeni komutlar verirsin.",
            verbose=True,
            allow_delegation=True,
            max_iter=10,
            llm=self.llm
        )
