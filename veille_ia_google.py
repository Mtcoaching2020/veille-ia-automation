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
        # Test GitHub Cloud (Secret JSON)
        creds_dict = json.loads(auth_data)
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        print("☁️ Connexion GitHub Cloud réussie.")
    except Exception:
        # Test Local (Fichier .json)
        if os.path.exists(auth_data):
            creds = Credentials.from_service_account_file(auth_data, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
            print(f"🏠 Connexion locale ({auth_data}) réussie.")
        else:
            print("❌ Erreur : Identifiants Google introuvables.")
            return None
    return gspread.authorize(creds)

def recuperer_news_rss():
    """Récupère les dernières actus via les flux RSS des sites de ta liste"""
    print("🌐 Récupération des flux RSS Tech (Liste personnalisée)...")
    flux_urls = [
        "https://www.lemondeinformatique.fr/flux-rss/thematique/intelligence-artificielle/rss.xml",
        "https://www.journaldunet.com/rss/it/intelligence-artificielle/",
        "https://www.presse-citron.net/tag/intelligence-artificielle/feed/",
        "https://www.usine-digitale.fr/ia/rss", # L'Usine Digitale - IA
        "https://www.zdnet.fr/feeds/rss/actualites/it-management-39000735q.htm", # ZDNet
        "https://www.silicon.fr/feed", # Silicon.fr
        "https://www.it-connect.fr/feed/", # IT Connect
        "https://intelligence-artificielle.com/feed/" # Site dédié IA
    ]
    
    articles_rss = []
    for url in flux_urls:
        try:
            feed = feedparser.parse(url)
            # On prend l'article le plus récent de chaque source pour varier au maximum
            if feed.entries:
                entry = feed.entries[0]
                articles_rss.append({
                    "titre": entry.title,
                    "lien": entry.link,
                    "source": "Flux RSS Tech"
                })
        except Exception as e:
            print(f"⚠️ Erreur RSS sur {url} : {e}")
            
    # On limite à 2-3 articles au total pour ne pas saturer Gemini d'un coup
    return articles_rss[:3]

def lancer_veille():
    print("🚀 Lancement de la veille...")
    gc = connexion_google_sheets()
    if not gc: return
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        sheet_id = "1KXGlAy0jf6kDU_tewvKO7CKlq-Ff1hC-NPriAvq-WIM"

    try:
        sheet = gc.open_by_key(sheet_id).worksheet("Veille IA & Business")
        print(f"🔗 Connecté à l'onglet : Veille IA & Business")
        
        # --- 1. COLLECTE DES NEWS (MULTI-SOURCES) ---
        news_a_traiter = []
        
        # Source A : Flux RSS
        articles_rss = recuperer_news_rss()
        news_a_traiter.extend(articles_rss)

        # Source B : Google Trends
        try:
            print("🔍 Recherche Google Trends...")
            pytrends = TrendReq(hl='fr-FR', tz=360)
            trends = pytrends.trending_searches(pn='france')[0].tolist()
            
            mots_cles_tech = ["IA", "AI", "Intelligence", "Tech", "Google", "Microsoft", "OpenAI", "Apple", "Nvidia"]
            for t in trends:
                if any(mot.lower() in t.lower() for mot in mots_cles_tech):
                    news_a_traiter.append({"titre": t, "lien": get_google_link(t), "source": "Google Trends"})
        except Exception as e:
            print(f"⚠️ Google Trends indisponible. Passage à la recherche alternative.")

        # Source C : Plan B "Aléatoire" (Si rien n'est trouvé)
        if not news_a_traiter:
            print("🎲 Utilisation du Plan B Dynamique (Recherche aléatoire)...")
            sujets_secours = ["LLM", "Chat GPT", "Actualité IA" , "Claude"]
            sujet_choisi = random.choice(sujets_secours)
            news_a_traiter.append({
                "titre": sujet_choisi, 
                "lien": get_google_link(sujet_choisi), 
                "source": "Recherche Secours"
            })

        # --- 2. FILTRAGE ET ANALYSE ---
        existing_links = sheet.col_values(6) # Colonne F (Liens)
        date_now = datetime.now().strftime("%d/%m/%Y %H:%M")

        for item in news_a_traiter:
            lien = item['lien']
            titre = item['titre']
            source = item['source']
            
            if lien in existing_links:
                print(f"⏭️ Doublon sauté : {titre}")
                continue

            print(f"✨ Analyse de : {titre} (via {source})")
            
            # Extraction et Analyse
            texte_article = extract_article_text(lien)
            input_ia = f"Sujet : {titre}. Contenu : {texte_article[:2500]}"
            resume_ia = analyser_avec_gemini(input_ia)

            # --- 3. AJOUT AU TABLEAU ---
            sheet.append_row([
                date_now, 
                source, 
                titre, 
                resume_ia, 
                "À publier", 
                lien
            ])
            print(f"✅ Ajouté au Sheets : {titre}")
            time.sleep(2) 

        print("✨ Mission terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur critique : {e}")

if __name__ == "__main__":
    lancer_veille()