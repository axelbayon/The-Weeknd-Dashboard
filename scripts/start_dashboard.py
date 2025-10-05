#!/usr/bin/env python3
"""
Script de lancement du dashboard The Weeknd.

PIPELINE DE DÉMARRAGE:
1. Démarre l'orchestrateur en arrière-plan (auto-refresh toutes les 5 min)
   - Le premier cycle démarre immédiatement
   - Affiche un message quand le dashboard est prêt
2. Lance le serveur HTTP pour visualiser le dashboard

L'orchestrateur gère automatiquement :
- Scraping Kworb (Songs + Albums)
- Génération des vues courantes (data/songs.json, data/albums.json)
- Enrichissement Spotify (covers, album_name)
- Rotation des snapshots historiques (J, J-1, J-2)
- Mise à jour meta.json (dates, stats, covers_revision)
"""

import subprocess
import sys
import os
import threading
import time
import json
from pathlib import Path


def wait_for_first_cycle(base_path: Path, timeout: int = 120):
    """
    Attend que le premier cycle soit terminé en surveillant meta.json.
    Retourne True si succès, False si timeout.
    """
    meta_path = base_path / "data" / "meta.json"
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        try:
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                
                status = meta.get("last_sync_status")
                
                # Nouveau statut détecté
                if status != last_status:
                    last_status = status
                    if status == "ok":
                        return True
                    elif status == "error":
                        print("│ ⚠️  Premier cycle terminé avec des erreurs")
                        return True
        except Exception:
            pass
        
        time.sleep(2)  # Vérifier toutes les 2 secondes
    
    print("│ ⚠️  Timeout: Premier cycle toujours en cours")
    return False

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
    
    print("\n" + "=" * 70)
    print(" " * 15 + "THE WEEKND DASHBOARD - DÉMARRAGE")
    print("=" * 70)
    print(f"\n📍 Répertoire : {base_path}")
    print(f"🐍 Python      : {python_exe}")
    print(f"🔄 Refresh     : Toutes les 5 minutes (Prompt 8.9)")
    print(f"🌐 URL locale  : http://localhost:8000/Website/")
    print("=" * 70)
    
    # ========================================================================
    # ÉTAPE 1 : Démarrage orchestrateur (pipeline automatique)
    # ========================================================================
    print("\n[ÉTAPE 1/2] 🚀 Lancement du pipeline d'actualisation...")
    print("│")
    print("│ Le pipeline s'exécute toutes les 5 minutes")
    print("│ (détails affichés ci-dessous)")
    print("│")
    
    orchestrator_script = base_path / "scripts" / "auto_refresh.py"
    
    # Lancer l'orchestrateur dans un thread daemon
    def run_orchestrator():
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            subprocess.run(
                [python_exe, str(orchestrator_script)],
                cwd=str(base_path),
                env=env
            )
        except Exception as e:
            print(f"❌ Erreur orchestrateur: {e}")
    
    orchestrator_thread = threading.Thread(target=run_orchestrator, daemon=True)
    orchestrator_thread.start()
    
    # Attendre un court instant pour permettre à l'orchestrateur de démarrer
    time.sleep(1)
    
    print("├─ ✅ Orchestrateur démarré en arrière-plan")
    print("│")
    
    # Attendre la fin du premier cycle
    success = wait_for_first_cycle(base_path, timeout=120)
    
    # ========================================================================
    # ÉTAPE 2 : Lancement serveur HTTP (APRÈS le premier cycle)
    # ========================================================================
    print("\n[ÉTAPE 2/2] 🌐 Lancement serveur HTTP...")
    print("│")
    
    server_path = base_path
    port = 8000
    
    print("├─ ✅ Serveur prêt !")
    print("│")
    print("=" * 70)
    print(" " * 20 + "🎉 DASHBOARD ACCESSIBLE")
    print("=" * 70)
    print(f"\n🔗 Ouvrez votre navigateur : http://localhost:{port}/Website/")
    print("\n💡 INFOS UTILES:")
    print("   • Données actualisées : Prêtes à consulter")
    print("   • Refresh auto        : Toutes les 5 minutes (vérification Kworb)")
    print("   • Covers Spotify      : Enrichies automatiquement à chaque cycle")
    print("   • Badges de rang      : Éphémères (J vs J-1 uniquement)")
    print("\n⌨️  Appuyez sur Ctrl+C pour arrêter le serveur")
    print("=" * 70 + "\n")
    
    try:
        subprocess.run(
            [python_exe, "-m", "http.server", str(port)],
            cwd=str(server_path),
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print(" " * 25 + "⏹️  ARRÊT DU SERVEUR")
        print("=" * 70)
        print("\n✅ Serveur HTTP arrêté proprement")
        print("⚠️  L'orchestrateur continue en arrière-plan (processus daemon)")
        print("\n👋 À bientôt !\n")
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        print("💡 Vérifiez que le port 8000 n'est pas déjà utilisé")
        sys.exit(1)

if __name__ == "__main__":
    main()
