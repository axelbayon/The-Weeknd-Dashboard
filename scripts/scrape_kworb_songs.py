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
    print("[ERROR] Dépendances manquantes. Installez-les avec:")
    print("   pip install requests beautifulsoup4")
    sys.exit(1)

# Importer le gestionnaire de dates
from date_manager import (
    extract_kworb_last_update,
    calculate_spotify_data_date,
    rotate_snapshots_atomic,
    update_meta_with_rotation,
    log_rotation_decision,
    should_rotate
)


# Configuration
KWORB_SONGS_URL = "https://kworb.net/spotify/artist/1Xyo4u8uXC1ZmMpatF05PJ_songs.html"
USER_AGENT = "The-Weeknd-Dashboard/1.0 (Educational Project; Python Scraper)"
THROTTLE_SECONDS = 1.0
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


def normalize_text(text: str) -> str:
    """
    Normalise un texte pour génération d'ID stable.
    
    Règles :
    - lowercasing
    - trim
    - suppression ponctuation
    - "feat./with/x/& (...)" retirés
    """
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


def generate_song_id(title: str, album: str) -> str:
    """
    Génère un ID stable pour une chanson.
    Format: kworb:<norm_title>@<norm_album>
    Si album inconnu, utiliser "unknown".
    
    IMPORTANT: Ne JAMAIS inclure le rank dans l'ID (stabilité inter-jours).
    """
    norm_title = normalize_text(title)
    norm_album = normalize_text(album) if album and album.lower() != "unknown" else "unknown"
    
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
    print(f"[WARN] Impossible de parser la date '{date_str}', utilisation de la date actuelle")
    return datetime.now(timezone.utc)


def scrape_kworb_songs(url: str, retries: int = MAX_RETRIES) -> Tuple[List[Dict], datetime, Dict]:
    """
    Scrape la page Kworb Songs et retourne les données brutes + stats role.
    
    Returns:
        Tuple[List[Dict], datetime, Dict]: (liste des chansons, timestamp, stats lead/feat)
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
            print(f"[GET] Récupération des données depuis Kworb (tentative {attempt + 1}/{retries})...")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Forcer l'encodage UTF-8 pour éviter les erreurs cp1252 sur Windows
            response.encoding = 'utf-8'
            
            # Throttle
            time.sleep(THROTTLE_SECONDS)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraire les stats Lead/Feat depuis la table des stats agrégées
            role_stats = {"lead": {}, "feat": {}}
            
            # Trouver toutes les tables
            tables = soup.find_all('table')
            
            # La première table (avant sortable) contient les stats agrégées
            stats_table = None
            for t in tables:
                if 'sortable' not in t.get('class', []):
                    stats_table = t
                    break
            
            if stats_table:
                rows = stats_table.find_all('tr')
                # rows[0] = header (Total, As lead, Solo, As feature)
                # rows[1] = Streams
                # rows[2] = Daily
                # rows[3] = Tracks
                
                if len(rows) >= 4:
                    # Extraire les valeurs des colonnes : col[1]=Total, col[2]=As lead, col[3]=Solo, col[4]=As feature
                    tracks_row = rows[3].find_all('td')
                    streams_row = rows[1].find_all('td')
                    daily_row = rows[2].find_all('td')
                    
                    if len(tracks_row) >= 5 and len(streams_row) >= 5 and len(daily_row) >= 5:
                        # As lead : col[2]
                        role_stats["lead"] = {
                            "count": int(tracks_row[2].get_text(strip=True).replace(',', '')),
                            "streams_total": clean_number(streams_row[2].get_text(strip=True)),
                            "streams_daily": clean_number(daily_row[2].get_text(strip=True))
                        }
                        
                        # As feature : col[4]
                        role_stats["feat"] = {
                            "count": int(tracks_row[4].get_text(strip=True).replace(',', '')),
                            "streams_total": clean_number(streams_row[4].get_text(strip=True)),
                            "streams_daily": clean_number(daily_row[4].get_text(strip=True))
                        }
                        
                        print(f"[Stats] Lead/Feat extraites : Lead={role_stats['lead']['count']} songs, Feat={role_stats['feat']['count']} songs")
                    else:
                        print("[WARN] Impossible d'extraire les stats : colonnes manquantes")
                else:
                    print("[WARN] Impossible d'extraire les stats : lignes manquantes")
            else:
                print("[WARN] Table de stats agrégées non trouvée")
            
            # Trouver la table des chansons (la table avec class 'sortable')
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
            seen_ids = {}  # Pour gérer les doublons temporaires
            
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
                
                # Génération de l'ID stable (sans rank!)
                # Format: kworb:<norm_title>@unknown
                # Si doublon, ajouter suffixe numérique: @unknown-2, @unknown-3, etc.
                base_id = generate_song_id(title, album)
                song_id = base_id
                
                # Gérer les doublons temporaires (en attendant données Spotify)
                if song_id in seen_ids:
                    seen_ids[song_id] += 1
                    # Remplacer @unknown par @unknown-N
                    song_id = song_id.replace("@unknown", f"@unknown-{seen_ids[song_id]}")
                else:
                    seen_ids[song_id] = 1
                
                song = {
                    "id": song_id,
                    "rank": rank,
                    "title": title,
                    "album": album,
                    "role": role,
                    "streams_total": streams_total,
                    "streams_daily": streams_daily
                }
                
                # Filtrer le doublon "XO / The Host" avec 0 streams quotidiens
                # (conserve uniquement la version avec des streams actifs)
                if title == "XO / The Host" and streams_daily == 0:
                    print(f"[FILTER] Exclusion doublon: {title} (rang {rank}, 0 streams quotidiens)")
                    continue
                
                songs.append(song)
            
            print(f"[OK] {len(songs)} chansons extraites avec succès")
            
            # Extraire le timestamp "Last updated" depuis le HTML
            last_update_kworb = extract_kworb_last_update(response.text)
            
            # Fallback : si extraction échoue, utiliser datetime.now(UTC)
            if last_update_kworb is None:
                print("[WARN] Timestamp Kworb non trouvé, fallback sur datetime.now(UTC)")
                last_update_kworb = datetime.now(timezone.utc)
            
            return songs, last_update_kworb, role_stats
            
        except requests.RequestException as e:
            print(f"[ERROR] Erreur réseau (tentative {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                wait_time = RETRY_BACKOFF ** attempt
                print(f"[WAIT] Nouvelle tentative dans {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            print(f"[ERROR] Erreur lors du scraping: {e}")
            raise


def create_snapshot(songs: List[Dict], last_update_kworb: datetime, base_path: Path) -> str:
    """
    Crée un snapshot journalier dans data/history/songs/ avec rotation intelligente J/J-1/J-2.
    
    Utilise le date_manager pour :
    - Calculer spotify_data_date depuis kworb_last_update_utc
    - Effectuer la rotation atomique si nouveau jour
    - Mettre à jour meta.json
    
    Returns:
        str: La date spotify_data_date (YYYY-MM-DD)
    """
    # Calculer spotify_data_date = kworb_day - 1 jour
    spotify_data_date = calculate_spotify_data_date(last_update_kworb)
    
    # Charger meta.json pour vérifier s'il faut rotate
    meta_path = base_path / "data" / "meta.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {"history": {}}
    
    previous_date = meta.get("history", {}).get("latest_date")
    rotated = should_rotate(meta, spotify_data_date)
    
    # Log la décision
    log_rotation_decision(last_update_kworb, spotify_data_date, previous_date, rotated)
    
    # Enrichir chaque chanson avec les timestamps
    snapshot_songs = []
    for song in songs:
        snapshot_song = {
            **song,
            "last_update_kworb": last_update_kworb.isoformat(),
            "spotify_data_date": spotify_data_date
        }
        snapshot_songs.append(snapshot_song)
    
    # Effectuer la rotation atomique (idempotente)
    success = rotate_snapshots_atomic(
        base_path,
        "songs",
        spotify_data_date,
        snapshot_songs
    )
    
    if not success:
        print("[ERROR] Échec de la rotation des snapshots")
    
    return spotify_data_date


def update_meta(spotify_data_date: str, last_update_kworb: datetime, role_stats: Dict, base_path: Path):
    """
    Met à jour data/meta.json avec les nouvelles informations + stats Lead/Feat.
    Utilise le date_manager pour gérer history de façon cohérente.
    """
    meta_path = base_path / "data" / "meta.json"
    
    # Utiliser le gestionnaire pour mettre à jour meta.json
    meta = update_meta_with_rotation(
        meta_path,
        last_update_kworb,
        spotify_data_date,
        data_type="songs"
    )
    
    # Ajouter les stats Lead/Feat extraites de Kworb
    if role_stats:
        meta["songs_role_stats"] = role_stats
        print(f"[Stats] Lead/Feat ajoutées à meta.json : Lead={role_stats.get('lead', {}).get('count', 'N/A')}, Feat={role_stats.get('feat', {}).get('count', 'N/A')}")
        
        # Sauvegarder à nouveau avec les stats
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    
    print(f"[SAVE] meta.json mis à jour")
    available_dates = meta.get("history", {}).get("available_dates", [])
    print(f"   Dates disponibles : {len(available_dates)}")


def regenerate_current_view(base_path: Path):
    """
    Régénère data/songs.json à partir des snapshots disponibles.
    Utilise le script generate_current_views.py existant.
    """
    import subprocess
    
    script_path = base_path / "scripts" / "generate_current_views.py"
    
    print("[REGEN] Régénération de la vue courante data/songs.json...")
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(base_path),
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"[ERROR] Erreur lors de la régénération: {result.stderr}")
        raise Exception("Échec de la régénération de data/songs.json")


def main():
    """Point d'entrée principal."""
    base_path = Path(__file__).parent.parent
    
    print("="*60)
    print("[SCRAPER] Kworb Songs - The Weeknd Dashboard")
    print("="*60)
    
    try:
        # 1. Scraper Kworb
        songs, last_update_kworb, role_stats = scrape_kworb_songs(KWORB_SONGS_URL)
        
        # 2. Créer snapshot J
        spotify_data_date = create_snapshot(songs, last_update_kworb, base_path)
        
        # 3. Mettre à jour meta.json avec les stats Lead/Feat
        update_meta(spotify_data_date, last_update_kworb, role_stats, base_path)
        
        # 4. Régénérer data/songs.json
        regenerate_current_view(base_path)
        
        print("\n" + "="*60)
        print("[OK] Scraping terminé avec succès!")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"[ERROR] Erreur critique : {e}")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()
