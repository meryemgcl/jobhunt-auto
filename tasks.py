from crewai import Task

class JobHuntTasks:
    def search_jobs_task(self, agent):
        return Task(
            description=(
                "İnternette (özellikle LinkedIn, GitHub, Kariyer.net vb. platformlarda) yazılım odaklı, "
                "bilgisayar programcılığı, yazılım geliştirme (Frontend/Backend/AI) üzerine güncel iş ilanlarını ara. "
                "Buna ek olarak, Türkiye genelindeki uzaktan (online) teknoloji eğitim programlarını, bootcamp'leri "
                "ve yazılım odaklı staj başvurularını (Remote veya hibrit) tespit et. "
                "Minimum 5 potansiyel fırsat bul ve bunların açıklamalarını, başvuru linkleriyle birlikte detaylıca listele."
            ),
            expected_output='Yazılım iş ilanları, eğitim programları ve staj fırsatlarından oluşan detaylı liste (Firma/Kurum, Başlık, Link).',
            agent=agent
        )

    def evaluate_jobs_task(self, agent, cv_profile_json):
        return Task(
            description=(
                f"Scout tarafından getirilen iş, staj ve eğitim fırsatlarını şu profil ile karşılaştır: {cv_profile_json}\n"
                "Her fırsat için 100 üzerinden bir Eşleşme Skoru (Match Score) belirle. Skoru 60'ın "
                "altında olanları ele. Kalanlar için 'Neden Uygun?' gerekçesini yaz."
            ),
            expected_output='Onaylanan fırsatlar ve her biri için detaylı gerekçe raporu.',
            agent=agent
        )

    def hackathon_search_task(self, agent):
        return Task(
            description=(
                "Devpost, Kaggle, Teknofest, Patika.dev gibi platformlarda ve genel internet aramalarında, "
                "Türkiye'deki veya global çaptaki güncel Hackathon ve kodlama yarışmalarını tespit et. "
                "Minimum 2 yarışma bul, tarihlerini ve başvuru linklerini ekle."
            ),
            expected_output='Güncel Hackathon ve kodlama yarışmaları listesi.',
            agent=agent
        )
        
    def opensource_search_task(self, agent):
        return Task(
            description=(
                "GitHub üzerinde 'good first issue' veya 'help wanted' etiketine sahip, "
                "yeni başlayanlara uygun Python, Frontend veya Yapay Zeka (AI) odaklı açık kaynak (open source) projelerini araştır. "
                "Minimum 2 proje/görev bul, linklerini ve ne yapılması gerektiğini kısaca listele."
            ),
            expected_output='Açık kaynak (Open Source) katkı fırsatları ve linkleri.',
            agent=agent
        )

    def freelance_search_task(self, agent):
        return Task(
            description=(
                "Upwork, Bionluk, Armut gibi platformlarda bilgisayar programcılığı, web geliştirme "
                "veya otomasyon alanlarında paylaşılan, 1-2 günde bitirilebilecek basit freelance (serbest) işleri araştır. "
                "Minimum 2 iş fırsatı bul, bütçelerini ve linklerini ekle."
            ),
            expected_output='Kısa süreli serbest çalışma (freelance) fırsatları ve linkleri.',
            agent=agent
        )

    def tech_news_task(self, agent):
        return Task(
            description=(
                "Medium, Dev.to, HackerNews gibi kaynaklardan veya genel teknoloji haber sitelerinden "
                "yapay zeka (AI) ve yazılım geliştirme alanındaki en sıcak ve trend 3 gelişmeyi/haberi bul. "
                "Her birini 1-2 cümleyle özetle."
            ),
            expected_output='Günlük yapay zeka ve yazılım teknolojileri gelişmeleri özeti.',
            agent=agent
        )

    def draft_email_task(self, agent):
        return Task(
            description=(
                "Tüm bu araştırmalardan elde edilen şu verileri al:\n"
                "1. Onaylanmış iş/staj/eğitim fırsatları raporu (Critic'ten gelen)\n"
                "2. Güncel Hackathon listesi (Scout'tan gelen)\n"
                "3. Açık kaynak projeleri fırsatları (Scout'tan gelen)\n"
                "4. Freelance iş fırsatları (Scout'tan gelen)\n"
                "5. Günlük teknoloji haberleri (Scout'tan gelen)\n\n"
                "'Colleague' ve 'Human-Touch' yeteneklerini kullanarak, Meryem'e hitaben tüm bu bilgileri "
                "harmanlayan çok kapsamlı, cesaretlendirici, motive edici bir 'Günlük Kariyer ve Gelişim Bülteni' hazırla. "
                "Bülten; net başlıklar, emojiler ve okuması kolay bir düzende olmalı."
            ),
            expected_output='İnsan tarafından yazılmış gibi duran, kapsamlı ve motive edici Günlük E-bülten metni.',
            agent=agent
        )
