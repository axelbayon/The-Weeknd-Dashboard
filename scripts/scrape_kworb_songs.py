#!/usr/bin/env python3
"""
Scraper Kworb pour les chansons de The Weeknd.
Génère un snapshot journalier et régénère data/songs.json avec calculs.
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Dépendances manquantes. Installez-les avec:")
    print("   pip install requests beautifulsoup4")
    sys.exit(1)


# Configuration
KWORB_SONGS_URL = "https://kworb.net/spotify/artist/1Xyo4u8uXC1ZmMpatF05PJ_songs.html"
USER_AGENT = "The-Weeknd-Dashboard/1.0 (Educational Project; Python Scraper)"
THROTTLE_SECONDS = 1.0
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


def normalize_key(title: str, album: str) -> str:
    """
    Normalise une clé d'alignement inter-jours.
    
    Règles :
    - lowercasing
    - trim
    - suppression ponctuation
    - "feat./with/x/& (...)" retirés
    """
    def clean(text: str) -> str:
        # Lowercase et trim
        text = text.lower().strip()
        
        # Retirer les patterns de featuring
        patterns = [
            " feat.", " feat ", " featuring ", " ft.", " ft ",
            " with ", " x ", " & ", " and "
        ]
        for pattern in patterns:
            if pattern in text:
                text = text.split(pattern)[0]
        
        # Retirer parenthèses et leur contenu
        if "(" in text:
            text = text.split("(")[0].strip()
        
        # Retirer ponctuation
        punctuation = ".,;:!?'\"-"
        for char in punctuation:
            text = text.replace(char, "")
        
        return text.strip()
    
    norm_title = clean(title)
    norm_album = clean(album)
    
    return f"kworb:{norm_title}@{norm_album}"


def detect_role(title: str) -> str:
    """
    Détecte le rôle de The Weeknd sur un titre.
    
    Heuristique simple :
    - Si "The Weeknd" apparaît en premier (ou seul) → "lead"
    - Si "feat.", "with", "x", "&" avant "The Weeknd" → "feat"
    """
    title_lower = title.lower()
    
    # Patterns indiquant un featuring
    feat_patterns = ["feat.", "feat ", "ft.", "ft ", "with ", " x ", " & "]
    
    for pattern in feat_patterns:
        if pattern in title_lower:
            # Vérifier si The Weeknd est après le pattern
            pattern_pos = title_lower.find(pattern)
            weeknd_pos = title_lower.find("the weeknd")
            
            if weeknd_pos > pattern_pos:
                return "feat"
    
    # Par défaut, considérer comme lead
    return "lead"


def clean_number(text: str) -> int:
    """
    Nettoie et convertit un nombre avec séparateurs (virgules, espaces).
    
    Exemples :
    - "4,290,300,000" → 4290300000
    - "5 300 000" → 5300000
    """
    if not text:
        return 0
    
    # Retirer tous les caractères non numériques sauf le point décimal
    cleaned = re.sub(r'[^\d.]', '', text)
    
    try:
        return int(float(cleaned))
    except ValueError:
        return 0


def parse_kworb_date(date_str: str) -> datetime:
    """
    Parse une date Kworb (format variable, généralement "YYYY-MM-DD" ou timestamp).
    Retourne un datetime UTC.
    """
    # Essayer différents formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    
    # Si aucun format ne fonctionne, utiliser la date actuelle
    print(f"⚠️  Impossible de parser la date '{date_str}', utilisation de la date actuelle")
    return datetime.now(timezone.utc)


def scrape_kworb_songs(url: str, retries: int = MAX_RETRIES) -> Tuple[List[Dict], datetime]:
    """
    Scrape la page Kworb Songs et retourne les données brutes.
    
    Returns:
        Tuple[List[Dict], datetime]: (liste des chansons, timestamp de mise à jour)
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }
    
    for attempt in range(retries):
        try:
            print(f"🌐 Récupération des données depuis Kworb (tentative {attempt + 1}/{retries})...")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Throttle
            time.sleep(THROTTLE_SECONDS)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver la table des chansons (la deuxième table avec class 'sortable')
            tables = soup.find_all('table')
            table = None
            for t in tables:
                if 'sortable' in t.get('class', []):
                    table = t
                    break
            
            if not table:
                raise ValueError("Table de chansons non trouvée sur la page")
            
            rows = table.find_all('tr')[1:]  # Skip header
            
            if not rows:
                raise ValueError("Aucune ligne de données trouvée dans la table")
            
            songs = []
            last_update_kworb = datetime.now(timezone.utc)  # Par défaut
            
            for i, row in enumerate(rows, start=1):
                cols = row.find_all('td')
                
                # Structure Kworb : [Title, Streams Total, Daily]
                if len(cols) < 3:
                    continue
                
                # Extraction des données
                rank = i
                title = cols[0].get_text(strip=True)
                streams_total_text = cols[1].get_text(strip=True)
                streams_daily_text = cols[2].get_text(strip=True)
                
                # Pas d'info album sur Kworb Songs, on met "Unknown" par défaut
                # (sera résolu plus tard via Spotify API)
                album = "Unknown"
                
                # Nettoyage et typage
                streams_total = clean_number(streams_total_text)
                streams_daily = clean_number(streams_daily_text)
                
                # Détection du rôle
                role = detect_role(title)
                
                # Génération de la clé (avec rank unique pour éviter collisions sans album)
                # Note : sera mis à jour quand on aura les données Spotify avec vrais albums
                song_id = f"kworb:{normalize_key(title, 'temp').replace('kworb:', '').replace('@temp', '')}:rank{rank}"
                
                song = {
                    "id": song_id,
                    "rank": rank,
                    "title": title,
                    "album": album,
                    "role": role,
                    "streams_total": streams_total,
                    "streams_daily": streams_daily
                }
                
                songs.append(song)
            
            print(f"✅ {len(songs)} chansons extraites avec succès")
            return songs, last_update_kworb
            
        except requests.RequestException as e:
            print(f"❌ Erreur réseau (tentative {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                wait_time = RETRY_BACKOFF ** attempt
                print(f"⏳ Nouvelle tentative dans {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            print(f"❌ Erreur lors du scraping: {e}")
            raise


def create_snapshot(songs: List[Dict], last_update_kworb: datetime, base_path: Path) -> str:
    """
    Crée un snapshot journalier dans data/history/songs/.
    
    Returns:
        str: La date spotify_data_date (YYYY-MM-DD)
    """
    # Calculer spotify_data_date = last_update_kworb - 1 jour
    spotify_data_date = (last_update_kworb - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Enrichir chaque chanson avec les timestamps
    snapshot_songs = []
    for song in songs:
        snapshot_song = {
            **song,
            "last_update_kworb": last_update_kworb.isoformat(),
            "spotify_data_date": spotify_data_date
        }
        snapshot_songs.append(snapshot_song)
    
    # Écrire le snapshot
    snapshot_path = base_path / "data" / "history" / "songs" / f"{spotify_data_date}.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_songs, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Snapshot créé : {snapshot_path}")
    print(f"   Date des données Spotify : {spotify_data_date}")
    
    return spotify_data_date


def update_meta(spotify_data_date: str, last_update_kworb: datetime, base_path: Path):
    """
    Met à jour data/meta.json avec les nouvelles informations.
    """
    meta_path = base_path / "data" / "meta.json"
    
    # Charger meta.json existant
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {"history": {}}
    
    # Récupérer les dates disponibles dans history/songs
    songs_history_path = base_path / "data" / "history" / "songs"
    available_dates = []
    
    if songs_history_path.exists():
        for file in songs_history_path.glob("*.json"):
            date = file.stem
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                available_dates.append(date)
    
    # Trier par ordre décroissant
    available_dates.sort(reverse=True)
    
    # Mettre à jour
    meta["kworb_last_update_utc"] = last_update_kworb.isoformat()
    meta["spotify_data_date"] = spotify_data_date
    meta["last_sync_local_iso"] = datetime.now().isoformat()
    meta["history"] = {
        "available_dates": available_dates,
        "latest_date": available_dates[0] if available_dates else spotify_data_date
    }
    
    # Sauvegarder
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    print(f"📝 meta.json mis à jour")
    print(f"   Dates disponibles : {len(available_dates)}")


def regenerate_current_view(base_path: Path):
    """
    Régénère data/songs.json à partir des snapshots disponibles.
    Utilise le script generate_current_views.py existant.
    """
    import subprocess
    
    script_path = base_path / "scripts" / "generate_current_views.py"
    
    print("🔄 Régénération de la vue courante data/songs.json...")
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(base_path),
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"❌ Erreur lors de la régénération: {result.stderr}")
        raise Exception("Échec de la régénération de data/songs.json")


def main():
    """Point d'entrée principal."""
    base_path = Path(__file__).parent.parent
    
    print("="*60)
    print("🎵 Scraper Kworb Songs — The Weeknd Dashboard")
    print("="*60)
    
    try:
        # 1. Scraper Kworb
        songs, last_update_kworb = scrape_kworb_songs(KWORB_SONGS_URL)
        
        # 2. Créer snapshot J
        spotify_data_date = create_snapshot(songs, last_update_kworb, base_path)
        
        # 3. Mettre à jour meta.json
        update_meta(spotify_data_date, last_update_kworb, base_path)
        
        # 4. Régénérer data/songs.json
        regenerate_current_view(base_path)
        
        print("\n" + "="*60)
        print("✅ Scraping terminé avec succès!")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ Erreur critique : {e}")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()
