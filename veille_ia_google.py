import json
from pytrends.request import TrendReq
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
from google_search_cleaner import get_google_link, extract_article_text
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Charger les variables d'environnement
load_dotenv()
def analyser_avec_gemini(texte_brut):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Clé API Gemini manquante."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-flash-latest')

    prompt = f"""
    Résume cet article en une phrase courte et pro : {texte_brut[:2000]}
    Idée TikTok : [Concept rapide]
    
    Instructions :
    1. Si le texte contient uniquement des messages de cookies ou d'erreur, réponds : "Contenu non pertinent (bloqué par cookies)".
    2. Sinon, fais un résumé très court (1 phrase) de l'actualité IA.
    3. Ajoute une ligne "Idée TikTok :" avec un concept de vidéo rapide.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur IA : {e}"
def lancer_veille():
    print("🚀 La fonction lancer_veille() a bien été appelée.")
    keywords = [
        "intelligence artificielle",
        "entrepreneuriat et IA",
        "startup IA",
        "innovation IA",
        "business intelligence artificielle"
    ]

    # 📊 Connexion à Google Trends
    pytrends = TrendReq(hl='fr-FR', tz=360)
    trends = []

    for keyword in keywords:
        try:
            suggestions = pytrends.suggestions(keyword)
            for sugg in suggestions:
                titre = sugg['title']
                if titre not in trends:
                    trends.append(titre)
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Erreur avec le mot-clé {keyword} :", e)

    trends = trends[:2]

    # 🔄 Connexion à Google Sheets (Version Hybride : Local + GitHub)
    if trends:
        SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")
        # On essaie de récupérer le contenu du JSON directement (pour GitHub)
        creds_json_string = os.getenv("GOOGLE_CREDENTIALS_JSON")
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        try:
            if creds_json_string:
                # Mode GitHub : On transforme le texte du secret en dictionnaire JSON
                creds_info = json.loads(creds_json_string)
                creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
            else:
                # Mode Local : On utilise ton fichier comme avant
                CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
                creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
            
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Veille IA & Business")
        except Exception as e:
            print(f"❌ Erreur de connexion Google Sheets : {e}")
            return

        existing_links = sheet.col_values(6)
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ajout_count = 0
        doublon_count = 0

        for trend in trends:
            lien = get_google_link(trend)

            if lien in existing_links:
                doublon_count += 1
                continue

            # Extraction du texte
            texte_article = extract_article_text(lien)
            
            # --- ZONE DE PRÉPARATION POUR L'IA ACTIVÉE ---
            # On baisse la limite à 50 caractères pour laisser une chance à Gemini
            if "Erreur" not in texte_article and len(texte_article) > 50:
                print(f"🧠 Analyse par Gemini pour : {trend}...")
                # On combine le titre de la tendance et le texte trouvé pour aider l'IA
                input_ia = f"Sujet : {trend}. Contenu extrait : {texte_article[:3000]}"
                resume_ia = analyser_avec_gemini(input_ia) 
            else:
                resume_ia = f"Lien trouvé mais contenu protégé. Sujet : {trend}"
            # ---------------------------------------------

            sheet.append_row([
                date_now,
                "Intelligence artificielle",
                trend,
                resume_ia,  # Ici, on envoie le résultat de Gemini !
                "Post TikTok suggéré", 
                lien,
                "À publier"
            ])
            print(f"✅ Ajouté : {trend}")
            ajout_count += 1

        print(f"🔁 Résumé : {ajout_count} ajoutés, {doublon_count} doublons.")
    else: 
        print("⚠️ Aucune tendance trouvée.")