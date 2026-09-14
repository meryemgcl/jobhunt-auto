# Rapor formatı
Dosya adı: ciktilar/YYYY-AA-GG-rapor.md
Amaç: kullanıcı on ayrı klasör gezmesin, tek dosya okusun.

## Bölüm A · Özet
Tablo: koşulan iş | biten | yapılamayan | atlanan | dalga sayısı
Altına tek cümle: koşu başarılı mı, elle müdahale gerekiyor mu.

## Bölüm B · İş iş sonuç
Her iş için kısa blok: bitti / yapılamadı / atlandı.
- Ne üretti: hangi dosya, nerede.
- Not: tek satır. Takıldığı yer, eksik bıraktığı şey.
Kural: "bitti" yalnız SONUC.md gerçekten çıktı bildirdiyse yazılır. Dosya boşsa
"çıktı üretmedi" yazılır. Uydurma tamamlama yok.

## Bölüm C · Yapılamayanlar
Tablo: iş | ne oldu | sonraki adım
Atlanan işler hangi işe bağlı oldukları için atlandıkları yazılarak işaretlenir.

## Bölüm D · Gerçekleşen zamanlama
Tablo: dalga | işler | tahmin | gerçek
Altına: toplam gerçek süre, sırayla koşsaydı süre, gerçekleşen kazanç.
Kural: kazanç şişirilmez. Beklenenden az kazandırdıysa yazılır ve sebebi eklenir.

## Bölüm E · Çakışma kontrolü
Tablo: kendi klasörü dışına yazan çalışan | aynı dosyaya iki çalışanın yazması |
eksik SONUC.md
Bu bölüm boş geçilmez. İzolasyon bozulduysa raporun en üstüne uyarı yazılır, çünkü o
koşunun çıktısına güvenilemez.

## Bölüm F · Filo defteri girdisi
Bu koşudan çıkan tek satırlık ders, kopyalanmaya hazır yazılır.
Özellikle: paralel sanılıp aslında çakışan işler, tahmini çok yanlış çıkan işler.
Ders çıkmadıysa "bu koşudan ders çıkmadı" yazılır, uydurma ders yazılmaz.
