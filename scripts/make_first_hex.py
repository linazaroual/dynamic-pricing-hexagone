# scripts/make_first_hex.py
# Génère un premier hexagone H3 (~1.2 km de côté, res=7) centré à Paris
# et exporte : docs/par_hex_PAR-0001.json + docs/par_hex_PAR-0001.geojson

import os
import uuid
import json
import h3  # v4 API
from geojson import Feature, FeatureCollection, Polygon

def main():
    # --- Paramètres ---
    RES = 7  # ~1.2 km côté moyen
    center_lat, center_lng = 48.856614, 2.3522219  # Paris centre (Hôtel de Ville)

    # --- Calcul H3 (v4) ---
    h = h3.latlng_to_cell(center_lat, center_lng, RES)  # index H3 de la cellule contenant le point
    lat, lng = h3.cell_to_latlng(h)                    # centroïde "canonique" de la cellule
    boundary = h3.cell_to_boundary(h)                  # liste de points [[lat, lng], ...]

    # --- Objet "zone" JSON ---
    zone = {
        "uuid": str(uuid.uuid4()),
        "id": "PAR-0001",
        "h3_index": h,
        "city_code": "PAR",
        "latitude": lat,
        "longitude": lng,
        "available": True,
        "manual_surge": 0,
        "status": "active"
    }

    # --- Dossier de sortie ---
    os.makedirs("docs", exist_ok=True)

    # --- Sauvegarde JSON (données) ---
    with open("docs/par_hex_PAR-0001.json", "w", encoding="utf-8") as f:
        json.dump(zone, f, ensure_ascii=False, indent=2)

    # --- Sauvegarde GeoJSON (affichage Leaflet) ---
    # GeoJSON attend des coordonnées (lng, lat) ET un anneau fermé (retour au premier point).
    ring = [[(lng_, lat_) for (lat_, lng_) in boundary] + [(boundary[0][1], boundary[0][0])]]
    poly = Feature(geometry=Polygon(ring), properties=zone)
    fc = FeatureCollection([poly])

    with open("docs/par_hex_PAR-0001.geojson", "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)

    print("✅ OK:", zone["id"], zone["h3_index"])
    print("→ Fichiers créés dans docs/: par_hex_PAR-0001.json et par_hex_PAR-0001.geojson")

if __name__ == "__main__":
    main()