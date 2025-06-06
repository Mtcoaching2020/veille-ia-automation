# Veille IA Automation 🚀

Ce projet a été réalisé dans le cadre de mon apprentissage accéléré en Python et de ma découverte de l'architecture d'un projet Python.  
L'objectif est d'explorer l'impact de l'intelligence artificielle (IA) dans les automatisations complexes, notamment dans la veille d'actualités et la génération de prompts.

## Objectif pédagogique

🔎 Comprendre :
- Comment structurer un projet Python modulaire et évolutif.
- Comment l'IA peut être intégrée dans un processus d'automatisation pour la veille d'actualités.
- Comment identifier et limiter les risques de biais lors de l'extraction d'actualités via l'IA.

## Contexte métier

Dans le secteur tertiaire, la veille d'actualités change de dimension grâce à l'injection d'IA dans les automatisations.  
Ce projet explore comment l'IA structure et automatise ce processus, en particulier au niveau :
- Des instructions envoyées à l'IA.
- De l'évaluation du risque de biais dans l'extraction d'informations.

## Structure du projet

- `main.py` : Script principal qui orchestre l'automatisation.
- `veille_ia_google.py` : Module qui gère l'extraction des tendances IA.
- `google_search_cleaner.py` : Module complémentaire pour nettoyer les liens Google.
- `README.md` : Documentation du projet.

## Utilisation

1. Configurez vos identifiants Google Sheets dans `google_sheets_credentials.json`.
2. Exécutez le projet avec :
   ```bash
   python main.py
