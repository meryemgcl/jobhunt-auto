# JobHunt-Auto Roadmap & Tasks

Bu liste, production hardening ve mimari gelişim sürecindeki tamamlanan ve planlanan görevleri takip eder.

## ✅ Tamamlanan Özellikler

### Mimari & Motor
- [x] Ana deterministik motor (`main.py`) ve adapter tabanlı veri toplama mimarisi.
- [x] `ThreadPoolExecutor` ile paralel (eşzamanlı) adaptör tarama (Greenhouse, Lever, Ashby, Remotive, Arbeitnow, HackerNews).
- [x] Global exception handling ile beklenmeyen çökmelerin engellenmesi.
- [x] `run_id` tabanlı yapılandırılmış loglama ve gözlemlenebilirlik (`RUN_SUMMARY.md`).
- [x] Canonical URL temizleme ve UTM/tracking parametre deduplication mantığı.
- [x] 30 günlük TTL temizliği ile hafıza şişmesinin önlenmesi (`services/memory.py`).

### Puanlama & Eşleştirme (Matcher)
- [x] Context-aware hard negatives: Başlık/şirkette kesin eleme, açıklamada sadece yumuşak ceza (-15).
- [x] Dinamik eşik ve "Potansiyel Adaylar" fallback mekanizması (20-49 puan).
- [x] Konum normalizasyonu ve eş anlamlılar haritası (`LOCATION_SYNONYMS`).
- [x] Kullanıcı feedback loop öğrenmesi (`uygun`, `alakasız`, `başvurdum`).

### Güvenlik & Dayanıklılık
- [x] E-posta başlık injection (CRLF) saldırılarına karşı `_sanitize_header()` filtresi.
- [x] HTTP istemcisinde SSL doğrulama zorunluluğu (`JOBHUNT_HTTP_VERIFY_SSL`).
- [x] Güvensiz URL şemalarının (`javascript:`, `data:`, `file:`) tamamen engellenmesi.
- [x] Başlangıçta env varlık kontrolü (`_check_required_env_vars()`) ile hassas verilerin loglanmaması.
- [x] `.env`, `*.db`, `seen_jobs.json` dosyalarının versiyon kontrolünden izole edilmesi.

### Veri Katmanı & Analitik
- [x] SQLite WAL modu ve 32MB önbellek (`PRAGMA cache_size = -32000`).
- [x] PostgreSQL çift sürücü desteği (`psycopg3`) ve geçiş betiği (`scripts/migrate_sqlite_to_postgres.py`).
- [x] `Analytics` Data Lake sorgu katmanı (`services/analytics.py`) ve LIMIT/OFFSET sayfalama.
- [x] CLI Veri Keşif Aracı (`scripts/data_explorer.py`) ve CSV/JSON dışa aktarım desteği.

### Test & Kalite
- [x] 72 adet kapsamlı unit test (%100 başarı oranı).
- [x] Güvenlik, adaptör hata izolasyonu, analitik ve matcher testleri.
- [x] Ruff linter ve type hinting uyumluluğu.

---

## 📌 Gelecek Planlar (Backlog)

- [ ] FastAPI tabanlı yerel yönetim panosu / web arayüzü.
- [ ] Telegram / Discord bot bildirim kanalı entegrasyonu.
- [ ] Go fetcher mikroservisinin (`services/go-fetcher/`) Python motoruyla IPC üzerinden bağlanması.
