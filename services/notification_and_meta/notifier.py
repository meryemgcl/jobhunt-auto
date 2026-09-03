import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def build_html_newsletter(matched_jobs, camps, rd_projects, podcasts, hackathons, news, profile):
    """Kapsamli, kategorize edilmis ve sik bir HTML bulteni olusturur."""
    
    # 1. Is & Staj Kartlari HTML
    jobs_html = ""
    for j in matched_jobs[:8]:
        score_badge = f"<span style='background:#10b981;color:#fff;padding:3px 8px;border-radius:12px;font-size:12px;font-weight:bold;'>⭐ %{j['score']} Uyumlu</span>"
        jobs_html += f"""
        <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:15px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.03);">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                <h3 style="margin:0;color:#0f172a;font-size:15px;line-height:1.3;">{j['title']}</h3>
                <div style="margin-left:8px;white-space:nowrap;">{score_badge}</div>
            </div>
            <p style="margin:4px 0;color:#64748b;font-size:12px;">
                🏢 <b>{j['company']}</b> | 📍 {j['location']} | 📅 {j['published_at']} | 🏷️ {j['source']}
            </p>
            <p style="margin:6px 0;color:#334155;font-size:13px;background:#f8fafc;padding:8px;border-left:3px solid #3b82f6;border-radius:2px;">
                🎯 <b>Neden Sana Uygun?</b> {j['match_reason']}
            </p>
            <div style="margin-top:8px;">
                <a href="{j['url']}" style="background:#2563eb;color:#ffffff;text-decoration:none;padding:5px 12px;border-radius:6px;font-size:12px;font-weight:bold;display:inline-block;">İlana Git & Başvur ➔</a>
            </div>
        </div>
        """

    # 2. Bootcampler & Egitim Kamplari
    camps_html = ""
    for c in camps:
        camps_html += f"""
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:10px 14px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#166534;font-weight:bold;font-size:13px;">🎓 {c['title']}</span>
                <span style="color:#15803d;font-size:11px;background:#dcfce7;padding:2px 6px;border-radius:4px;">{c['status']}</span>
            </div>
            <div style="margin-top:4px;font-size:12px;">
                <span style="color:#64748b;">Kurum: {c['platform']}</span> - 
                <a href="{c['url']}" style="color:#16a34a;font-weight:bold;text-decoration:none;">Programa İncele & Katıl ➔</a>
            </div>
        </div>
        """

    # 3. AR-GE & TUBITAK Projeleri
    rd_html = ""
    for r in rd_projects:
        rd_html += f"""
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:10px 14px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#1e40af;font-weight:bold;font-size:13px;">🔬 {r['title']}</span>
                <span style="color:#1d4ed8;font-size:11px;background:#dbeafe;padding:2px 6px;border-radius:4px;">{r['organization']}</span>
            </div>
            <p style="margin:4px 0 0 0;font-size:12px;color:#475569;">
                {r['type']} - <a href="{r['url']}" style="color:#2563eb;font-weight:bold;text-decoration:none;">Başvuru & Detaylar ➔</a>
            </p>
        </div>
        """

    # 4. Podcastler
    podcasts_html = ""
    for p in podcasts:
        podcasts_html += f"""
        <div style="background:#faf5ff;border:1px solid #e9d5ff;border-radius:6px;padding:10px 14px;margin-bottom:8px;">
            <div style="color:#6b21a8;font-weight:bold;font-size:13px;">🎧 {p['title']}</div>
            <div style="color:#7e22ce;font-size:12px;margin:2px 0;">{p['topic']}</div>
            <div style="font-size:11px;margin-top:4px;">
                <a href="{p['url']}" style="color:#9333ea;font-weight:bold;text-decoration:none;">Spotify / Podcast'te Dinle ➔</a>
            </div>
        </div>
        """

    # 5. Hackathonlar
    hackathons_html = ""
    for h in hackathons:
        hackathons_html += f"""
        <li style="margin-bottom:6px;font-size:13px;color:#334155;">
            🏆 <b>{h['title']}</b> ({h['platform']}) - <span style="color:#059669;">{h['status']}</span> 
            <a href="{h['url']}" style="color:#2563eb;margin-left:4px;text-decoration:none;font-weight:bold;">Katıl ➔</a>
        </li>
        """

    # 6. Haberler
    news_html = ""
    for n in news:
        news_html += f"""
        <li style="margin-bottom:6px;font-size:13px;color:#334155;">
            📰 <b>{n['title']}</b> <span style="color:#64748b;font-size:11px;">({n['source']})</span>
            <a href="{n['url']}" style="color:#2563eb;margin-left:4px;text-decoration:none;">Oku ➔</a>
        </li>
        """

    # Ana E-Posta Gövdesi
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;background-color:#f8fafc;margin:0;padding:20px;">
        <div style="max-width:700px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);border:1px solid #e2e8f0;">
            
            <!-- Header -->
            <div style="background:linear-gradient(135deg, #0f172a 0%, #1e293b 100%);color:#ffffff;padding:24px;text-align:center;">
                <h1 style="margin:0;font-size:22px;letter-spacing:-0.5px;">🚀 JobHunt-Auto | Kişiselleştirilmiş Kariyer Bülteni</h1>
                <p style="margin:6px 0 0 0;font-size:13px;color:#94a3b8;">Meryem Güçlü • Türkiye & Uzaktan / Sivas & Erzurum & Global Fırsatlar</p>
            </div>

            <!-- Bilgilendirme Rozeti -->
            <div style="background:#f1f5f9;padding:12px 20px;border-bottom:1px solid #e2e8f0;font-size:12px;color:#475569;line-height:1.5;">
                📍 <b>Hedef Konumlar:</b> Sivas, Erzurum, Türkiye Geneli Uzaktan (Remote) & Hibrit<br>
                💡 <b>Odak Alanlar:</b> Python, AI / Makine Öğrenimi, Backend, C#, Staj, Bootcampler ve AR-GE
            </div>

            <div style="padding:20px;">
                
                <!-- 1. Is & Staj Firsatlari -->
                <h2 style="color:#0f172a;font-size:16px;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:0;">
                    💼 Seçilen İş ve Staj Fırsatları ({len(matched_jobs)} İlan)
                </h2>
                {jobs_html if jobs_html else "<p style='color:#64748b;'>Yeni ilan bulunamadı.</p>"}

                <!-- 2. Bootcampler & Egitim Kamplari -->
                <h2 style="color:#0f172a;font-size:16px;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:25px;">
                    🎓 Ücretsiz Eğitim Kampları & Bootcampler
                </h2>
                {camps_html}

                <!-- 3. AR-GE & TUBITAK Projeleri -->
                <h2 style="color:#0f172a;font-size:16px;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:25px;">
                    🔬 AR-GE Projeleri & TÜBİTAK 2209 Öğrenci Destekleri
                </h2>
                {rd_html}

                <!-- 4. Podcast Onerileri -->
                <h2 style="color:#0f172a;font-size:16px;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:25px;">
                    🎧 Haftalık Geliştirici & Teknoloji Podcast'leri
                </h2>
                {podcasts_html}

                <!-- 5. Hackathonlar -->
                <h2 style="color:#0f172a;font-size:16px;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:25px;">
                    🏆 Aktif Yarışma & Hackathon Platformları
                </h2>
                <ul style="padding-left:18px;margin:8px 0;">
                    {hackathons_html}
                </ul>

                <!-- 6. Teknoloji Haberleri -->
                <h2 style="color:#0f172a;font-size:16px;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:25px;">
                    📰 Günün Trend Teknoloji Haberleri
                </h2>
                <ul style="padding-left:18px;margin:8px 0;">
                    {news_html}
                </ul>
            </div>

            <!-- Footer -->
            <div style="background:#f8fafc;padding:15px;text-align:center;border-top:1px solid #e2e8f0;font-size:11px;color:#94a3b8;">
                Bu bülten <b>JobHunt-Auto Deterministik Motoru</b> tarafından otomatik olarak derlenmiştir.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_email_newsletter(html_content, total_jobs_count):
    """SMTP uzerinden guvenli e-posta gonderir."""
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
    msg["Subject"] = f"🚀 JobHunt-Auto | {total_jobs_count} İş/Staj + Bootcampler, AR-GE ve Podcast Bültenin!"

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
