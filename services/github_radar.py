import requests

def fetch_good_first_issues():
    """
    GitHub REST API uzerinden Python ve AI odakli 'good first issue' ve 
    'help wanted' etiketine sahip acik kaynak firsatlarini ceker.
    """
    issues = []
    url = 'https://api.github.com/search/issues?q=label:%22good%20first%20issue%22+language:python+state:open&sort=updated&order=desc&per_page=3'
    headers = {
        'User-Agent': 'JobHunt-Auto-Radar',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            for item in r.json().get('items', [])[:3]:
                repo_name = "/".join(item.get('repository_url', '').split('/')[-2:])
                issues.append({
                    "title": item.get("title", ""),
                    "repo": repo_name,
                    "url": item.get("html_url", ""),
                    "comments": item.get("comments", 0),
                    "created_at": item.get("created_at", "")[:10]
                })
    except Exception as e:
        print(f"[GitHub Radar] API hatasi: {e}")
        
    # Standart ve garantili acik kaynak repo arama fallback baglantilari
    if not issues:
        issues = [
            {
                "title": "Python Açık Kaynak İyi Başlangıç Sorunları (Good First Issues)",
                "repo": "GitHub Community",
                "url": "https://github.com/topics/good-first-issue?l=python",
                "comments": "Aktif",
                "created_at": "Sürekli Güncel"
            },
            {
                "title": "HuggingFace Transformers Açık Katkı Görevleri",
                "repo": "huggingface/transformers",
                "url": "https://github.com/huggingface/transformers/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22",
                "comments": "Aktif",
                "created_at": "Sürekli Güncel"
            }
        ]
        
    return issues
