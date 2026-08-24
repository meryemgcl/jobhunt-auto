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

    msg = MIMEMultipart('alternative')
    msg['From'] = f"JobHunt-Auto 🤖 <{smtp_user}>"
    msg['To'] = user_email_to
    msg['Subject'] = "🚀 JobHunt-Auto | Günlük Kariyer Bültenin Hazır!"

    import markdown

    plain_body = f"JobHunt-Auto Günlük Bülten\n\n{content}\n\nSevgilerle,\nJobHunt-Auto Asistanın 🤖"

    # Ajanlardan gelen Markdown metnini temiz HTML'e dönüştür
    html_rendered = markdown.markdown(content, extensions=['extra', 'nl2br'])

    html_body = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 700px; margin: auto; color: #333;">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;text-align:center;">
        <h1 style="color:#e94560;margin:0;">🚀 JobHunt-Auto</h1>
        <p style="color:#aaa;margin:5px 0;">Yapay Zeka Destekli Kariyer Asistanın</p>
      </div>
      <div style="background:#f9f9f9;padding:25px;border-radius:0 0 8px 8px;border:1px solid #eee;line-height:1.7;">
        {html_rendered}
      </div>
      <p style="text-align:center;color:#aaa;font-size:12px;margin-top:10px;">
        Bu e-posta <b>JobHunt-Auto</b> tarafından otomatik olarak gönderilmiştir.
      </p>
    </body></html>
    """

    # Hem düz metin hem HTML ekle (istemci HTML desteklemiyorsa düz metni gösterir)
    msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

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
