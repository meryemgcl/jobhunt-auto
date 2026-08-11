from crewai import Task

class JobHuntTasks:
    def search_jobs_task(self, agent):
        return Task(
            description=(
                "İnternette (varsayılan: LinkedIn/Web) Meryem'in profiline (AI Engineer, Frontend, Python) uygun olan "
                "güncel ilanları ara. Aramalarında özellikle şu konumlara öncelik ver: Erzurum, Sivas, Kayseri ve UZAKTAN (Remote) çalışma imkanı sunan işler. "
                "Minimum 3 potansiyel ilan bul ve bunların açıklamalarını çıkar."
            ),
            expected_output='Ham iş ilanları listesi (Firma, Başlık, Açıklama, Link).',
            agent=agent
        )

    def evaluate_jobs_task(self, agent, cv_profile_json):
        return Task(
            description=(
                f"Scout tarafından getirilen ilanları şu profil ile karşılaştır: {cv_profile_json}\n"
                "Her ilan için 100 üzerinden bir Eşleşme Skoru (Match Score) belirle. Skoru 60'ın "
                "altında olanları ele. Kalanlar için 'Neden Uygun?' gerekçesini yaz."
            ),
            expected_output='Onaylanan ilanlar ve her biri için detaylı gerekçe raporu.',
            agent=agent
        )

    def draft_email_task(self, agent):
        return Task(
            description=(
                "Onaylanmış ilan raporunu al. 'Colleague' ve 'Human-Touch' yeteneklerini kullanarak, "
                "Meryem'e hitaben samimi, robotik olmayan ve teşvik edici bir günlük rapor e-postası yaz. "
                "Cümlelerinde yapay zeka klişelerinden uzak dur."
            ),
            expected_output='İnsan tarafından yazılmış gibi duran, profesyonel ama samimi E-Posta metni.',
            agent=agent
        )
