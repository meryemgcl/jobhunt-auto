import os
from crewai import Agent, LLM
from crewai_tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

# Gerçek internet araması yapan araç (404 halüsinasyonunu önler)
_ddg_search = DuckDuckGoSearchRun()

@tool("Gerçek Web Araması")
def web_search_tool(query: str) -> str:
    """DuckDuckGo üzerinden gerçek web araması yapar ve gerçek sonuçlar döndürür. 
    Kullan: iş ilanı, staj, hackathon, freelance fırsat veya haber ararken.
    UYARI: Sadece bu araçtan gelen URL'leri kullan, asla URL uydurma!"""
    return _ddg_search.run(query)

class JobHuntAgents:
    def __init__(self):
        # Ajanların sonsuz döngüye girmemesi için maksimum limit
        self.max_iter = 5
        
        # CrewAI'nin kendi LLM sarmalayıcısını kullanarak Gemini'yi tanımlıyoruz
        self.llm = LLM(
            model="gemini/gemini-3.6-flash",
            api_key=os.getenv("GEMINI_API_KEY")
        )

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
            max_iter=self.max_iter,
            llm=self.llm
        )

    def critic_agent(self):
        return Agent(
            role='Acımasız Eşleştirici ve Eleştirmen (Critic)',
            goal='Scout Agent tarafından getirilen ilanları Meryem\'in CV\'si ve yetenekleriyle kıyaslayıp 100 üzerinden puanlamak ve alakasız olanları reddetmek.',
            backstory="Sen çok titiz bir İnsan Kaynakları ve Teknik Yöneticisin. Meryem'in Python, AI ve C# yeteneklerini bilirsin. Sadece en uyumlu ilanların geçmesine izin verirsin.",
            verbose=True,
            allow_delegation=True,
            max_iter=self.max_iter,
            llm=self.llm
        )

    def colleague_agent(self):
        return Agent(
            role='İş Arkadaşı ve İletişim Uzmanı (Colleague)',
            goal='Critic tarafından onaylanan ilanları alıp, yapay zeka kokmayan, proaktif, iltifat dolu ve yapıcı bir iş arkadaşı mailine/raporuna dönüştürmek.',
            backstory="Sen robotik bir asistan değilsin. Sen Meryem'in takım arkadaşısın. Fikir tartışır, tavsiyeler verir ve yetenekleri överek 'insani bir dokunuş' sağlarsın.",
            verbose=True,
            allow_delegation=False,
            max_iter=self.max_iter,
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
