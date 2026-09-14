# Security Policy

## Desteklenen Sürümler

| Sürüm | Güvenlik Güncellemeleri |
|-------|------------------------|
| 0.3.x | Aktif olarak destekleniyor |
| 0.2.x | Kritik düzeltmeler yalnızca |
| < 0.2 | Desteklenmiyor |

---

## Güvenlik Açığı Bildirimi

**Lütfen güvenlik açıklarını herkese açık GitHub Issue olarak açmayın.**

Bir güvenlik açığı keşfettiyseniz:

1. GitHub'ın [Private Vulnerability Reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) özelliğini kullanın.
2. Alternatif olarak, repo sahibine doğrudan mesaj gönderin.

Bildirilen açıklar **48 saat** içinde yanıtlanmaya çalışılır.

---

## Gizli Bilgi (Secret) Yönetimi

Bu proje şu gizli bilgileri kullanır:

| Değişken | Nerede Saklanmalı |
|----------|-------------------|
| `SMTP_USER` / `SMTP_PASS` | GitHub Actions Secrets veya `.env.local` (repo'ya commit edilmez) |
| `JOBHUNT_API_TOKEN` | GitHub Actions Secrets |
| API anahtarları (Gemini vb.) | GitHub Actions Secrets veya `.env.local` |

> [!CAUTION]
> `.env` dosyasını hiçbir zaman repo'ya commit etmeyin. `.gitignore`'un `.env`'i kapsadığından emin olun.

---

## Güvenli Geliştirme Kuralları

- Tüm harici URL'ler `services/url_utils.py::clean_url()` ile normalize edilir.
- Jinja2 şablonları `select_autoescape` ile XSS'e karşı koruma altındadır.
- HTTP istekleri `services/http_client.py` üzerinden timeout, retry ve User-Agent yönetimiyle yapılır.
- Firestore güvenlik kuralları şablon bölümünde tanımlanmıştır.
