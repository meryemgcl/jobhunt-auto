# Changelog

Bu proje [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) formatını ve
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) kurallarını benimser.

---

## [Unreleased]

### Added
- `EXCLUDED_COMPANIES` ve `EXCLUDED_KEYWORDS` kara listeleri `config.py`'ye eklendi; kullanici tarafından doğrudan düzenlenebilir.
- `matcher.py` bu kara listeleri okuyor ve eşleşen ilanlara doğrudan 0 puan veriyor.
- `scripts/generate_static_dashboard.py`: SQLite üzerinden son N günün koşu istatistiklerini, skor dağılımını ve kaynak bazlı metrikleri hem terminale hem de `DASHBOARD_REPORT.md`'ye yazıyor.
- E-posta şablonuna puan >= 85 olan ilanlar için "YÜKSEK EŞLEŞME" etiketi ve koşullu "Ön Yazı Üret" butonu eklendi.
- `feature_flags` artık Jinja2 şablonuna iletiliyor; özellik bayraklarına template'ten erişilebiliyor.
- `CHANGELOG.md`, `SECURITY.md` ve `.github/ISSUE_TEMPLATE/` dosyaları oluşturuldu.

---

## [0.3.0] — 2026-08

### Added
- Firebase bağımlılığından tamamen kurtularak Firebase Firestore'dan SQLite tabanlı mimariye geçiş.
- `services/database.py`: `run_summaries`, `score_history`, `opportunities` ve `feedback` tablolarını yöneten merkezi SQLite servisi.
- `services/observability.py`: Koşu özetleri, kaynak alarmları ve günlük özet yazımı.
- `services/feedback.py`: Kullanıcı geri bildirim indexi ve keyword ağırlık öğrenimi.
- Adapter tabanlı kaynak toplama mimarisi (`services/adapters/`).
- Dockerfile, Docker Compose ve `healthcheck.py` altyapısı.
- CI hattına ruff, compileall, import smoke, pytest, healthcheck ve concurrency kilidi eklendi.

### Changed
- `print()` kullanımından `logging` + `run_id` tabanlı yapılandırılmış loglamaya geçiş.
- E-posta başarısızlığında hafıza güncellemesi artık engelleniyor.
- HTML e-posta içeriği Jinja2 şablonuna (`newsletter.html.j2`) taşındı, autoescape aktif.

---

## [0.2.0] — 2026-05

### Added
- Canonical URL temizleme ve UTM/tracking parametresi sıyırma (`services/url_utils.py`).
- `seen_jobs.json` yapısı structured memory formatına dönüştürüldü.
- HTTP timeout, retry, backoff ve User-Agent yönetimi merkezileştirildi (`services/http_client.py`).
- GitHub Good First Issue radarı (`services/github_radar.py`).
- Skill gap analizi (`services/analytics.py`).

### Changed
- CrewAI bağımlılığı `legacy/` klasörüne taşındı; ana motor tamamen deterministik hale getirildi.

---

## [0.1.0] — 2026-02

### Added
- İlk deterministik iş ilanı toplama ve puanlama motoru (`main.py`, `services/matcher.py`).
- Çok kaynaklı veri toplama: LinkedIn, Kariyer.net, Youthall, Techcareer.net, GitHub.
- Jinja2 tabanlı HTML e-posta bülteni.
- `pyproject.toml` ile paket yönetimi ve `ruff` + `pytest` entegrasyonu.
- Aday profili mock yapısı (`services/profile_analyzer/analyzer.py`).
