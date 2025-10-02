#!/usr/bin/env python3
"""
Validateur de conformité pour les contrats de données.
Vérifie les schémas JSON, arrondis, unicité des id, cohérence des dates.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Union
import sys


class DataValidator:
    """Validateur de données pour le dashboard The Weeknd."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> bool:
        """Exécute toutes les validations. Retourne True si tout est OK."""
        print("🔍 Validation des contrats de données...\n")
        
        # Charger les données
        songs = self._load_json("data/songs.json")
        albums = self._load_json("data/albums.json")
        meta = self._load_json("data/meta.json")
        
        if not songs or not albums or not meta:
            print("❌ Impossible de charger les fichiers de données")
            return False
        
        # Validations
        self.validate_schema_songs(songs)
        self.validate_schema_albums(albums)
        self.validate_schema_meta(meta)
        self.validate_rounding(songs, "songs")
        self.validate_rounding(albums, "albums")
        self.validate_unique_ids(songs, "songs")
        self.validate_unique_ids(albums, "albums")
        self.validate_date_consistency(songs, albums, meta)
        self.validate_cap_values(songs, "songs", 100_000_000)
        self.validate_cap_values(albums, "albums", 1_000_000_000)
        
        # Résumé
        print("\n" + "="*60)
        if self.errors:
            print(f"❌ {len(self.errors)} erreur(s) détectée(s):")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"⚠️  {len(self.warnings)} avertissement(s):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ Toutes les validations sont passées avec succès!")
        
        print("="*60)
        
        return len(self.errors) == 0
    
    def _load_json(self, relative_path: str) -> Union[Dict, List, None]:
        """Charge un fichier JSON."""
        filepath = self.base_path / relative_path
        if not filepath.exists():
            self.errors.append(f"Fichier introuvable: {relative_path}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Erreur JSON dans {relative_path}: {e}")
            return None
    
    def validate_schema_songs(self, songs: List[Dict]):
        """Valide le schéma des chansons."""
        print("📋 Validation du schéma songs.json...")
        
        required_fields = [
            "id", "rank", "title", "album", "role", "streams_total",
            "streams_daily", "streams_daily_prev", "variation_pct",
            "next_cap_value", "days_to_next_cap", "last_update_kworb",
            "spotify_data_date", "spotify_track_id", "spotify_album_id"
        ]
        
        for i, song in enumerate(songs):
            for field in required_fields:
                if field not in song:
                    self.errors.append(f"songs[{i}]: champ manquant '{field}'")
            
            # Validation des types et contraintes
            if "id" in song and not song["id"].startswith("kworb:"):
                self.errors.append(f"songs[{i}]: id invalide (doit commencer par 'kworb:')")
            
            if "rank" in song and (not isinstance(song["rank"], int) or song["rank"] < 1):
                self.errors.append(f"songs[{i}]: rank invalide (doit être entier >= 1)")
            
            if "role" in song and song["role"] not in ["lead", "feat"]:
                self.errors.append(f"songs[{i}]: role invalide (doit être 'lead' ou 'feat')")
        
        print(f"   ✓ {len(songs)} chansons validées")
    
    def validate_schema_albums(self, albums: List[Dict]):
        """Valide le schéma des albums."""
        print("📋 Validation du schéma albums.json...")
        
        required_fields = [
            "id", "rank", "title", "streams_total", "streams_daily",
            "streams_daily_prev", "variation_pct", "next_cap_value",
            "days_to_next_cap", "last_update_kworb", "spotify_data_date",
            "spotify_album_id"
        ]
        
        for i, album in enumerate(albums):
            for field in required_fields:
                if field not in album:
                    self.errors.append(f"albums[{i}]: champ manquant '{field}'")
            
            if "id" in album and not album["id"].startswith("kworb:"):
                self.errors.append(f"albums[{i}]: id invalide (doit commencer par 'kworb:')")
            
            if "rank" in album and (not isinstance(album["rank"], int) or album["rank"] < 1):
                self.errors.append(f"albums[{i}]: rank invalide (doit être entier >= 1)")
        
        print(f"   ✓ {len(albums)} albums validés")
    
    def validate_schema_meta(self, meta: Dict):
        """Valide le schéma meta.json."""
        print("📋 Validation du schéma meta.json...")
        
        required_fields = [
            "kworb_last_update_utc", "spotify_data_date",
            "last_sync_local_iso", "history"
        ]
        
        for field in required_fields:
            if field not in meta:
                self.errors.append(f"meta.json: champ manquant '{field}'")
        
        if "history" in meta:
            if "available_dates" not in meta["history"]:
                self.errors.append("meta.json: history.available_dates manquant")
            if "latest_date" not in meta["history"]:
                self.errors.append("meta.json: history.latest_date manquant")
        
        print("   ✓ meta.json validé")
    
    def validate_rounding(self, items: List[Dict], data_type: str):
        """Valide les arrondis à 2 décimales pour variation_pct et days_to_next_cap."""
        print(f"🔢 Validation des arrondis pour {data_type}...")
        
        for i, item in enumerate(items):
            # Variation %
            if "variation_pct" in item:
                var = item["variation_pct"]
                if isinstance(var, (int, float)):
                    # Vérifier que c'est arrondi à 2 décimales
                    rounded = round(var, 2)
                    if abs(var - rounded) > 1e-10:
                        self.errors.append(
                            f"{data_type}[{i}]: variation_pct non arrondi à 2 déc. ({var})"
                        )
                elif var != "N.D.":
                    self.errors.append(
                        f"{data_type}[{i}]: variation_pct invalide (doit être nombre ou 'N.D.')"
                    )
            
            # Jours restants
            if "days_to_next_cap" in item:
                days = item["days_to_next_cap"]
                if isinstance(days, (int, float)):
                    rounded = round(days, 2)
                    if abs(days - rounded) > 1e-10:
                        self.errors.append(
                            f"{data_type}[{i}]: days_to_next_cap non arrondi à 2 déc. ({days})"
                        )
                elif days != "N.D.":
                    self.errors.append(
                        f"{data_type}[{i}]: days_to_next_cap invalide (doit être nombre ou 'N.D.')"
                    )
        
        print(f"   ✓ Arrondis validés pour {data_type}")
    
    def validate_unique_ids(self, items: List[Dict], data_type: str):
        """Valide l'unicité des id."""
        print(f"🔑 Validation de l'unicité des id pour {data_type}...")
        
        ids = [item.get("id") for item in items if "id" in item]
        unique_ids = set(ids)
        
        if len(ids) != len(unique_ids):
            duplicates = [id for id in ids if ids.count(id) > 1]
            self.errors.append(
                f"{data_type}: id dupliqués détectés: {set(duplicates)}"
            )
        else:
            print(f"   ✓ {len(ids)} id uniques pour {data_type}")
    
    def validate_date_consistency(self, songs: List[Dict], albums: List[Dict], meta: Dict):
        """Valide la cohérence des dates entre fichiers."""
        print("📅 Validation de la cohérence des dates...")
        
        latest_date = meta.get("history", {}).get("latest_date")
        spotify_data_date = meta.get("spotify_data_date")
        
        # Vérifier que spotify_data_date = latest_date
        if latest_date != spotify_data_date:
            self.errors.append(
                f"Incohérence: meta.spotify_data_date ({spotify_data_date}) != "
                f"meta.history.latest_date ({latest_date})"
            )
        
        # Vérifier que toutes les chansons ont la même date
        for i, song in enumerate(songs):
            if song.get("spotify_data_date") != spotify_data_date:
                self.errors.append(
                    f"songs[{i}]: spotify_data_date ({song.get('spotify_data_date')}) "
                    f"!= meta.spotify_data_date ({spotify_data_date})"
                )
        
        # Vérifier que tous les albums ont la même date
        for i, album in enumerate(albums):
            if album.get("spotify_data_date") != spotify_data_date:
                self.errors.append(
                    f"albums[{i}]: spotify_data_date ({album.get('spotify_data_date')}) "
                    f"!= meta.spotify_data_date ({spotify_data_date})"
                )
        
        print(f"   ✓ Dates cohérentes (spotify_data_date = {spotify_data_date})")
    
    def validate_cap_values(self, items: List[Dict], data_type: str, step: int):
        """Valide que les paliers sont corrects."""
        print(f"🎯 Validation des paliers pour {data_type} (step={step:,})...")
        
        for i, item in enumerate(items):
            if "next_cap_value" in item and "streams_total" in item:
                next_cap = item["next_cap_value"]
                streams_total = item["streams_total"]
                
                # Vérifier que c'est un multiple du step
                if next_cap % step != 0:
                    self.errors.append(
                        f"{data_type}[{i}]: next_cap_value ({next_cap:,}) "
                        f"n'est pas un multiple de {step:,}"
                    )
                
                # Vérifier que c'est supérieur strict à streams_total
                if next_cap <= streams_total:
                    self.errors.append(
                        f"{data_type}[{i}]: next_cap_value ({next_cap:,}) "
                        f"doit être > streams_total ({streams_total:,})"
                    )
        
        print(f"   ✓ Paliers validés pour {data_type}")


def main():
    """Point d'entrée principal."""
    base_path = Path(__file__).parent.parent
    validator = DataValidator(base_path)
    
    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
