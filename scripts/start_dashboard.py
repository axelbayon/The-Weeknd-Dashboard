#!/usr/bin/env python3
"""
Script de lancement complet du dashboard The Weeknd.
1. Scrape les données depuis Kworb
2. Lance un serveur HTTP local pour visualiser le dashboard
"""

import subprocess
import sys
import os
from pathlib import Path

def get_python_executable():
    """Détermine le bon exécutable Python à utiliser."""
    # Essayer d'abord l'exécutable actuel
    current_python = sys.executable
    
    # Sur Windows, essayer les chemins courants de Python
    if os.name == 'nt':
        possible_pythons = [
            current_python,
            r"C:\Users\axelb\AppData\Local\Programs\Python\Python314\python.exe",
            r"C:\Python314\python.exe",
            r"C:\Python313\python.exe",
            "python",
            "python3"
        ]
        
        for py_path in possible_pythons:
            try:
                # Tester si cet exécutable a les dépendances requises
                result = subprocess.run(
                    [py_path, "-c", "import requests, bs4"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return py_path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
    
    return current_python

def main():
    base_path = Path(__file__).parent.parent
    python_exe = get_python_executable()
    
    print("=" * 60)
    print("The Weeknd Dashboard - Lancement complet")
    print("=" * 60)
    
    # Étape 1 : Scraping des données
    print("\nEtape 1/3 : Recuperation des chansons depuis Kworb...")
    scraper_songs = base_path / "scripts" / "scrape_kworb_songs.py"
    
    try:
        result = subprocess.run(
            [python_exe, str(scraper_songs)],
            cwd=str(base_path),
            check=True
        )
        print("OK Chansons mises a jour!\n")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du scraping songs: {e}\n")
    
    # Étape 2 : Scraping des albums
    print("Etape 2/3 : Recuperation des albums depuis Kworb...")
    scraper_albums = base_path / "scripts" / "scrape_kworb_albums.py"
    
    try:
        result = subprocess.run(
            [python_exe, str(scraper_albums)],
            cwd=str(base_path),
            check=True
        )
        print("OK Albums mis a jour!\n")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du scraping albums: {e}\n")
    
    # Étape 3 : Lancement du serveur
    print("Etape 3/3 : Lancement du serveur HTTP...")
    website_path = base_path / "Website"
    port = 8000
    
    print(f"\n{'=' * 60}")
    print(f"Dashboard accessible sur : http://localhost:{port}")
    print(f"{'=' * 60}")
    print(f"\nUtilisation de Python: {python_exe}")
    print("Appuyez sur Ctrl+C pour arreter le serveur\n")
    
    try:
        subprocess.run(
            [python_exe, "-m", "http.server", str(port)],
            cwd=str(website_path),
            check=True
        )
    except KeyboardInterrupt:
        print("\n\nServeur arrete. A bientot!")
    except Exception as e:
        print(f"\nErreur lors du lancement du serveur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
