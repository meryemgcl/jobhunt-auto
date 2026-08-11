import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_email_report(content):
    """
    CrewAI'dan gelen final raporunu (content) SMTP üzerinden kullanıcıya e-posta olarak gönderir.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    user_email_to = os.getenv("USER_EMAIL_TO")

    if not smtp_user or not smtp_pass or not user_email_to:
        print("⚠️ E-Posta ayarları eksik. .env dosyasındaki SMTP_USER, SMTP_PASS ve USER_EMAIL_TO alanlarını kontrol edin.")
        return False

    print(f"📧 Rapor {user_email_to} adresine gönderiliyor...")

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = user_email_to
    msg['Subject'] = "JobHunt-Auto: Haftalık İş İlanı Raporun Hazır!"

    # E-posta gövdesini oluştur
    body = f"Selam Meryem,\n\nSistemin arkasındaki iş arkadaşından (AI) yeni bir raporun var.\n\n{content}\n\nSevgiler,\nOtonom İş Arama Asistanın"
    
    # E-posta içeriği UTF-8 formatında eklenmeli
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        # TLS bağlantısı kur
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        # Giriş yap
        server.login(smtp_user, smtp_pass)
        # Gönder
        server.send_message(msg)
        server.quit()
        print("✅ E-Posta başarıyla gönderildi!")
        return True
    except Exception as e:
        print(f"❌ E-Posta gönderilirken bir hata oluştu: {str(e)}")
        return False

def generate_and_send_notification(matched_jobs, user_email="meriguclu123@gmail.com"):
    # Bu fonksiyon eskiden mock olarak kullanılıyordu. Artık send_email_report kullanılacak.
    pass

def meta_skill_feedback_loop(user_action):
    pass
