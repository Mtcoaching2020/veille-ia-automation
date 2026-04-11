import json
import os
import time
import random
import feedparser
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from pytrends.request import TrendReq
from dotenv import load_dotenv
import google.generativeai as genai
from google_search_cleaner import get_google_link, extract_article_text

# Charger les variables d'environnement
load_dotenv()

def analyser_avec_gemini(texte_brut):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Clé API Gemini manquante."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-flash-latest')
        
        prompt = f"""
        Résume cet article en une phrase courte et pro : {texte_brut[:2000]}
        Idée TikTok : [Concept rapide]
        
        Instructions :
        1. Si le texte est vide ou contient des erreurs, réponds : "Contenu non pertinent".
        2. Sinon, fais un résumé très court (1 phrase) de l'actualité IA.
        3. Ajoute une ligne "Idée TikTok :" avec un concept de vidéo rapide.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur IA : {e}"

def connexion_google_sheets():
    auth_data = os.getenv('GOOGLE_SERVICE_ACCOUNT')
    if auth_data is None:
        auth_data = "google_sheets_credentials.json"

    try:
        creds_dict = json.loads(auth_data)
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        print("☁️ Connexion GitHub Cloud réussie.")
    except Exception:
        if os.path.exists(auth_data):
            creds = Credentials.from_service_account_file(auth_data, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
            print(f"🏠 Connexion locale ({auth_data}) réussie.")
        else:
            print("❌ Erreur : Identifiants Google introuvables.")
            return None
    return gspread.authorize(creds)

def recuperer_news_rss():
    """Récupère les 5 dernières actus de 12 sources françaises références"""
    print("🌐 Scan des 12 sources françaises (5 articles par flux)...")
    flux_urls = [
        "https://www.lemondeinformatique.fr/flux-rss/thematique/intelligence-artificielle/rss.xml",
        "https://www.journaldunet.com/rss/it/intelligence-artificielle/",
        "https://www.presse-citron.net/tag/intelligence-artificielle/feed/",
        "https://www.usine-digitale.fr/ia/rss",
        "https://www.zdnet.fr/feeds/rss/actualites/it-management-39000735q.htm",
        "https://www.silicon.fr/feed",
        "https://www.actuia.com/flux/",
        "https://siecledigital.fr/intelligence-artificielle/feed/",
        "https://www.numerama.com/t/intelligence-artificielle/feed/",
        "https://www.futura-sciences.com/tech/intelligence-artificielle/rss.xml",
        "https://intelligence-artificielle.com/feed/",
        "https://www.it-connect.fr/feed/"
    ]
    
    articles_rss = []
    for url in flux_urls:
        try:
            feed = feedparser.parse(url)
            # ICI : On boucle sur les 5 derniers articles de chaque site
            for entry in feed.entries[:5]:
                articles_rss.append({
                    "titre": entry.title,
                    "lien": entry.link,
                    "source": "Flux RSS Tech"
                })
        except Exception as e:
            print(f"⚠️ Erreur RSS sur {url}")
            
    random.shuffle(articles_rss)
    return articles_rss

def lancer_veille():
    print("🚀 Lancement de la veille V3 (Sources élargies)...")
    gc = connexion_google_sheets()
    if not gc: return
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "1KXGlAy0jf6kDU_tewvKO7CKlq-Ff1hC-NPriAvq-WIM")

    try:
        sheet = gc.open_by_key(sheet_id).worksheet("Veille IA & Business")
        print(f"🔗 Connecté à l'onglet : Veille IA & Business")
        
        # 1. Collecte
        news_a_traiter = recuperer_news_rss()

        # 2. Paramètres de contrôle (Test bridé à 3 ajouts)
        MAX_DEPOT = 3 
        articles_ajoutes = 0
        existing_links = sheet.col_values(6) 
        date_now = datetime.now().strftime("%d/%m/%Y %H:%M")

        # 3. Filtrage et Analyse
        for item in news_a_traiter:
            if articles_ajoutes >= MAX_DEPOT:
                print(f"🛑 Quota de {MAX_DEPOT} articles atteint.")
                break

            lien = item['lien']
            titre = item['titre']
            
            if lien in existing_links:
                continue

            print(f"✨ Analyse de : {titre}")
            
            texte_article = extract_article_text(lien)
            input_ia = f"Sujet : {titre}. Contenu : {texte_article[:2500]}"
            resume_ia = analyser_avec_gemini(input_ia)

            # 4. Ajout au tableau
            sheet.append_row([date_now, item['source'], titre, resume_ia, "À publier", lien])
            print(f"✅ Ajouté au Sheets : {titre}")
            articles_ajoutes += 1
            time.sleep(2) 

        print(f"✨ Mission terminée ! {articles_ajoutes} nouveaux articles ajoutés.")
        
    except Exception as e:
        print(f"❌ Erreur critique : {e}")

if __name__ == "__main__":
    lancer_veille()