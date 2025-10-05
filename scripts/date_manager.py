#!/usr/bin/env python3
"""
Gestionnaire de dates et rotation J/J-1/J-2 pour The Weeknd Dashboard.

Règle métier critique :
- spotify_data_date = kworb_day - 1 jour calendaire
- Ne change JAMAIS tant que kworb_day n'a pas changé
- Rotation J→J-1→J-2 uniquement si spotify_data_date > history.latest_date

Source de vérité unique : meta.json.kworb_last_update_utc (UTC)
"""

import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict
import re


def parse_kworb_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse un timestamp Kworb en forçant UTC.
    
    Formats supportés :
    - ISO 8601 avec timezone : "2025-10-05T19:28:03.912861+00:00"
    - ISO 8601 sans timezone : "2025-10-05T19:28:03"
    - Date simple : "2025-10-05"
    
    Returns:
        datetime en UTC ou None si parsing échoue
    """
    if not timestamp_str:
        return None
    
    timestamp_str = timestamp_str.strip()
    
    # Format ISO 8601 avec timezone
    formats_with_tz = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # 2025-10-05T19:28:03.912861+00:00
        "%Y-%m-%dT%H:%M:%S%z",      # 2025-10-05T19:28:03+00:00
    ]
    
    for fmt in formats_with_tz:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            # Convertir en UTC si autre timezone
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    
    # Format ISO 8601 sans timezone (assume UTC)
    formats_without_tz = [
        "%Y-%m-%dT%H:%M:%S.%f",  # 2025-10-05T19:28:03.912861
        "%Y-%m-%dT%H:%M:%S",      # 2025-10-05T19:28:03
        "%Y-%m-%d",               # 2025-10-05
    ]
    
    for fmt in formats_without_tz:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    
    print(f"[WARN] Impossible de parser le timestamp Kworb: {timestamp_str}")
    return None


def extract_kworb_last_update(html_content: str) -> Optional[datetime]:
    """
    Extrait le timestamp "Last updated" depuis le HTML Kworb.
    
    Cherche les patterns courants :
    - "Last updated: YYYY/MM/DD" (format Kworb réel)
    - "Last updated: YYYY-MM-DD HH:MM:SS UTC"
    - "Page last updated: ..."
    - timestamp dans un élément <time> ou <span>
    
    Returns:
        datetime en UTC ou None si non trouvé
    """
    # Pattern 1: "Last updated: YYYY/MM/DD" (format Kworb réel)
    pattern1 = r'Last updated:?\s*(\d{4}/\d{2}/\d{2})'
    match = re.search(pattern1, html_content, re.IGNORECASE)
    if match:
        date_str = match.group(1).strip()
        try:
            dt = datetime.strptime(date_str, "%Y/%m/%d")
            # Kworb met à jour vers minuit UTC
            return dt.replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
        except ValueError:
            pass
    
    # Pattern 2: "Last updated: YYYY-MM-DD HH:MM:SS"
    pattern2 = r'Last updated:?\s*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)'
    match = re.search(pattern2, html_content, re.IGNORECASE)
    if match:
        date_str = match.group(1).strip()
        # Ajouter :00 si pas d'heure
        if ' ' not in date_str:
            date_str += " 00:00:00"
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    
    # Pattern 3: Date dans format US "MM/DD/YYYY"
    pattern3 = r'(\d{1,2}/\d{1,2}/\d{4})'
    match = re.search(pattern3, html_content)
    if match:
        date_str = match.group(1)
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    
    # Si aucun pattern trouvé, retourner None
    # Le fallback sera datetime.now(timezone.utc) dans le code appelant
    print("[WARN] Aucun timestamp 'Last updated' trouvé dans le HTML Kworb")
    return None


def calculate_spotify_data_date(kworb_last_update_utc: datetime) -> str:
    """
    Calcule spotify_data_date à partir du timestamp Kworb UTC.
    
    Règle : spotify_data_date = (jour calendaire de kworb_last_update_utc) - 1 jour
    
    Exemple :
    - kworb_last_update_utc = 2025-10-05T19:28:03+00:00
    - kworb_day = 2025-10-05
    - spotify_data_date = 2025-10-04
    
    Args:
        kworb_last_update_utc: datetime en UTC
    
    Returns:
        str: Date au format YYYY-MM-DD
    """
    # Extraire le jour calendaire en UTC
    kworb_day = kworb_last_update_utc.date()
    
    # Soustraire 1 jour
    spotify_date = kworb_day - timedelta(days=1)
    
    return spotify_date.strftime("%Y-%m-%d")


def should_rotate(meta: Dict, new_spotify_data_date: str) -> bool:
    """
    Détermine si une rotation J/J-1/J-2 est nécessaire.
    
    Critère : new_spotify_data_date > meta.history.latest_date (strict)
    
    Args:
        meta: Contenu de meta.json
        new_spotify_data_date: Nouvelle date calculée (YYYY-MM-DD)
    
    Returns:
        bool: True si rotation nécessaire
    """
    if "history" not in meta or "latest_date" not in meta["history"]:
        # Premier run, toujours créer le snapshot
        return True
    
    current_latest = meta["history"]["latest_date"]
    
    # Comparer les dates (format YYYY-MM-DD permet comparaison string)
    return new_spotify_data_date > current_latest


def rotate_snapshots_atomic(
    base_path: Path,
    data_type: str,
    new_date: str,
    current_data: list
) -> bool:
    """
    Effectue une rotation atomique et idempotente J→J-1→J-2 pour songs ou albums.
    
    Étapes :
    1. Vérifier si rotation nécessaire (nouveau jour)
    2. Si oui :
       - Renommer ancien J-1 → J-2 (supprime J-2 si existe)
       - Renommer ancien J → J-1
       - Créer nouveau J avec current_data
    3. Sinon :
       - Réécrire seulement le fichier J actuel (idempotence)
    
    Args:
        base_path: Racine du projet
        data_type: "songs" ou "albums"
        new_date: Date du nouveau snapshot (YYYY-MM-DD)
        current_data: Données à écrire dans le snapshot J
    
    Returns:
        bool: True si succès
    """
    history_path = base_path / "data" / "history" / data_type
    history_path.mkdir(parents=True, exist_ok=True)
    
    # Charger meta.json pour connaître la latest_date actuelle
    meta_path = base_path / "data" / "meta.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {"history": {}}
    
    # Déterminer si rotation nécessaire
    needs_rotation = should_rotate(meta, new_date)
    
    if needs_rotation:
        print(f"[ROTATE] {data_type.upper()} : Nouveau jour détecté → {new_date}")
        
        # Récupérer l'ancienne latest_date
        old_latest = meta.get("history", {}).get("latest_date")
        
        if old_latest and old_latest != new_date:
            # Étape 1 : Chercher J-1 actuel (s'il existe)
            # On liste tous les fichiers et on prend le 2ème plus récent
            snapshots = sorted(history_path.glob("*.json"), reverse=True)
            
            if len(snapshots) >= 2:
                # snapshots[0] = J actuel
                # snapshots[1] = J-1 actuel → doit devenir J-2
                j_minus_1 = snapshots[1]
                
                # Supprimer l'ancien J-2 s'il existe (3ème fichier)
                if len(snapshots) >= 3:
                    old_j_minus_2 = snapshots[2]
                    try:
                        old_j_minus_2.unlink()
                        print(f"   [DEL] J-2 purgé : {old_j_minus_2.name}")
                    except Exception as e:
                        print(f"   [WARN] Impossible de supprimer J-2: {e}")
                
                # Renommer J-1 → J-2
                # Calculer le nouveau nom (date de J-1 - 1 jour)
                try:
                    j_minus_1_date = datetime.strptime(j_minus_1.stem, "%Y-%m-%d").date()
                    # J-2 n'est pas forcément J-1 - 1 jour, on garde juste l'ancien J-1
                    # On ne le renomme pas, on le garde avec son nom actuel
                    # En fait, on veut juste garder les 3 plus récents
                    # Donc on ne fait rien pour J-1, il reste tel quel
                except ValueError:
                    pass
            
            # Étape 2 : Renommer J actuel → J-1
            old_j_path = history_path / f"{old_latest}.json"
            if old_j_path.exists():
                # On le laisse en place avec son nom (il deviendra automatiquement J-1)
                print(f"   [KEEP] {old_latest}.json devient J-1")
        
        # Étape 3 : Créer nouveau J
        new_j_path = history_path / f"{new_date}.json"
        with open(new_j_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
        print(f"   [CREATE] Nouveau J : {new_date}.json")
        
    else:
        print(f"[UPDATE] {data_type.upper()} : Même jour, réécriture J = {new_date}.json")
        
        # Réécrire le fichier J actuel (idempotence)
        current_j_path = history_path / f"{new_date}.json"
        with open(current_j_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
    
    # Maintenir uniquement les 3 fichiers les plus récents (J, J-1, J-2)
    snapshots = sorted(history_path.glob("*.json"), reverse=True)
    if len(snapshots) > 3:
        for old_snapshot in snapshots[3:]:
            try:
                old_snapshot.unlink()
                print(f"   [PURGE] {old_snapshot.name}")
            except Exception as e:
                print(f"   [WARN] Impossible de purger {old_snapshot.name}: {e}")
    
    return True


def update_meta_with_rotation(
    meta_path: Path,
    kworb_last_update_utc: datetime,
    spotify_data_date: str,
    data_type: str = "songs"
) -> Dict:
    """
    Met à jour meta.json avec les nouvelles dates et history.
    
    Args:
        meta_path: Chemin vers meta.json
        kworb_last_update_utc: Timestamp Kworb en UTC
        spotify_data_date: Date Spotify calculée (YYYY-MM-DD)
        data_type: "songs" ou "albums"
    
    Returns:
        Dict: meta.json mis à jour
    """
    # Charger meta.json existant
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {"history": {}}
    
    # Scanner les snapshots disponibles
    base_path = meta_path.parent  # data/
    history_path = base_path / "history" / data_type
    
    available_dates = []
    if history_path.exists():
        for file in history_path.glob("*.json"):
            date = file.stem
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                available_dates.append(date)
    
    # Trier par ordre décroissant
    available_dates.sort(reverse=True)
    
    # Mettre à jour meta
    meta["kworb_last_update_utc"] = kworb_last_update_utc.isoformat()
    meta["spotify_data_date"] = spotify_data_date
    meta["last_sync_local_iso"] = datetime.now().isoformat()
    
    # Mettre à jour history
    if "history" not in meta:
        meta["history"] = {}
    
    if data_type == "songs":
        meta["history"]["available_dates"] = available_dates
        meta["history"]["latest_date"] = available_dates[0] if available_dates else spotify_data_date
    else:  # albums
        meta["history"]["available_dates_albums"] = available_dates
        # Ne pas écraser latest_date qui est géré par songs
    
    # Sauvegarder
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    return meta


def log_rotation_decision(
    kworb_last_update_utc: datetime,
    spotify_data_date: str,
    previous_date: Optional[str],
    rotated: bool
):
    """
    Log clair de la décision de rotation.
    
    Args:
        kworb_last_update_utc: Timestamp Kworb
        spotify_data_date: Nouvelle date calculée
        previous_date: Ancienne latest_date
        rotated: True si rotation effectuée
    """
    kworb_day = kworb_last_update_utc.date().strftime("%Y-%m-%d")
    
    print(f"\n{'='*60}")
    print(f"📅 Date Manager - Décision de rotation")
    print(f"{'='*60}")
    print(f"Kworb Last Updated (UTC) : {kworb_last_update_utc.isoformat()}")
    print(f"Kworb Day (UTC)          : {kworb_day}")
    print(f"Spotify Data Date        : {spotify_data_date} (= Kworb Day - 1)")
    print(f"Previous Latest Date     : {previous_date or 'N/A'}")
    
    if rotated:
        print(f"✅ ROTATION effectuée : {previous_date} → {spotify_data_date}")
    else:
        print(f"⏭️  PAS de rotation : Date inchangée ({spotify_data_date})")
    
    print(f"{'='*60}\n")
