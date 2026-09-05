import logging

from services.adapters import GitHubIssuesAdapter, StaticOpportunityAdapter


logger = logging.getLogger(__name__)

def fetch_good_first_issues():
    """
    GitHub REST API uzerinden Python ve AI odakli 'good first issue' ve 
    'help wanted' etiketine sahip acik kaynak firsatlarini ceker.
    """
    issues = GitHubIssuesAdapter().fetch()

    if not issues:
        logger.info("GitHub API sonuc vermedi; curated fallback baglantilari kullaniliyor.")
        issues = StaticOpportunityAdapter(
            [
                {
                    "title": "Python Açık Kaynak İyi Başlangıç Sorunları (Good First Issues)",
                    "repo": "GitHub Community",
                    "url": "https://github.com/topics/good-first-issue?l=python",
                    "comments": "Aktif",
                    "created_at": "Sürekli Güncel",
                    "source_reliability": 75,
                },
                {
                    "title": "HuggingFace Transformers Açık Katkı Görevleri",
                    "repo": "huggingface/transformers",
                    "url": "https://github.com/huggingface/transformers/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22",
                    "comments": "Aktif",
                    "created_at": "Sürekli Güncel",
                    "source_reliability": 80,
                },
            ],
            category="open_source",
            source_name="GitHub Fallback",
        ).fetch()

    return issues
