#!/usr/bin/env python3
"""
Scraper Kworb pour les albums de The Weeknd.
Génère un snapshot journalier et régénère data/albums.json avec calculs.
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
KWORB_ALBUMS_URL = "https://kworb.net/spotify/artist/1Xyo4u8uXC1ZmMpatF05PJ_albums.html"
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
    - suppression ponctuation et caractères spéciaux
    """
    # Lowercase et trim
    text = text.lower().strip()
    
    # Retirer parenthèses et leur contenu
    if "(" in text:
        text = text.split("(")[0].strip()
    
    # Retirer caractères spéciaux et ponctuation
    # Garder seulement lettres, chiffres et espaces
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789 "
    text = ''.join(char for char in text if char in allowed_chars)
    
    # Nettoyer les espaces multiples
    text = ' '.join(text.split())
    
    return text.strip()


def generate_album_id(album_title: str) -> str:
    """
    Génère un ID stable pour un album.
    Format: kworb:album:<norm_album>
    """
    norm_album = normalize_text(album_title)
    return f"kworb:album:{norm_album}"


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


def scrape_kworb_albums(url: str, retries: int = MAX_RETRIES) -> Tuple[List[Dict], datetime]:
    """
    Scrape la page Kworb Albums et retourne les données brutes.
    
    Returns:
        Tuple[List[Dict], datetime]: (liste des albums, timestamp de mise à jour)
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
            print(f"🌐 Récupération des données albums depuis Kworb (tentative {attempt + 1}/{retries})...")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Forcer l'encodage UTF-8 pour éviter les erreurs cp1252 sur Windows
            response.encoding = 'utf-8'
            
            # Throttle
            time.sleep(THROTTLE_SECONDS)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver la table des albums (table avec class 'sortable')
            tables = soup.find_all('table')
            table = None
            for t in tables:
                if 'sortable' in t.get('class', []):
                    table = t
                    break
            
            if not table:
                raise ValueError("Table d'albums non trouvée sur la page")
            
            rows = table.find_all('tr')[1:]  # Skip header
            
            if not rows:
                raise ValueError("Aucune ligne de données trouvée dans la table")
            
            albums = []
            last_update_kworb = datetime.now(timezone.utc)
            seen_ids = {}  # Pour gérer les doublons
            
            for i, row in enumerate(rows, start=1):
                cols = row.find_all('td')
                
                # Structure Kworb Albums : [Album Title, Streams Total, Daily]
                if len(cols) < 3:
                    continue
                
                # Extraction des données
                rank = i
                title = cols[0].get_text(strip=True)
                streams_total_text = cols[1].get_text(strip=True)
                streams_daily_text = cols[2].get_text(strip=True)
                
                # Nettoyage et typage
                streams_total = clean_number(streams_total_text)
                streams_daily = clean_number(streams_daily_text)
                
                # Génération de l'ID stable
                # Format: kworb:album:<norm_album>
                base_id = generate_album_id(title)
                album_id = base_id
                
                # Gérer les doublons (ex: différentes éditions d'un même album)
                if album_id in seen_ids:
                    seen_ids[album_id] += 1
                    # Ajouter suffixe numérique
                    album_id = f"{base_id}-{seen_ids[album_id]}"
                else:
                    seen_ids[album_id] = 1
                
                album = {
                    "id": album_id,
                    "rank": rank,
                    "title": title,
                    "streams_total": streams_total,
                    "streams_daily": streams_daily
                }
                
                albums.append(album)
            
            print(f"✅ {len(albums)} albums extraits avec succès")
            
            # Extraire le timestamp "Last updated" depuis le HTML
            last_update_kworb = extract_kworb_last_update(response.text)
            
            # Fallback : si extraction échoue, utiliser datetime.now(UTC)
            if last_update_kworb is None:
                print("[WARN] Timestamp Kworb non trouvé, fallback sur datetime.now(UTC)")
                last_update_kworb = datetime.now(timezone.utc)
            
            return albums, last_update_kworb
            
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


def create_snapshot(albums: List[Dict], last_update_kworb: datetime, base_path: Path) -> str:
    """
    Crée un snapshot journalier dans data/history/albums/ avec rotation intelligente J/J-1/J-2.
    
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
    
    # Log la décision (albums utilisent même date que songs)
    if rotated:
        print(f"[ROTATE] ALBUMS : Nouveau jour détecté → {spotify_data_date}")
    else:
        print(f"[UPDATE] ALBUMS : Même jour, réécriture J = {spotify_data_date}.json")
    
    # Enrichir chaque album avec les timestamps
    snapshot_albums = []
    for album in albums:
        snapshot_album = {
            **album,
            "last_update_kworb": last_update_kworb.isoformat(),
            "spotify_data_date": spotify_data_date
        }
        snapshot_albums.append(snapshot_album)
    
    # Effectuer la rotation atomique (idempotente)
    success = rotate_snapshots_atomic(
        base_path,
        "albums",
        spotify_data_date,
        snapshot_albums
    )
    
    if not success:
        print("[ERROR] Échec de la rotation des snapshots albums")
    
    return spotify_data_date


def update_meta(spotify_data_date: str, last_update_kworb: datetime, base_path: Path):
    """
    Met à jour data/meta.json avec les nouvelles informations Albums.
    Utilise le date_manager pour gérer history de façon cohérente.
    """
    meta_path = base_path / "data" / "meta.json"
    
    # Utiliser le gestionnaire pour mettre à jour meta.json
    meta = update_meta_with_rotation(
        meta_path,
        last_update_kworb,
        spotify_data_date,
        data_type="albums"
    )
    
    print(f"💾 meta.json mis à jour (albums)")
    available_dates = meta.get("history", {}).get("available_dates_albums", [])
    print(f"   Dates disponibles albums : {len(available_dates)}")


def regenerate_current_view(base_path: Path):
    """
    Régénère data/albums.json à partir des snapshots disponibles.
    Utilise le script generate_current_views.py existant.
    """
    import subprocess
    
    script_path = base_path / "scripts" / "generate_current_views.py"
    
    print("🔄 Régénération de la vue courante data/albums.json...")
    
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
        raise Exception("Échec de la régénération de data/albums.json")


def main():
    """Point d'entrée principal."""
    base_path = Path(__file__).parent.parent
    
    print("="*60)
    print("💿 Scraper Kworb Albums — The Weeknd Dashboard")
    print("="*60)
    
    try:
        # 1. Scraper Kworb Albums
        albums, last_update_kworb = scrape_kworb_albums(KWORB_ALBUMS_URL)
        
        # 2. Créer snapshot J
        spotify_data_date = create_snapshot(albums, last_update_kworb, base_path)
        
        # 3. Mettre à jour meta.json
        update_meta(spotify_data_date, last_update_kworb, base_path)
        
        # 4. Régénérer data/albums.json
        regenerate_current_view(base_path)
        
        print("\n" + "="*60)
        print("✅ Scraping Albums terminé avec succès!")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ Erreur critique : {e}")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()
