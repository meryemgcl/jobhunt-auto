import requests
from bs4 import BeautifulSoup
import re

def scrape_url_text(url):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; JobHuntBot/1.0)'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        return text[:5000]
    except Exception as e:
        return 'Sayfa okunamadi: ' + str(e)
