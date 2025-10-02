#!/usr/bin/env python3
"""
Script de lancement complet du dashboard The Weeknd.
1. Scrape les données depuis Kworb
2. Lance un serveur HTTP local pour visualiser le dashboard
"""

import subprocess
import sys
import time
from pathlib import Path

def main():
    base_path = Path(__file__).parent.parent
    
    print("=" * 60)
    print("🎵 The Weeknd Dashboard - Lancement complet")
    print("=" * 60)
    
    # Étape 1 : Scraping des données
    print("\n📊 Étape 1/2 : Récupération des données depuis Kworb...")
    scraper_script = base_path / "scripts" / "scrape_kworb_songs.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(scraper_script)],
            cwd=str(base_path),
            check=True
        )
        print("✅ Données mises à jour avec succès!\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du scraping: {e}")
        print("Le serveur sera lancé avec les données existantes.\n")
    
    # Étape 2 : Lancement du serveur
    print("🌐 Étape 2/2 : Lancement du serveur HTTP...")
    website_path = base_path / "Website"
    port = 8000
    
    print(f"\n{'=' * 60}")
    print(f"✅ Dashboard accessible sur : http://localhost:{port}")
    print(f"{'=' * 60}")
    print("\n💡 Appuyez sur Ctrl+C pour arrêter le serveur\n")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "http.server", str(port)],
            cwd=str(website_path),
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Serveur arrêté. À bientôt!")
    except Exception as e:
        print(f"\n❌ Erreur lors du lancement du serveur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
