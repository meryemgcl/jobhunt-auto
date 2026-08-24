from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

def get_cv_similarity_score(job_description, cv_text):
    """TF-IDF kullanarak CV ile is tanimi arasindaki benzerlik skorunu hesaplar (0-100)."""
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = vectorizer.fit_transform([cv_text, job_description])
        score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100
        return round(score, 2)
    except Exception:
        return 0.0
