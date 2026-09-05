## 📌 Tanım (Description)
<!-- Yapılan değişikliklerin kısa ve öz bir özeti -->

## 🎯 Motivasyon ve Bağlam (Motivation & Context)
<!-- Bu PR hangi sorunu çözüyor veya hangi özelliği ekliyor? -->

## 🧪 Nasıl Test Edildi? (Testing)
- [ ] Yerel ortamda `python main.py` ile çalıştırılarak test edildi.
- [ ] E-posta şablonu ve veri toplayıcılar doğrulandı.
- [ ] `ruff check .` başarıyla çalıştı.
- [ ] `python -m compileall main.py api.py config.py services legacy tests` başarıyla çalıştı.
- [ ] Import smoke test başarıyla çalıştı.
- [ ] `python healthcheck.py` başarıyla çalıştı.
- [ ] `pytest` başarıyla çalıştı.
- [ ] Docker/Compose etkisi varsa build veya deployment senaryosu kontrol edildi.

## 📋 Değişiklik Türü (Type of Change)
- [ ] 🐛 Hata düzeltmesi (Bug fix)
- [ ] ✨ Yeni özellik (New feature)
- [ ] ⚡ Performans / Mimari iyileştirmesi (Refactoring / Performance)
- [ ] 📝 Dokümantasyon güncellemesi (Documentation)

## ✅ Kontrol Listesi (Checklist)
- [ ] Kod projenin kod stiline uygundur.
- [ ] `requirements.txt` ve bağımlılıklar güncellenmiştir.
- [ ] Dış kaynaklı HTML/e-posta alanları sanitize edilmiştir.
- [ ] SQLite state, `seen_jobs.json` ve dashboard dosyaları tutarlı kalacak şekilde ele alınmıştır.
- [ ] Production kodu ile legacy/prototip kodu karıştırılmamıştır.
