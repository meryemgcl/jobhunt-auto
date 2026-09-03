import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

def build_html_newsletter(matched_jobs, camps, rd_projects, podcasts, hackathons, news, profile):
    """Kurumsal, profesyonel ve objektif bir sistem istihbarat raporu olusturur."""
    
    current_date_str = datetime.datetime.now().strftime('%d.%m.%Y')
    
    # 1. Is & Staj Kartlari
    jobs_html = ""
    for j in matched_jobs[:8]:
        score_badge = f"<span style='background:#047857;color:#ffffff;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:700;letter-spacing:0.3px;'>%{j['score']} EŞLEŞME İNDEKSİ</span>"
        jobs_html += f"""
        <div style="background:#ffffff;border:1px solid #cbd5e1;border-radius:8px;padding:16px;margin-bottom:14px;box-shadow:0 1px 3px rgba(15,23,42,0.04);">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                <h3 style="margin:0;color:#0f172a;font-size:15px;font-weight:700;line-height:1.3;">{j['title']}</h3>
                <div style="margin-left:10px;white-space:nowrap;">{score_badge}</div>
            </div>
            <div style="margin:4px 0 8px 0;color:#475569;font-size:12px;">
                🏢 <b>Kurum:</b> {j['company']} &nbsp;|&nbsp; 📍 <b>Konum:</b> {j['location']} &nbsp;|&nbsp; 📅 <b>Tarih:</b> {j['published_at']} &nbsp;|&nbsp; 🏷️ <b>Ağ:</b> {j['source']}
            </div>
            <div style="margin:8px 0;color:#1e293b;font-size:12px;background:#f8fafc;padding:10px 12px;border-left:3px solid #2563eb;border-radius:2px;line-height:1.5;">
                🔍 <b>Sistem Uygunluk Analizi:</b> {j['match_reason']}
            </div>
            <div style="margin-top:10px;">
                <a href="{j['url']}" style="background:#0f172a;color:#ffffff;text-decoration:none;padding:6px 14px;border-radius:4px;font-size:12px;font-weight:600;display:inline-block;">İlanı İncele & Doğrudan Başvur ➔</a>
            </div>
        </div>
        """

    # 2. Bootcampler & Egitim Kamplari
    camps_html = ""
    for c in camps:
        camps_html += f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px 14px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#0f172a;font-weight:600;font-size:13px;">🎓 {c['title']}</span>
                <span style="color:#047857;font-size:11px;font-weight:600;background:#d1fae5;padding:2px 6px;border-radius:3px;">{c['status']}</span>
            </div>
            <div style="margin-top:4px;font-size:12px;color:#64748b;">
                Platform: <b>{c['platform']}</b> &nbsp;|&nbsp; 
                <a href="{c['url']}" style="color:#2563eb;font-weight:600;text-decoration:none;">Program Detayları & Kayıt ➔</a>
            </div>
        </div>
        """

    # 3. AR-GE & TUBITAK Projeleri
    rd_html = ""
    for r in rd_projects:
        rd_html += f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px 14px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#0f172a;font-weight:600;font-size:13px;">🔬 {r['title']}</span>
                <span style="color:#1d4ed8;font-size:11px;font-weight:600;background:#dbeafe;padding:2px 6px;border-radius:3px;">{r['organization']}</span>
            </div>
            <div style="margin-top:4px;font-size:12px;color:#64748b;">
                Kapsam: {r['type']} &nbsp;|&nbsp; 
                <a href="{r['url']}" style="color:#2563eb;font-weight:600;text-decoration:none;">Resmi Başvuru Çağrısı ➔</a>
            </div>
        </div>
        """

    # 4. Podcastler
    podcasts_html = ""
    for p in podcasts:
        podcasts_html += f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px 14px;margin-bottom:8px;">
            <div style="color:#0f172a;font-weight:600;font-size:13px;">🎧 {p['title']}</div>
            <div style="color:#64748b;font-size:12px;margin:2px 0;">{p['topic']}</div>
            <div style="font-size:12px;margin-top:4px;">
                Yayın Kanalı: <b>{p['host']}</b> &nbsp;|&nbsp; 
                <a href="{p['url']}" style="color:#7c3aed;font-weight:600;text-decoration:none;">Bölümü Dinle ➔</a>
            </div>
        </div>
        """

    # 5. Hackathonlar
    hackathons_html = ""
    for h in hackathons:
        hackathons_html += f"""
        <li style="margin-bottom:8px;font-size:13px;color:#334155;line-height:1.4;">
            🏆 <b>{h['title']}</b> ({h['platform']}) &nbsp;•&nbsp; <span style="color:#059669;font-weight:600;">{h['status']}</span> 
            <a href="{h['url']}" style="color:#2563eb;margin-left:6px;text-decoration:none;font-weight:600;">Katılım Bağlantısı ➔</a>
        </li>
        """

    # 6. Haberler
    news_html = ""
    for n in news:
        news_html += f"""
        <li style="margin-bottom:8px;font-size:13px;color:#334155;line-height:1.4;">
            📰 <b>{n['title']}</b> <span style="color:#64748b;font-size:12px;">({n['source']})</span>
            <a href="{n['url']}" style="color:#2563eb;margin-left:6px;text-decoration:none;font-weight:600;">Haberi İncele ➔</a>
        </li>
        """

    # Kurumsal HTML Govdesi
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;background-color:#f1f5f9;margin:0;padding:24px;color:#0f172a;">
        <div style="max-width:720px;margin:0 auto;background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08);border:1px solid #cbd5e1;">
            
            <!-- Executive Header -->
            <div style="background:#0f172a;color:#ffffff;padding:24px 28px;border-bottom:3px solid #2563eb;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-size:11px;font-weight:700;letter-spacing:1.2px;color:#94a3b8;text-transform:uppercase;">JOBHUNT-AUTO SYSTEM</div>
                        <h1 style="margin:4px 0 0 0;font-size:20px;font-weight:700;color:#ffffff;letter-spacing:-0.3px;">Kariyer & Fırsat İstihbarat Raporu</h1>
                    </div>
                    <div style="text-align:right;">
                        <span style="background:#1e293b;color:#cbd5e1;padding:4px 10px;border-radius:4px;font-size:11px;font-weight:600;border:1px solid #334155;">{current_date_str}</span>
                    </div>
                </div>
            </div>

            <!-- Sistem Parametreleri ve Kapsam -->
            <div style="background:#f8fafc;padding:14px 28px;border-bottom:1px solid #e2e8f0;font-size:12px;color:#475569;line-height:1.6;">
                <div>🎯 <b>Hedef Yetenek Seti:</b> Bilişim Sistemleri, Python, AI/ML, Backend, C#, SQL, Veri Analizi</div>
                <div>📍 <b>Coğrafi Kapsam:</b> Sivas, Erzurum, Türkiye Geneli (Uzaktan / Hibrit) & Global Remote</div>
                <div>⚡ <b>Sistem Durumu:</b> Deterministik Çok Kaynaklı Veri Motoru Tarafından Doğrulandı</div>
            </div>

            <div style="padding:24px 28px;">
                
                <!-- 1. Is & Staj Firsatlari -->
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #0f172a;padding-bottom:6px;margin-bottom:14px;">
                    <h2 style="color:#0f172a;font-size:15px;font-weight:700;margin:0;text-transform:uppercase;letter-spacing:0.5px;">
                        💼 Doğrulanmış İş ve Staj Fırsatları
                    </h2>
                    <span style="font-size:12px;color:#64748b;font-weight:600;">{len(matched_jobs)} Aktif Pozisyon</span>
                </div>
                {jobs_html if jobs_html else "<p style='color:#64748b;font-size:13px;'>Kriterlere uygun yeni pozisyon bulunamadı.</p>"}

                <!-- 2. Bootcampler -->
                <div style="border-bottom:2px solid #0f172a;padding-bottom:6px;margin-top:28px;margin-bottom:14px;">
                    <h2 style="color:#0f172a;font-size:15px;font-weight:700;margin:0;text-transform:uppercase;letter-spacing:0.5px;">
                        🎓 Ücretsiz Eğitim Kampları & Bootcampler
                    </h2>
                </div>
                {camps_html}

                <!-- 3. AR-GE & TUBITAK -->
                <div style="border-bottom:2px solid #0f172a;padding-bottom:6px;margin-top:28px;margin-bottom:14px;">
                    <h2 style="color:#0f172a;font-size:15px;font-weight:700;margin:0;text-transform:uppercase;letter-spacing:0.5px;">
                        🔬 AR-GE Projeleri & TÜBİTAK Öğrenci Destekleri
                    </h2>
                </div>
                {rd_html}

                <!-- 4. Podcastler -->
                <div style="border-bottom:2px solid #0f172a;padding-bottom:6px;margin-top:28px;margin-bottom:14px;">
                    <h2 style="color:#0f172a;font-size:15px;font-weight:700;margin:0;text-transform:uppercase;letter-spacing:0.5px;">
                        🎧 Haftalık Geliştirici & Teknoloji Podcast'leri
                    </h2>
                </div>
                {podcasts_html}

                <!-- 5. Hackathonlar -->
                <div style="border-bottom:2px solid #0f172a;padding-bottom:6px;margin-top:28px;margin-bottom:14px;">
                    <h2 style="color:#0f172a;font-size:15px;font-weight:700;margin:0;text-transform:uppercase;letter-spacing:0.5px;">
                        🏆 Aktif Yarışma & Hackathon Platformları
                    </h2>
                </div>
                <ul style="padding-left:18px;margin:8px 0;">
                    {hackathons_html}
                </ul>

                <!-- 6. Haberler -->
                <div style="border-bottom:2px solid #0f172a;padding-bottom:6px;margin-top:28px;margin-bottom:14px;">
                    <h2 style="color:#0f172a;font-size:15px;font-weight:700;margin:0;text-transform:uppercase;letter-spacing:0.5px;">
                        📰 Güncel Teknoloji Gelişmeleri
                    </h2>
                </div>
                <ul style="padding-left:18px;margin:8px 0;">
                    {news_html}
                </ul>
            </div>

            <!-- Institutional Footer -->
            <div style="background:#f8fafc;padding:16px 28px;text-align:center;border-top:1px solid #e2e8f0;font-size:11px;color:#64748b;line-height:1.5;">
                Bu rapor <b>JobHunt-Auto Otonom Veri Motoru</b> tarafından taranmış, doğrulanmış ve derlenmiştir.<br>
                Sistem bildirimleri kurumsal yapılandırma kapsamında periyodik olarak iletilmektedir.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_email_newsletter(html_content, total_jobs_count):
    """SMTP uzerinden kurumsal basliklarla guvenli e-posta gonderir."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    user_email_to = os.getenv("USER_EMAIL_TO")

    if not smtp_user or not smtp_pass or not user_email_to:
        print("⚠️ E-Posta ayarlari eksik. SMTP_USER, SMTP_PASS ve USER_EMAIL_TO degiskenlerini kontrol edin.")
        return False

    current_date_str = datetime.datetime.now().strftime('%d.%m.%Y')
    print(f"📧 Rapor {user_email_to} adresine iletiliyor...")

    msg = MIMEMultipart("alternative")
    
    # Kurumsal ve sistem odakli gonderici basliklari
    msg["From"] = formataddr(("JobHunt-Auto Platform Intelligence", smtp_user))
    msg["To"] = user_email_to
    msg["Reply-To"] = "no-reply@jobhunt.auto"
    msg["Subject"] = f"JobHunt-Auto Raporu | {total_jobs_count} Doğrulanmış Pozisyon, Kamp & AR-GE Çağrısı ({current_date_str})"
    msg["X-Auto-Response-Suppress"] = "All"
    msg["X-Entity-Ref-ID"] = f"JOBHUNT-AUTO-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"

    msg.attach(MIMEText("Lütfen HTML destekleyen bir e-posta istemcisi kullanın.", "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print("✅ Kurumsal sistem raporu basariyla iletildi!")
        return True
    except Exception as e:
        print(f"❌ E-Posta iletim hatasi: {e}")
        return False
