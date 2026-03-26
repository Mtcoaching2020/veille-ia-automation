import re
"""
google_search_cleaner.py

Ce module contient des fonctions de nettoyage des liens Google et d'extraction de texte simulée pour la démonstration d'un projet d'automatisation Python. 
Ce script est volontairement simplifié et à compléter selon vos besoins réels.
"""

from newspaper import Article

def get_google_link(query):
    import feedparser
    import urllib.parse
    from googlenewsdecoder import new_decoderv1 # Le décodeur magique
    
    query_encoded = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={query_encoded}&hl=fr&gl=FR&ceid=FR:fr"
    
    feed = feedparser.parse(rss_url)
    
    if feed.entries:
        encoded_url = feed.entries[0].link
        try:
            # On décode le lien CBMi... pour avoir le vrai site
            decoded_url = new_decoderv1(encoded_url, interval=1)
            if decoded_url.get("status"):
                return decoded_url["decoded_url"]
            return encoded_url # Retour secours
        except:
            return encoded_url
    return None

def extract_article_text(url):
    try:
        from newspaper import Article
        # On ajoute un 'User-Agent' pour simuler un vrai humain sur Chrome
        article = Article(url, browser_user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        return f"Erreur d'extraction : {e}"