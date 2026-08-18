import os
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from main import main as run_crewai_job

app = FastAPI(
    title="JobHunt-Auto n8n Trigger API",
    description="n8n üzerinden CrewAI sistemini tetiklemek için kullanılan servis.",
    version="1.0"
)

def crewai_background_task():
    """Arka planda CrewAI görevini çalıştırır."""
    print("🚀 n8n tarafından tetikleme alındı. CrewAI başlatılıyor...")
    run_crewai_job()

@app.api_route("/trigger-crew", methods=["GET", "POST"])
async def trigger_crew(background_tasks: BackgroundTasks):
    """
    n8n üzerinden HTTP POST ile bu endpoint'e istek atılarak
    CrewAI süreçleri asenkron olarak başlatılabilir.
    """
    background_tasks.add_task(crewai_background_task)
    return {"status": "success", "message": "CrewAI task successfully queued."}

@app.get("/")
async def root():
    return {"message": "JobHunt-Auto API Çalışıyor. /trigger-crew adresine POST isteği atabilirsiniz."}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
