import json
import os

MEMORY_FILE = "seen_jobs.json"

def load_seen_jobs():
    """Hafıza dosyasından daha önce gönderilmiş ilanların (firma ve pozisyon) listesini okur."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def add_seen_jobs(new_jobs):
    """Yeni gönderilen ilanları hafıza dosyasına ekler (Tekrar edenleri engeller)."""
    seen_jobs = load_seen_jobs()
    
    # Sadece daha önce eklenmemiş olanları ekle
    added = False
    for job in new_jobs:
        if job not in seen_jobs:
            seen_jobs.append(job)
            added = True
            
    if added:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(seen_jobs, f, ensure_ascii=False, indent=4)
        print(f"[MEMORY] {len(new_jobs)} yeni ilan/fırsat hafızaya kaydedildi.")
