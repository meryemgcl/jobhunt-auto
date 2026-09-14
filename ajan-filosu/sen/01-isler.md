# Sen · yapılacaklar

Bu koşuda `jobhunt-auto` sisteminin mevcut adapter yapısını ve veritabanını bozmadan, projenin otomasyon ve analiz gücünü artıracak eklentiler planlanmıştır.

## İşler
- `config.py` dosyasına "EXCLUDED_COMPANIES" (Kara listeye alınan şirketler) ve "EXCLUDED_KEYWORDS" (İstenmeyen anahtar kelimeler, örn: "Blockchain", "DevOps") için yeni konfigürasyon değişkenleri ekle.
- `main.py` veya puanlama servisi (scoring) içinde bu yeni konfigürasyon değişkenlerini okuyarak, istenmeyen şirket veya kelimeleri içeren ilanların puanını doğrudan 0 (sıfır) yapacak eleme (filtering) mantığını yaz.
- `jobhunt.db` (SQLite) veritabanını okuyan ve Jinja2 kullanarak son 7 günün istatistiklerini (bulunan ilan sayısı, ortalama puanlar) gösteren basit bir `scripts/generate_static_dashboard.py` oluştur.
- E-posta şablonuna (HTML/Jinja2), puanı 85'in üzerinde olan "Yüksek Eşleşmeli" ilanlar için "Hızlı Başvuru" (Quick Apply) veya "Ön Yazı Üret" (Generate Cover Letter) butonu ekle.

## Bu koşuda dokunulmayacaklar (opsiyonel)
- `tests/` klasörü (Mevcut testleri bozmamak için)
- `seen_jobs.json` (Hafıza yapısını bozmamak için)
- `infrastructure/` ve `Dockerfile` (Deployment süreçlerine dokunma)

## Geri alınamaz işler (opsiyonel ama önemli)
- `jobhunt.db` tablosuna migration/alter table yapmak (Eğer gerekirse sıralı yapılmalı, paralel olmamalı).

## Filo defteri
-
