import json
import os
import time
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
        
        # --- RÉCUPÉRATION DES TENDANCES ---
        trends = []
        try:
            print("🔍 Recherche Google Trends...")
            pytrends = TrendReq(hl='fr-FR', tz=360)
            pytrends.build_payload(["intelligence artificielle", "IA"], cat=0, timeframe='now 1-d', geo='FR')
            trends = pytrends.trending_searches(pn='france')[0].tolist()
        except Exception as e:
            print(f"⚠️ Google Trends indisponible (404/Limite). Utilisation du Plan B.")
            trends = ["Nouveautés Gemini AI 2026", "Évolution Agents IA"]

        trends = trends[:2] # On se limite à 2 news pour le test
        existing_links = sheet.col_values(6) # Colonne F (Liens)
        date_now = datetime.now().strftime("%d/%m/%Y %H:%M")

        for trend in trends:
            lien = get_google_link(trend)
            
            if lien in existing_links:
                print(f"⏭️ Doublon sauté : {trend}")
                continue

            # Extraction et Analyse
            texte_article = extract_article_text(lien)
            input_ia = f"Sujet : {trend}. Contenu : {texte_article[:2500]}"
            resume_ia = analyser_avec_gemini(input_ia)

            # --- AJOUT AU TABLEAU (Ordre exact de tes colonnes) ---
            # Date | Source | Titre | Résumé | Impact | Lien
            sheet.append_row([
                date_now, 
                "Google News", 
                trend, 
                resume_ia, 
                "À publier", 
                lien
            ])
            print(f"✅ Ajouté : {trend}")
            time.sleep(2)

        print("✨ Mission terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur critique : {e}")

if __name__ == "__main__":
    lancer_veille()