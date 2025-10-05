#!/usr/bin/env python3
"""
Orchestrateur auto-refresh pour The Weeknd Dashboard.
Exécute périodiquement le pipeline : scrape Songs/Albums, régénère vues, met à jour meta.json.
Intervalle par défaut : 5 minutes (300 secondes) - Prompt 8.9.
"""

import json
import os
import random
import subprocess
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Configuration
DEFAULT_REFRESH_INTERVAL = 300  # Prompt 8.9: 5 minutes (changé de 600)
JITTER_SECONDS = 15  # ±15 secondes
LOCK_FILE = ".sync.lock"


class OrchestrationLock:
    """Gestion du verrou anti-chevauchement."""
    
    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
    
    def acquire(self) -> bool:
        """Tente d'acquérir le verrou. Retourne True si succès."""
        if self.lock_path.exists():
            # Vérifier si le lock est vieux (>15 min = processus mort)
            lock_age = time.time() - self.lock_path.stat().st_mtime
            if lock_age > 900:  # 15 minutes
                print("⚠️  Lock ancien détecté, nettoyage...")
                self.release()
            else:
                return False
        
        try:
            self.lock_path.touch()
            return True
        except Exception as e:
            print(f"❌ Erreur création lock: {e}")
            return False
    
    def release(self):
        """Libère le verrou."""
        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
        except Exception as e:
            print(f"⚠️  Erreur suppression lock: {e}")


def get_python_executable() -> str:
    """Détermine le bon exécutable Python avec dépendances."""
    current_python = sys.executable
    
    if os.name == 'nt':
        possible_pythons = [
            current_python,
            r"C:\Users\axelb\AppData\Local\Programs\Python\Python314\python.exe",
            r"C:\Python314\python.exe",
            "python"
        ]
        
        for py_path in possible_pythons:
            try:
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


def run_script(script_path: Path, python_exe: str, base_path: Path, timeout: int = 120) -> Tuple[bool, Optional[str]]:
    """
    Exécute un script Python.
    Retourne (succès, message_erreur).
    """
    try:
        # Forcer l'encodage UTF-8 pour éviter les problèmes avec les emojis
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONLEGACYWINDOWSSTDIO'] = '0'  # Désactive le mode legacy sur Windows
        
        # Sur Windows, utiliser creationflags pour éviter les erreurs de threads
        kwargs = {
            'cwd': str(base_path),
            'capture_output': True,
            'text': True,
            'encoding': 'utf-8',
            'errors': 'ignore',  # Ignorer les erreurs d'encodage au lieu de crash
            'timeout': timeout,
            'env': env
        }
        
        # Ajouter flag Windows pour créer sans fenêtre console
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        
        result = subprocess.run(
            [python_exe, str(script_path)],
            **kwargs
        )
        
        if result.returncode == 0:
            return True, None
        else:
            error_msg = result.stderr[:200] if result.stderr else "Erreur inconnue"
            return False, error_msg
    except subprocess.TimeoutExpired:
        return False, f"Timeout (>{timeout}s)"
    except Exception as e:
        return False, str(e)[:200]


def update_meta_status(base_path: Path, status: str, error: Optional[str] = None):
    """
    Met à jour meta.json avec le statut de synchronisation.
    """
    meta_path = base_path / "data" / "meta.json"
    
    try:
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        else:
            meta = {}
        
        meta["last_sync_status"] = status
        meta["last_sync_local_iso"] = datetime.now().isoformat()
        
        if error:
            meta["last_error"] = error
        elif "last_error" in meta:
            del meta["last_error"]
        
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    
    except Exception as e:
        print(f"⚠️  Erreur mise à jour meta.json: {e}")


def rotate_snapshots(base_path: Path, keep_count: int = 3):
    """
    Maintient un minimum de snapshots et purge les plus anciens.
    Garde au minimum keep_count dates (par défaut 3 pour J, J-1, J-2).
    """
    for snapshot_type in ["songs", "albums"]:
        history_path = base_path / "data" / "history" / snapshot_type
        
        if not history_path.exists():
            continue
        
        # Lister tous les snapshots
        snapshots = sorted(history_path.glob("*.json"), reverse=True)
        
        # Garder les keep_count plus récents, supprimer le reste
        if len(snapshots) > keep_count:
            for old_snapshot in snapshots[keep_count:]:
                try:
                    old_snapshot.unlink()
                    print(f"🗑️  Snapshot purgé : {old_snapshot.name}")
                except Exception as e:
                    print(f"⚠️  Erreur purge {old_snapshot.name}: {e}")


def run_pipeline(base_path: Path, python_exe: str, cycle_number: int = 1) -> bool:
    """
    Exécute le pipeline complet de synchronisation.
    
    Étapes :
    1. Scrape Songs     : Récupère données Kworb → Crée snapshot J → Régénère songs.json
    2. Scrape Albums    : Récupère données Kworb → Crée snapshot J → Régénère albums.json
    3. Enrichissement   : Ajoute cover_url Spotify dans songs.json et albums.json
    
    Note: La rotation des snapshots (J, J-1, J-2) est gérée automatiquement 
          par les scrapers via date_manager.py (basée sur kworb_day).
    
    Args:
        base_path: Racine du projet
        python_exe: Chemin de l'exécutable Python
        cycle_number: Numéro du cycle (pour affichage)
    
    Retourne True si succès complet.
    """
    print("\n" + "═" * 70)
    print(f"{'':^70}")
    print(f"🔄 CYCLE #{cycle_number} — {datetime.now().strftime('%H:%M:%S')}".center(70))
    print(f"{'':^70}")
    print("═" * 70)
    
    all_success = True
    error_messages = []
    
    # Étape 1 : Scrape Songs
    print("\n┌────────────────────────────────────────────────────────────────────┐")
    print("│ [1/3] 📊 SCRAPING SONGS                                            │")
    print("│                                                                    │")
    print("│ • Récupère données depuis Kworb                                    │")
    print("│ • Crée snapshot journalier (data/history/songs/YYYY-MM-DD.json)    │")
    print("│ • Régénère data/songs.json avec calculs (delta, badges)            │")
    print("└────────────────────────────────────────────────────────────────────┘")
    success, error = run_script(
        base_path / "scripts" / "scrape_kworb_songs.py",
        python_exe,
        base_path
    )
    if success:
        print("│ ✅ Songs scraped avec succès")
    else:
        print(f"│ ❌ Erreur: {error}")
        all_success = False
        error_messages.append(f"Songs: {error}")
    
    # Étape 2 : Scrape Albums
    print("\n┌────────────────────────────────────────────────────────────────────┐")
    print("│ [2/3] 💿 SCRAPING ALBUMS                                           │")
    print("│                                                                    │")
    print("│ • Récupère données depuis Kworb                                    │")
    print("│ • Crée snapshot journalier (data/history/albums/YYYY-MM-DD.json)   │")
    print("│ • Régénère data/albums.json avec calculs (delta, badges)           │")
    print("└────────────────────────────────────────────────────────────────────┘")
    success, error = run_script(
        base_path / "scripts" / "scrape_kworb_albums.py",
        python_exe,
        base_path
    )
    if success:
        print("│ ✅ Albums scraped avec succès")
    else:
        print(f"│ ❌ Erreur: {error}")
        all_success = False
        error_messages.append(f"Albums: {error}")
    
    # Étape 3 : Enrichissement covers Spotify
    print("\n┌────────────────────────────────────────────────────────────────────┐")
    print("│ [3/3] 🎨 ENRICHISSEMENT SPOTIFY                                    │")
    print("│                                                                    │")
    print("│ • Lit songs.json et albums.json                                    │")
    print("│ • Recherche tracks/albums manquants sur Spotify API                │")
    print("│ • Ajoute cover_url + album_name dans les fichiers JSON             │")
    print("│ • Incrémente covers_revision dans meta.json                        │")
    print("└────────────────────────────────────────────────────────────────────┘")
    success, error = run_script(
        base_path / "scripts" / "enrich_covers.py",
        python_exe,
        base_path,
        timeout=300  # 5 minutes pour l'enrichissement Spotify
    )
    if success:
        print("│ ✅ Covers enrichies avec succès")
    else:
        print(f"│ ⚠️  Avertissement: {error} (non-bloquant)")
        # Ne pas bloquer le pipeline si l'enrichissement échoue
    
    # Footer avec info rotation
    print("\n┌────────────────────────────────────────────────────────────────────┐")
    print("│ 🔄 ROTATION SNAPSHOTS                                              │")
    print("│                                                                    │")
    print("│ Gérée automatiquement par les scrapers via date_manager.py         │")
    print("│ • Maintient 3 jours : J (aujourd'hui), J-1, J-2                    │")
    print("│ • Rotation basée sur kworb_day (changement UTC 00:00)              │")
    print("└────────────────────────────────────────────────────────────────────┘")
    print("│ ✅ Rotation automatique active")
    
    # Mise à jour du statut dans meta.json
    if all_success:
        update_meta_status(base_path, "ok")
        print("\n" + "═" * 70)
        print(f"{'✅ CYCLE #' + str(cycle_number) + ' TERMINÉ — Succès complet':^70}")
        print("═" * 70)
    else:
        error_summary = "; ".join(error_messages[:2])  # Max 2 erreurs
        update_meta_status(base_path, "error", error_summary)
        print("\n" + "═" * 70)
        print(f"{'⚠️  CYCLE #' + str(cycle_number) + ' TERMINÉ — Erreurs partielles':^70}")
        print("═" * 70)
    
    return all_success


def main():
    """Point d'entrée principal de l'orchestrateur."""
    parser = argparse.ArgumentParser(description="Orchestrateur auto-refresh Dashboard")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Exécute une seule itération puis s'arrête"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Intervalle en secondes (override REFRESH_INTERVAL_SECONDS)"
    )
    
    args = parser.parse_args()
    
    # Configuration
    base_path = Path(__file__).parent.parent
    lock_path = base_path / "data" / LOCK_FILE
    python_exe = get_python_executable()
    
    # Déterminer l'intervalle
    interval = args.interval
    if interval is None:
        interval = int(os.getenv("REFRESH_INTERVAL_SECONDS", DEFAULT_REFRESH_INTERVAL))
    
    print("=" * 60)
    print("🎵 The Weeknd Dashboard — Orchestrateur Auto-Refresh")
    print("=" * 60)
    print(f"Mode: {'ONCE' if args.once else 'CONTINU'}")
    print(f"Intervalle: {interval}s ({interval/60:.1f} min)")
    print(f"Python: {python_exe}")
    print(f"Lock file: {lock_path}")
    print("=" * 60)
    
    lock = OrchestrationLock(lock_path)
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            # Tenter d'acquérir le verrou
            if not lock.acquire():
                print(f"\n⏭️  Itération {iteration} SKIPPED — Pipeline déjà en cours (lock actif)")
                if args.once:
                    break
                time.sleep(30)  # Attendre 30s avant de réessayer
                continue
            
            try:
                # Ajouter jitter aléatoire (±15s)
                jitter = random.uniform(-JITTER_SECONDS, JITTER_SECONDS)
                if jitter > 0:
                    print(f"\n⏱️  Jitter: +{jitter:.1f}s")
                    time.sleep(jitter)
                
                # Exécuter le pipeline
                run_pipeline(base_path, python_exe, cycle_number=iteration)
                
            finally:
                # Toujours libérer le verrou
                lock.release()
            
            # Mode --once : arrêter après une itération
            if args.once:
                print("\n✅ Mode --once : arrêt après 1 itération")
                break
            
            # Attendre l'intervalle avant la prochaine exécution
            next_run = datetime.fromtimestamp(time.time() + interval)
            print(f"\n{'═' * 70}")
            print(f"{'⏰ PROCHAIN CYCLE':^70}")
            print(f"{'═' * 70}")
            print(f"📅 Date: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️  Dans: {interval}s ({interval/60:.0f} minutes)")
            print(f"{'═' * 70}\n")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Arrêt demandé (Ctrl+C)")
        lock.release()
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Erreur critique orchestrateur: {e}")
        lock.release()
        sys.exit(1)


if __name__ == "__main__":
    main()
