import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Bu script otomasyon klasöründe çalışacak
load_dotenv()

def test_mail():
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    user_email_to = os.getenv("USER_EMAIL_TO")

    print(f"Gonderici: {smtp_user}, Alici: {user_email_to}")
    
    if not smtp_user or not smtp_pass:
        print("HATA: Bilgiler eksik.")
        return

    msg = MIMEText("Sistem testi: Sadece bunu okuyabiliyorsaniz, e-posta ayarlarimiz tamamen dogru calisiyordur.", "plain", "utf-8")
    msg['Subject'] = "JobHunt-Auto TEST"
    msg['From'] = smtp_user
    msg['To'] = user_email_to

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.set_debuglevel(1)  # Tüm SMTP yanıtlarını göster
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print("\n\nBASARILI: Test e-postasi iletildi!")
    except Exception as e:
        print("\n\nHATA OLUSTU:", e)

if __name__ == "__main__":
    test_mail()
