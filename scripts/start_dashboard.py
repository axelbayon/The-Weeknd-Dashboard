#!/usr/bin/env python3
"""
Script de lancement complet du dashboard The Weeknd.
1. Lance l'orchestrateur auto-refresh en arrière-plan
2. Lance un serveur HTTP local pour visualiser le dashboard
"""

import subprocess
import sys
import os
import threading
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
    
    # Étape 1 : Lancement orchestrateur en arrière-plan
    print("\nEtape 1/3 : Demarrage orchestrateur auto-refresh...")
    orchestrator_script = base_path / "scripts" / "auto_refresh.py"
    
    # Lancer l'orchestrateur dans un thread séparé
    def run_orchestrator():
        try:
            # Forcer l'encodage UTF-8
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            subprocess.run(
                [python_exe, str(orchestrator_script)],
                cwd=str(base_path),
                env=env
            )
        except Exception as e:
            print(f"Erreur orchestrateur: {e}")
    
    orchestrator_thread = threading.Thread(target=run_orchestrator, daemon=True)
    orchestrator_thread.start()
    print("OK Orchestrateur demarre en arriere-plan (refresh toutes les 10 min)\n")
    
    # Étape 2 : Premier scraping synchrone (pour avoir des données immédiatement)
    print("Etape 2/3 : Synchronisation initiale des donnees...")
    
    # Forcer l'encodage UTF-8 pour éviter les problèmes
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        # Scraper Songs
        result = subprocess.run(
            [python_exe, str(base_path / "scripts" / "scrape_kworb_songs.py")],
            cwd=str(base_path),
            env=env,
            capture_output=True
        )
        # Scraper Albums
        result = subprocess.run(
            [python_exe, str(base_path / "scripts" / "scrape_kworb_albums.py")],
            cwd=str(base_path),
            env=env,
            capture_output=True
        )
        print("OK Donnees initiales synchronisees!\n")
    except Exception as e:
        print(f"Avertissement sync initiale: {e}\n")
    
    # Étape 3 : Lancement du serveur
    print("Etape 3/3 : Lancement du serveur HTTP...")
    website_path = base_path / "Website"
    port = 8000
    
    print(f"\n{'=' * 60}")
    print(f"Dashboard accessible sur : http://localhost:{port}")
    print(f"{'=' * 60}")
    print(f"\nUtilisation de Python: {python_exe}")
    print("Auto-refresh actif : toutes les 10 minutes")
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
