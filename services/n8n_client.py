import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_to_n8n(report_content: str):
    """
    Görev sonucunu (CrewAI raporunu) n8n webhook'una gönderir.
    n8n tarafında bir 'Webhook' node'u olmalıdır.
    """
    # .env dosyasından N8N_WEBHOOK_URL okuyoruz. 
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    
    if not webhook_url:
        print("⚠️ N8N_WEBHOOK_URL .env dosyasında bulunamadı. n8n'e veri gönderilmiyor.")
        return False
        
    payload = {
        "source": "JobHunt-Auto CrewAI",
        "report": report_content
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print(f"✅ Sonuç n8n'e başarıyla gönderildi! (HTTP {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ n8n webhook isteği başarısız oldu: {e}")
        return False
