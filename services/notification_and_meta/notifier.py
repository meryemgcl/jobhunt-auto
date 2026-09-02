import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def build_html_newsletter(matched_jobs, hackathons, news, profile):
    """Modern, sik ve kurumsal bir HTML bulteni olusturur."""
    
    # 1. Is Kartlari HTML'i
    jobs_html = ""
    for j in matched_jobs[:8]: # En iyi 8 ilan
        score_badge = f"<span style='background:#10b981;color:#fff;padding:3px 8px;border-radius:12px;font-size:12px;font-weight:bold;'>⭐ %{j['score']} Uyumlu</span>"
        jobs_html += f"""
        <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <h3 style="margin:0;color:#1e293b;font-size:16px;">{j['title']}</h3>
                {score_badge}
            </div>
            <p style="margin:4px 0;color:#64748b;font-size:13px;">
                🏢 <b>{j['company']}</b> | 📍 {j['location']} | 📅 {j['published_at']} | 🏷️ Kaynak: {j['source']}
            </p>
            <p style="margin:8px 0;color:#334155;font-size:13px;background:#f8fafc;padding:8px;border-left:3px solid #3b82f6;border-radius:2px;">
                🎯 <b>Neden Sana Uygun?</b> {j['match_reason']}
            </p>
            <div style="margin-top:10px;">
                <a href="{j['url']}" style="background:#2563eb;color:#ffffff;text-decoration:none;padding:6px 14px;border-radius:6px;font-size:13px;font-weight:bold;display:inline-block;">İlana Git & Başvur ➔</a>
            </div>
        </div>
        """

    # 2. Hackathon HTML'i
    hackathons_html = ""
    for h in hackathons:
        hackathons_html += f"""
        <li style="margin-bottom:8px;font-size:13px;color:#334155;">
            🏆 <b>{h['title']}</b> ({h['platform']}) - <span style="color:#059669;">{h['status']}</span> 
            <a href="{h['url']}" style="color:#2563eb;margin-left:6px;text-decoration:none;font-weight:bold;">Katıl ➔</a>
        </li>
        """

    # 3. Haberler HTML'i
    news_html = ""
    for n in news:
        news_html += f"""
        <li style="margin-bottom:8px;font-size:13px;color:#334155;">
            📰 <b>{n['title']}</b> - <span style="color:#64748b;">({n['source']})</span>
            <a href="{n['url']}" style="color:#2563eb;margin-left:6px;text-decoration:none;">Haberi Oku ➔</a>
        </li>
        """

    # Ana E-posta Sablonu
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;background-color:#f1f5f9;margin:0;padding:20px;">
        <div style="max-width:680px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.05);">
            
            <!-- Header -->
            <div style="background:linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);color:#ffffff;padding:25px;text-align:center;">
                <h1 style="margin:0;font-size:22px;">🚀 JobHunt-Auto | Günlük Kariyer Bülteni</h1>
                <p style="margin:6px 0 0 0;font-size:14px;color:#c7d2fe;">Meryem Güçlü için Özel Olarak Filtrelendi</p>
            </div>

            <!-- Profil Ozeti -->
            <div style="background:#e0e7ff;padding:12px 20px;border-bottom:1px solid #c7d2fe;font-size:13px;color:#3730a3;">
                💡 <b>Odak Alanların:</b> Python, AI / Makine Öğrenimi, Backend, C#, Staj & Junior Pozisyonlar
            </div>

            <div style="padding:20px;">
                <!-- Is Ilanlari -->
                <h2 style="color:#1e293b;font-size:17px;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:0;">
                    💼 Senin İçin Seçilen En Taze İlanlar ({len(matched_jobs)} Fırsat)
                </h2>
                {jobs_html if jobs_html else "<p style='color:#64748b;'>Bugün için yeni bir ilan bulunamadı.</p>"}

                <!-- Hackathonlar -->
                <h2 style="color:#1e293b;font-size:17px;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:25px;">
                    🏆 Aktif Hackathon & Yarışmalar
                </h2>
                <ul style="padding-left:18px;margin:10px 0;">
                    {hackathons_html}
                </ul>

                <!-- Teknoloji Gelismeleri -->
                <h2 style="color:#1e293b;font-size:17px;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:25px;">
                    🔥 Günün Öne Çıkan Teknoloji Haberleri
                </h2>
                <ul style="padding-left:18px;margin:10px 0;">
                    {news_html}
                </ul>
            </div>

            <!-- Footer -->
            <div style="background:#f8fafc;padding:15px;text-align:center;border-top:1px solid #e2e8f0;font-size:12px;color:#94a3b8;">
                Bu bülten <b>JobHunt-Auto</b> deterministik veri motoru tarafından otomatik olarak derlenmiştir.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_email_newsletter(html_content, total_jobs_count):
    """SMTP uzerinden kullaniciya guvenli e-posta gonderir."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    user_email_to = os.getenv("USER_EMAIL_TO")

    if not smtp_user or not smtp_pass or not user_email_to:
        print("⚠️ E-Posta ayarlari eksik. SMTP_USER, SMTP_PASS ve USER_EMAIL_TO degiskenlerini kontrol edin.")
        return False

    print(f"📧 Rapor {user_email_to} adresine gonderiliyor...")

    msg = MIMEMultipart("alternative")
    msg["From"] = f"JobHunt-Auto 🤖 <{smtp_user}>"
    msg["To"] = user_email_to
    msg["Subject"] = f"🚀 JobHunt-Auto | {total_jobs_count} Yeni Fırsat & Günlük Kariyer Bültenin!"

    msg.attach(MIMEText("Lütfen HTML destekleyen bir e-posta istemcisi kullanın.", "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print("✅ E-Posta basariyla gonderildi!")
        return True
    except Exception as e:
        print(f"❌ E-Posta gonderilirken hata: {e}")
        return False
