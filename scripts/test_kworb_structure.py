#!/usr/bin/env python3
"""
Script de test pour analyser la structure HTML de Kworb.
"""

import requests
from bs4 import BeautifulSoup

url = "https://kworb.net/spotify/artist/1Xyo4u8uXC1ZmMpatF05PJ_songs.html"
headers = {"User-Agent": "The-Weeknd-Dashboard/1.0 (Educational Project)"}

response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.content, 'html.parser')

# Afficher toutes les tables
tables = soup.find_all('table')
print(f"Nombre de tables trouvees: {len(tables)}")

for i, table in enumerate(tables):
    print(f"\n=== Table {i+1} ===")
    print(f"Classes: {table.get('class')}")
    rows = table.find_all('tr')
    print(f"Nombre de lignes: {len(rows)}")
    
    if rows:
        # Afficher la première ligne (header)
        print("\nHeader:")
        headers_cells = rows[0].find_all(['th', 'td'])
        for cell in headers_cells:
            print(f"  - {cell.get_text(strip=True)}")
        
        # Afficher les 3 premières lignes de données
        print("\nPremières lignes de données:")
        for row in rows[1:4]:
            cols = row.find_all('td')
            print(f"  Colonnes: {len(cols)}")
            for j, col in enumerate(cols):
                print(f"    [{j}] {col.get_text(strip=True)[:50]}")
