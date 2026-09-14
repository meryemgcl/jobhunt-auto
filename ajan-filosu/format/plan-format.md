# Plan formatı
Dosya adı: plan/YYYY-AA-GG-plan.md. Yazıldıktan sonra DURULUR.

## Bölüm A · İşler
Tablo: # | iş | girdisi | çıktısı | YAZACAĞI dosyalar
"YAZACAĞI dosyalar" bu tablonun en önemli sütunu. Okuma saylmaz, yalnız yazma saylır.
İki işin bu sütunu kesişiyorsa aynı dalgaya konamazlar.
Belirsiz iş plana girmez, kullanıcıya sorulur.

## Bölüm B · Bağımlılık haritası
İki tür ayrı ayrı yazılır, karıştırılmaz.
Veri bağımlılığı:  1 -> 3   (3'ün girdisi 1'in çıktısı)
Yazma çakışması:  4 <-> 6  (ikisi de aynı dosyaya yazıyor)
Çakışma varsa hangisinin önce koşacağı ve sebebi yazılır.

## Bölüm C · Dalgalar
Tablo: dalga | işler | aynı anda mı | neden
Kurallar: bir dalgada en fazla 4 iş. Geri alınamaz işler kendi dalgasında ve SIRALI.
Bir dakikadan kısa işler birleştirilir, birleştirme yapıldıysa yazılır.

## Bölüm D · Paralelleştirilmeyenler ve nedeni
Tablo: iş | neden (veri bağımlılığı / yazma çakışması / geri alınamaz / çok küçük)
Bu bölüm boş kalmamalı; boşsa büyük ihtimalle bir çakışma kaçırılmıştır.

## Bölüm E · Tahmini kazanç
Tablo: hepsi sırayla | dalgalarla | kazanç
Kural: kazanç en uzun dalga zincirinden hesaplanır, iş sayısından değil. Dört iş paralel
koşuyorsa süre en uzun işin süresidir, dörtte biri değil. Her çalışan için kurulum
maliyeti vardır, tahmine onu da kat. Süreleri bilmiyorsan "bilinmiyor" yaz, uydurma.

## Bölüm F · Onay
Kullanıcı kontrol listesi: işler doğru anlaşılmış mı · YAZACAĞI sütunu eksiksiz mi ·
aynı dosyaya yazan iki iş aynı dalgada mı (olmamalı) · geri alınamaz iş paralel dalgaya
düşmüş mü (düşmemeli).
Onaydan sonra koş.
