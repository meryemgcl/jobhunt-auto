<div align="center">

# 🎯 JobHunt-Auto

### Otonom Kariyer & Fırsat İstihbarat Platformu

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-72%20Passed%20(100%25)-22c55e.svg?style=for-the-badge&logo=pytest&logoColor=white)](./tests)
[![Database](https://img.shields.io/badge/Database-SQLite%20WAL%20%7C%20PostgreSQL-4169E1.svg?style=for-the-badge&logo=sqlite&logoColor=white)](./services/database.py)
[![Security](https://img.shields.io/badge/Security-Hardened%20%26%20CRLF%20Guarded-9333ea.svg?style=for-the-badge&logo=securityscorecard&logoColor=white)](./services/url_utils.py)
[![Architecture](https://img.shields.io/badge/Architecture-Concurrent%20Adapters-f59e0b.svg?style=for-the-badge)](./services/job_collector.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](./LICENSE)

<p align="center">
  <b>JobHunt-Auto</b>, global ve yerel platformlardaki yazılım pozisyonlarını eşzamanlı olarak toplayan, aday profiline göre bağlamsal (context-aware) olarak puanlayan, tekrarları eleyen ve doğrudan gelen kutunuza kurumsal SaaS kalitesinde bülten ileten <b>deterministik kariyer otomasyon motorudur</b>.
</p>

[Özellikler](#-öne-çıkan-özellikler) •
[Mimari](#-sistem-mimarisi) •
[Hızlı Başlangıç](#-hızlı-başlangıç) •
[Veri Keşif Aracı (CLI)](#-veri-keşif-ve-analitik-cli) •
[Güvenlik](#-güvenlik-ve-dayanıklılık) •
[Testler](#-test-ve-kalite)

</div>

---

## ⚡ Öne Çıkan Özellikler

- 🚀 **Eşzamanlı (Concurrent) Adaptör Taraması:** `ThreadPoolExecutor` altyapısıyla Greenhouse, Ashby, Lever, Remotive, Arbeitnow ve HackerNews platformlarından **saniyeler içinde 300+ ilan** toplanır. Bir adaptörün çökmesi diğerlerini asla etkilemez.
- 🎯 **Bağlamsal (Context-Aware) Puanlama Motoru:**
  - **Negatif Kelime Ayrımı:** *"Senior"* veya *"Manager"* gibi elenmesi gereken kelimeler başlık/şirket alanında geçerse puanı sıfırlar; açıklama alanında geçerse sadece yumuşak ceza (-15 puan) uygulayarak adayı haksız yere elemez.
  - **Potansiyel Adaylar (Fallback):** Eşiği (55 puan) geçen ilan bulunamazsa, adayın motivasyonunu korumak ve piyasa nabzını ölçmek için 20–49 puan arasındaki en iyi 3 pozisyon bültene eklenir.
  - **Konum Normalizasyonu:** `Turkey`, `Türkiye (Remote)`, `Uzaktan` gibi varyasyonlar otomatik olarak tekilleştirilir.
- 📬 **SaaS Standardında HTML Bülten:** Tablo tabanlı, mobil uyumlu, renk kodlu uygunluk skorları ve kurumsal gradient başlıklarla donatılmış Jinja2 şablonu.
- 💾 **Çift Sürücülü Veri Katmanı:** Yerel geliştirmede **SQLite (WAL modu + 32MB bellek önbelleği)**, bulut/CI ortamında **PostgreSQL (`psycopg3`)** desteği.
- 📊 **Dahili Veri Keşif Aracı (Data Lake CLI):** Tüm taranan ilanları, koşu başarı oranlarını ve puan geçmişini terminalden anında sorgulama ve CSV/JSON formatında dışa aktarma imkanı.
- 🛡️ **Güvenlik Odaklı Mimari:** E-posta başlık injection (CRLF) saldırılarına karşı `_sanitize_header()`, SSL doğrulaması ve zararlı şemaların (`javascript:`, `data:`) engellenmesi.

---

## 🏗️ Sistem Mimarisi

```mermaid
flowchart TD
    subgraph DataCollection["1. Eşzamanlı Veri Toplama"]
        direction TB
        G[Greenhouse API]
        A[Ashby HQ]
        L[Lever.co]
        R[Remotive API]
        AN[Arbeitnow]
        HN[HackerNews Hiring]
        GH[GitHub Good First Issues]
    end

    subgraph CoreEngine["2. İşleme & Puanlama Motoru"]
        DEDUP[MD5 Deduplication & 30-Day TTL]
        NORM[Konum & Rol Normalizasyonu]
        MATCHER["Context-Aware Matcher\n(Tech + Role + Location + Feedback)"]
        SKILLGAP[Piyasa Beceri Açığı Analizi]
    end

    subgraph Persistence["3. Veri & Durum Yönetimi"]
        SQLITE[(SQLite WAL Mode)]
        PG[(PostgreSQL Production)]
        OUTBOX[Outbox Queue & Retry Engine]
    end

    subgraph Notification["4. Güvenli Dağıtım & Arayüz"]
        JINJA[Jinja2 Kurumsal Bülten Şablonu]
        SANITIZE[CRLF Header Sanitizer & SSL Guard]
        SMTP[Google SMTP / Relay]
        CLI[Data Explorer CLI]
    end

    DataCollection --> DEDUP
    DEDUP --> NORM
    NORM --> MATCHER
    MATCHER --> SKILLGAP
    SKILLGAP --> Persistence
    Persistence --> OUTBOX
    OUTBOX --> JINJA
    JINJA --> SANITIZE
    SANITIZE --> SMTP
    Persistence --> CLI
```

---

## 🚀 Hızlı Başlangıç

### 1. Depoyu Klonlayın ve Ortamı Hazırlayın

```bash
git clone https://github.com/meryemgcl/jobhunt-auto.git
cd jobhunt-auto

# Sanal ortam oluşturun ve aktif edin
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Ortam Değişkenlerini Tanımlayın (`.env`)

Depo kökünde bir `.env` dosyası oluşturun (`.env.example` dosyasını referans alabilirsiniz):

```env
# E-Posta Gönderici Bilgileri (Google Uygulama Şifresi)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ornek@gmail.com
SMTP_PASS=abcd efgh ijkl mnop

# Alıcı E-Posta
USER_EMAIL_TO=ornek+otomasyon@gmail.com

# İsteğe Bağlı: PostgreSQL Bağlantısı (Tanımlanmazsa yerel SQLite kullanılır)
# DATABASE_URL=postgresql://user:pass@localhost:5432/jobhunt
```

### 3. Profilinizi Özelleştirin (`profile.yaml`)

Yeteneklerinizi, hedeflenen pozisyonları ve tercih ettiğiniz çalışma lokasyonlarını `profile.yaml` üzerinden dilediğiniz gibi güncelleyin:

```yaml
name: "Adınız Soyadınız"
title: "Yazılım Geliştirici"
experience_level: "Junior/Intern"

core_skills:
  - "Python"
  - "FastAPI"
  - "SQL"
  - "Docker"

preferred_locations:
  - "Remote"
  - "İstanbul"
  - "Türkiye Geneli"
```

### 4. Çalıştırın

```bash
# Güvenli Önizleme Modu (E-posta göndermez, veritabanını kirletmez, HTML önizleme üretir)
python main.py --dry-run

# Canlı Gönderim Modu (Taramayı yapar, veritabanını günceller ve e-posta iletir)
python main.py --send
```

---

## 📊 Veri Keşif ve Analitik CLI

`scripts/data_explorer.py` aracı sayesinde sistem tarafından toplanan tüm fırsatları doğrudan terminalinizden analiz edebilir ve raporlayabilirsiniz:

```bash
# 1. Genel Sistem Özeti (Toplam taranan, eşleşen, başarı oranı)
python scripts/data_explorer.py report

# 2. Eşleşen Pozisyonları Filtreleme
python scripts/data_explorer.py jobs --status sent --min-score 60

# 3. Son Koşuların Geçmişi
python scripts/data_explorer.py runs --last 10

# 4. En Çok İlan Açan Şirketlerin Analizi
python scripts/data_explorer.py companies

# 5. Tüm Veritabanını CSV veya JSON Olarak Dışa Aktarma
python scripts/data_explorer.py export-csv --output exports/ilanlar.csv
python scripts/data_explorer.py export-json --output exports/ilanlar.json
```

---

## 🛡️ Güvenlik ve Dayanıklılık

| Güvenlik Katmanı | Uygulanan Önlem | İlgili Dosya |
|------------------|-----------------|--------------|
| **CRLF Header Injection** | `To`, `From` ve `Subject` alanlarındaki tüm satır sonu ve tab karakterleri filtrelenir. | `services/notification_and_meta/notifier.py` |
| **Strict SSL Verification** | Dış API ve kaynak isteklerinde varsayılan olarak SSL doğrulaması zorunludur. | `services/http_client.py` |
| **URL Sanitization** | `javascript:`, `data:`, `file:` gibi potansiyel zararlı URL şemaları elenir. | `services/url_utils.py` |
| **Zero-Secret Logging** | API anahtarları veya SMTP parolaları hata veya bilgi loglarına asla yazdırılmaz. | `main.py` |
| **Git İzolasyonu** | `.env`, SQLite veritabanı dosyaları ve geçmiş hafıza dosyaları `.gitignore` ile korunur. | `.gitignore` |

---

## 🧪 Test ve Kalite

Proje, kapsamlı bir test süiti ile korunmaktadır. Testleri çalıştırmak için:

```bash
pytest -q --tb=short
```

```text
........................................................................ [100%]
72 passed in 5.61s
```

- **`test_security.py`**: CRLF injection, zararlı URL filtreleme ve SSL yapılandırma testleri.
- **`test_job_collector.py`**: Adaptör çökme izolasyonu ve hata sayaçları testleri.
- **`test_analytics.py`**: Boş veritabanı uç durumları, limit/offset sayfalama ve metrik testleri.
- **`test_matcher.py`**: Bağlamsal puanlama, yumuşak ceza ve fallback mekanizması testleri.

---

## 📂 Dizin Yapısı

```text
├── config.py                 # Puan ağırlıkları, kara listeler ve adaptör ayarları
├── profile.yaml              # Kullanıcı profil ve hedef yetenek konfigürasyonu
├── main.py                   # Deterministik ana motor ve CLI giriş noktası
├── Makefile                  # Geliştirici kısayolları ve otomasyon hedefleri
├── scripts/
│   ├── data_explorer.py      # Veri gölü ve analitik CLI aracı
│   └── migrate_sqlite_to_postgres.py  # SQLite -> Postgres geçiş aracı
├── services/
│   ├── adapters/             # Greenhouse, Lever, Ashby, Remotive vb. veri adaptörleri
│   ├── analytics.py          # Veri gölü sorgu katmanı ve piyasa analiz fonksiyonları
│   ├── database.py           # SQLite WAL & PostgreSQL bağlantı ve migration motoru
│   ├── job_collector.py      # ThreadPoolExecutor tabanlı paralel veri toplayıcı
│   ├── matcher.py            # Bağlamsal uygunluk ve puanlama motoru
│   ├── memory.py             # 30 günlük TTL ve dedup hafıza yöneticisi
│   └── notification_and_meta/# Jinja2 HTML bülten şablonu ve güvenli SMTP istemcisi
└── tests/                    # 72 adet kapsamlı unit ve entegrasyon testi
```

---

## 📄 Lisans

Bu proje [MIT Lisansı](./LICENSE) kapsamında açık kaynak olarak paylaşılmaktadır.
