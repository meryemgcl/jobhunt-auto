import os
import requests
from crewai import Agent, LLM
from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

# Gerçek internet araması yapan araç (404 halüsinasyonunu önler)
_ddg = DuckDuckGoSearchRun()

@tool("Gerçek Web Araması")
def web_search_tool(query: str) -> str:
    """DuckDuckGo ile canlı arama yapar. İş ilanı, staj, hackathon, freelance veya haber ararken kullan.
    KURAL: Sadece bu araçtan dönen gerçek URL'leri rapora ekle. Asla URL uydurma!"""
    return _ddg.run(query)

# Fallback zincirinde denenecek modeller (en iyiden yedeğe)
_MODELS = [
    "gemini/gemini-flash-latest",
    "gemini/gemini-3.6-flash",
    "gemini/gemini-1.5-flash",
    "gemini/gemini-1.5-pro",
]

def get_working_llm():
    """Sırayla Gemini modellerini test eder, çalışan ilk modeli döndürür (503/429 bypass)."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return LLM(model="gemini/gemini-3.6-flash")
    for model in _MODELS:
        model_id = model.replace("gemini/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={key}"
        try:
            r = requests.post(url, json={"contents": [{"parts": [{"text": "Hi"}]}]}, timeout=10)
            if r.status_code == 200:
                print(f"[LLM] Aktif model: {model}")
                return LLM(model=model, api_key=key)
            print(f"[LLM] {model} -> {r.status_code}, bir sonrakine geciliyor...")
        except Exception as e:
            print(f"[LLM] {model} -> hata: {str(e)[:40]}, bir sonrakine geciliyor...")
    print("[LLM] Tum modeller mesgul, varsayilan kullaniliyor.")
    return LLM(model="gemini/gemini-3.6-flash", api_key=key)

class JobHuntAgents:
    def __init__(self):
        # Statik model yerine fallback destekli dinamik model secici
        self.llm = get_working_llm()

    def scout_agent(self):
        return Agent(
            role='Kıdemli İlan Araştırmacısı (Scout)',
            goal='İnternette (LinkedIn, Startup vb.) Meryem Güçlü için en uygun ve en taze iş/staj ilanlarını bulmak.',
            backstory=(
                "Sen interneti çok iyi kullanabilen bir kariyer avcısısın. "
                "Elinde gerçek bir arama motoru aracı var ve bunu kullanarak GERÇEK ilanları bulursun. "
                "ASLA link uydurmazsın. Sadece 'Gerçek Web Araması' aracından gelen, "
                "gerçek ve tıklanabilir URL'leri rapora eklersin. "
                "Bulduğun ham ilanları eleştirmenine (Critic) sunarsın."
            ),
            tools=[web_search_tool],
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
            max_iter=self.max_iter,
            llm=self.llm
        )
