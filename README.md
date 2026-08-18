# 🚀 JobHunt-Auto (AI Destekli Kariyer Asistanı)

JobHunt-Auto, iş arama sürecini tamamen otomatikleştiren, **CrewAI** tabanlı çoklu ajan (multi-agent) mimarisine sahip yapay zeka destekli kişisel kariyer asistanıdır. Her sabah saat 09:00 ve öğleden sonra 14:00'te uyanır, yeteneklerinize (CV'nize) uygun ilanları tarar, eler ve size e-posta ile bir "Günlük Bülten" yollar.

## 🌟 Özellikler

- **🤖 Çoklu Ajan Mimarisi (CrewAI):**
  - **Scout (Kıdemli İlan Araştırmacısı):** İnternetteki en taze iş, staj, eğitim ve freelance fırsatlarını kazar.
  - **Critic (Acımasız Eşleştirici):** Scout'un getirdiği ilanları kullanıcının CV'si ile kıyaslar, %60 uyumun altındakileri acımasızca eler.
  - **Colleague (İletişim Uzmanı):** Onaylanan ilanları, motivasyon dolu, emojili ve samimi bir iş arkadaşı e-postası formatına çevirir.
  
- **🧠 Kalıcı Hafıza (Memory) Sistemi:** 
  - Sistemin "Dün gönderdiği ilanı bugün tekrar göndermemesi" için özel bir `seen_jobs.json` hafıza dosyası vardır. Düzenli olarak GitHub'a commit edilerek hafızanın kalıcılığı sağlanır.
  
- **🎯 6 Farklı Boyutta Fırsat Taraması:**
  1. **İş/Staj İlanları:** LinkedIn, Kariyer vb. platformlardaki yazılım ilanları.
  2. **Eğitim/Bootcamp:** Güncel teknoloji kampları.
  3. **Hackathon:** Devpost, Kaggle ve Teknofest gibi yarışmalar.
  4. **Açık Kaynak (Open Source):** GitHub üzerindeki `good first issue` etiketli katkı fırsatları.
  5. **Freelance Fırsatlar:** Upwork, Bionluk gibi platformlardaki 1-2 günlük mikro işler.
  6. **Teknoloji Gündemi:** Sektördeki en sıcak ve trend 3 gelişme/haber.

- **⚡ Google Gemini 3.6 Flash:** En düşük gecikme ve sıfır çökme (503 High Demand önlemi) ile en güncel Google AI modeli entegrasyonu. (Langchain altyapısı ile desteklenmektedir.)

- **☁️ Otomatik Çalışma (GitHub Actions):** `.github/workflows/job_hunt.yml` dosyası sayesinde kod bulutta her gün günde 2 kez otomatik çalışır. Bilgisayarınızın açık kalmasına gerek yoktur!

---

## 🛠️ Kurulum ve Lokal Çalıştırma

Projeyi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin:

1. **Depoyu Klonlayın:**
   ```bash
   git clone https://github.com/meryemgcl/jobhunt-auto.git
   cd jobhunt-auto
   ```

2. **Gereksinimleri Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Çevre Değişkenlerini (Environment Variables) Ayarlayın:**
   Projeye ait `.env.example` dosyasının adını `.env` olarak değiştirin ve içindeki bilgileri kendinize göre doldurun:
   ```env
   GEMINI_API_KEY=sizin_api_anahtariniz
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=gonderici_mailiniz@gmail.com
   SMTP_PASS=google_uygulama_sifresi (16 hane)
   USER_EMAIL_TO=alici_mailiniz@gmail.com
   ```

4. **Sistemi Başlatın:**
   ```bash
   python main.py
   ```
   *Not: İşlem ortalama 1-2 dakika sürer. Bittiğinde terminalde "E-Posta başarıyla gönderildi" yazısını göreceksiniz.*

---

## 🏗️ Proje Mimarisi (Dosya Yapısı)

* `main.py`: Ajanları (Crew), görevleri (Tasks) ve hafızayı (Memory) birleştirip sistemi başlatan ana orkestrasyon dosyası.
* `agents.py`: Scout, Critic ve Colleague isimli yapay zeka ajanlarının sistem komutlarının (Prompt) barındığı yer.
* `tasks.py`: Ajanlara verilen 6 farklı veri çekme ve filtreleme görevinin bulunduğu dosya.
* `services/memory.py`: Okunan iş linklerini kaydeden, tekrarı engelleyen hafıza modülü.
* `seen_jobs.json`: Otomasyonun daha önce bulduğu fırsatların kayıtlı olduğu log dosyası.
* `.github/workflows/job_hunt.yml`: Kodun bulutta otomatik çalışmasını ve hafızayı kaydetmesini sağlayan CI/CD otomasyon dosyası.

---

## 🤝 Katkıda Bulunma

Bu proje açık kaynaklıdır. Projeye katkıda bulunmak (yeni ajanlar eklemek, WhatsApp entegrasyonu yapmak vb.) isterseniz, lütfen bir Pull Request (PR) açmaktan çekinmeyin!

1. Bu depoyu (repository) çatallayın (Fork).
2. Yeni bir dal (branch) oluşturun (`git checkout -b feature/yeni-ozellik`).
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`).
4. Dalınızı (branch) gönderin (`git push origin feature/yeni-ozellik`).
5. Bir Pull Request açın.

---

**Geliştiren:** [Meryem Güçlü] - Yapay zekanın sadece kod yazan değil, kariyer inşa eden bir asistan olabileceğine inanan vizyoner projeler serisi! 🚀
