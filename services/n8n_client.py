import os
import logging

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def send_to_n8n(report_content: str):
    """
    Görev sonucunu (JobHunt-Auto raporunu) n8n webhook'una gönderir.
    n8n tarafında bir 'Webhook' node'u olmalıdır.
    """
    # .env dosyasından N8N_WEBHOOK_URL okuyoruz. 
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    
    if not webhook_url:
        logger.warning("N8N_WEBHOOK_URL .env dosyasinda bulunamadi. n8n'e veri gonderilmiyor.")
        return False
        
    payload = {
        "source": "JobHunt-Auto Deterministic Engine",
        "report": report_content
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        logger.info("Sonuc n8n'e basariyla gonderildi. http_status=%s", response.status_code)
        return True
    except requests.exceptions.RequestException as e:
        logger.error("n8n webhook istegi basarisiz oldu: %s", e)
        return False
