# JobHunt-Auto TODO

Bu liste, mevcut production hardening çalışmasından sonraki geliştirme önceliklerini takip eder.

## Tamamlanan Temel Altyapı

- [x] Ana deterministik motor, API modu ve legacy/CrewAI bağımlılıklarını ayır.
- [x] `pyproject.toml` ile Python sürümü, ruff ve pytest ayarlarını sabitle.
- [x] `print` çıktılarını `logging` ve `run_id` tabanlı loglamaya taşı.
- [x] E-posta başarısızlığında hafızanın başarıyla güncellenmesini engelle.
- [x] HTML e-posta içeriğini Jinja2 şablonuna taşı ve external field autoescape uygula.
- [x] Canonical URL temizleme ve UTM/tracking parametresi temizliği ekle.
- [x] `seen_jobs.json` yapısını structured memory formatına geçir.
- [x] Adapter tabanlı kaynak toplama mimarisi ekle.
- [x] HTTP timeout, retry, backoff ve User-Agent yönetimini merkezileştir.
- [x] SQLite state, feedback, score history ve run summary tablolarını ekle.
- [x] Dockerfile, Docker Compose ve healthcheck altyapısını ekle.
- [x] CI hattına ruff, compileall, import smoke, pytest, healthcheck ve concurrency kilidi ekle.
- [x] `EXCLUDED_COMPANIES` ve `EXCLUDED_KEYWORDS` kara listelerini `config.py`'ye ekle; matcher'a entegre et.
- [x] `scripts/generate_static_dashboard.py` — SQLite üzerinden istatistik ve dashboard raporu üret.
- [x] E-posta şablonuna puan >= 85 için "YÜKSEK EŞLEŞME" etiketi ve "Ön Yazı Üret" butonu ekle.
- [x] `CHANGELOG.md` ve `SECURITY.md` ekle; `README.md` repo yapısını güncelle.

## P0 - Kritik Production Hazırlığı

- [ ] Gerçek SMTP, API token ve `DATABASE_URL` değerlerinin yalnızca GitHub Secrets veya deployment secret manager üzerinden geldiğini doğrula.
- [ ] GitHub Actions üzerinde manuel `workflow_dispatch` çalıştırması yaparak e-posta, dashboard ve state commit akışını uçtan uca test et.
- [ ] PostgreSQL backfill sonrası `seen_jobs.json` ve DB dedupe davranışını en az iki ardışık koşuda doğrula.
- [x] Kaynak adapter’ları için fixture tabanlı contract testlerini genişlet.
- [x] İş kaynaklarını Remotive, Arbeitnow, Hacker News Hiring, Greenhouse, Lever ve Ashby board'larıyla çeşitlendir; kaynak tarihi olan eski ilanları filtrele.
- [x] Tarihi bilinmeyen arama sonuçlarına bugünün tarihini atama; başvuru/dizin sonuçlarını doğrulanmış aktif fırsat gibi etiketleme.
- [x] Yerel CLI varsayılanını e-postasız ve state yazmayan HTML önizlemesi yap; e-posta gönderimini açık `--send` seçeneğine bağla.
- [x] Windows yerel kurulum betiği ekle; örnek SMTP kimlik bilgilerini boş tut ve mevcut `.env` dosyasını koru.
- [x] SMTP teslimat hatalarında aynı digest'i kalıcı outbox üzerinden yeniden dene; bekleyen digest çözülmeden yeni taramaları bastırma.
- [x] Doğrulanmamış statik podcast bağlantılarını kaldır; yarışma bağlantılarını etkin etkinlik değil, kaynak dizini olarak etiketle.
- [ ] SMTP başarısızlığı, API rate limit, network timeout ve bozuk JSON senaryoları için hata testleri ekle.
- [x] `JOBHUNT_API_TOKEN` zorunlu modunu production deployment dokümantasyonunda netleştir.
- [x] PostgreSQL destekli Docker image build senaryosunu CI içine al.
- [ ] `docker compose --profile api up` senaryosunu gerçek secret ve veritabanıyla release checklist içinde doğrula.

## P1 - Veri Modeli ve Matcher İyileştirmeleri

- [x] Aday profilini hard-coded mock yapıdan çıkarıp `profile.yaml` veya SQLite `candidate_profile` tablosuna taşı.
- [x] Matcher ağırlıklarını config dosyasından yönetilebilir hale getir.
- [ ] Feedback learning için keyword yaklaşımını etiket, kaynak, şirket ve lokasyon bazlı ayrı sinyallere böl.
- [ ] `alakasız` feedback’i için benzer ilanları düşüren fakat false negative riskini sınırlayan eşik sistemi ekle.
- [ ] Her opportunity için `status` geçişlerini netleştir: `seen`, `sent`, `fit`, `irrelevant`, `applied`, `archived`.
- [ ] Skor geçmişi üzerinden haftalık trend raporu üret.
- [x] Kaynak bazında ilan, şirket çeşitliliği, eşleşme, tarih ve doğrudan başvuru bağlantısı ölçümlerini çalıştırma özetine ekle.
- [ ] Kaynak güven puanını statik değer yerine birikmiş başarı oranı, hata oranı ve tazelik verisiyle dinamik hesapla.

## P2 - UX, Dashboard ve Operasyon

- [ ] `DASHBOARD.md` içine son run alarm özetlerini ve kaynak bazlı veri kalitesi metriklerini ekle.
- [ ] Basit bir web dashboard ekleyerek fırsatlara `uygun`, `alakasız`, `basvurdum` feedback butonları koy.
- [ ] API için OpenAPI örneklerini ve curl tariflerini genişlet.
- [ ] `RUN_SUMMARY.md` içeriğini günlük/haftalık karşılaştırmalı hale getir.
- [ ] n8n workflow dosyasını yeni `/feedback` ve `/health` endpoint’leriyle uyumlu örneklerle güncelle.
- [ ] E-posta template’i için mobil istemci görsel regresyon kontrolü ekle.

## P3 - Uzun Vadeli Özellikler

- [ ] Başvuru takip modülü ekle: başvuru tarihi, şirket, rol, durum, not ve takip tarihi.
- [ ] Takvim entegrasyonu veya reminder mekanizmasıyla takip tarihlerini otomatik hatırlat.
- [ ] LinkedIn, Kariyer.net, Youthall gibi kaynaklar için resmi API veya güvenli scraping stratejilerini değerlendirme dokümanı hazırla.
- [ ] Çoklu profil desteği ekle: farklı adaylar veya farklı kariyer hedefleri için ayrı matcher profilleri.
- [ ] Haftalık PDF/HTML kariyer performans raporu üret.
- [ ] Release versiyonlama, changelog ve container registry publish süreci ekle.

## Cross-AI Çalışma Notları

- [ ] Yeni AI aracıyla çalışırken `README.md` içindeki Cross-AI Development Guide bölümünü ilk context olarak paylaş.
- [ ] Her AI oturumundan önce aktif üretim yolunun `main.py` ve `services/` olduğunu belirt.
- [ ] AI’dan değişiklik isterken önce mevcut testleri çalıştırmasını, sonra scoped patch üretmesini iste.
- [ ] Legacy dosyaları production’a geri taşımadan önce açık bir migration planı oluştur.
- [ ] Her değişiklikten sonra kalite kapısını çalıştır: `ruff`, `compileall`, import smoke, `healthcheck`, `pytest`.
