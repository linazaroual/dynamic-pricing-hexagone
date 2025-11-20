import os
import json
import uuid
import h3

# Résolution H3 (8 ≈ 0.5 km)
RES = 8

# Fichier GeoJSON avec la frontière de l'Île-de-France
GEOJSON_PATH = "docs/ile_de_france.geojson"


def load_idf_outer_ring():
    """
    Charge le GeoJSON IDF et renvoie :
    - une liste de points du polygone extérieur au format (lat, lng)
    - la bbox (min_lat, max_lat, min_lng, max_lng) pour limiter les calculs
    """
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        gj = json.load(f)

    # Récupérer la géométrie
    if gj.get("type") == "FeatureCollection":
        geom = gj["features"][0]["geometry"]
    elif gj.get("type") == "Feature":
        geom = gj["geometry"]
    else:
        geom = gj

    # On prend le premier anneau (polygone extérieur)
    # GeoJSON: [ [lng, lat], [lng, lat], ... ]
    coords = geom["coordinates"][0]

    poly = []
    lats = []
    lngs = []
    for lng, lat in coords:
        poly.append((lat, lng))   # on stocke en (lat, lng)
        lats.append(lat)
        lngs.append(lng)

    bbox = (min(lats), max(lats), min(lngs), max(lngs))
    return poly, bbox


def point_in_poly(lat, lng, poly):
    """
    Test point-in-polygon (algorithme du rayon horizontal).
    poly : liste de (lat, lng)
    """
    inside = False
    n = len(poly)
    for i in range(n):
        lat1, lng1 = poly[i]
        lat2, lng2 = poly[(i + 1) % n]

        # croisement avec le rayon horizontal vers l'est
        if ((lng1 > lng) != (lng2 > lng)):
            # calcul de la latitude du point d'intersection
            inter_lat = lat1 + (lat2 - lat1) * (lng - lng1) / (lng2 - lng1 + 1e-12)
            if inter_lat > lat:
                inside = not inside
    return inside


def h3_cell_to_polygon(h):
    """
    Transforme un index H3 en polygone GeoJSON (anneau fermé).
    """
    boundary = h3.cell_to_boundary(h)
    ring = [[lng, lat] for lat, lng in boundary]
    ring.append(ring[0])
    return [ring]


def main():
    print("📍 Chargement frontière Île-de-France…")
    poly, bbox = load_idf_outer_ring()
    min_lat, max_lat, min_lng, max_lng = bbox
    print("   BBOX:", bbox)

    # Seed au centre de Paris
    seed_lat, seed_lng = 48.8566, 2.3522
    seed = h3.latlng_to_cell(seed_lat, seed_lng, RES)

    # On explore autour du seed avec grid_disk
    print("🧮 Génération des hexagones H3 par propagation (grid_disk)…")
    cells = set([seed])
    MAX_K = 120  # rayon max en "anneaux" H3 (suffisant pour IDF en res=8)

    for k in range(1, MAX_K + 1):
        ring = h3.grid_disk(seed, k)
        cells.update(ring)

    print(f"   Total hexagones dans le disque brut : {len(cells)}")

    # Filtrer par bbox + polygone
    print("🧹 Filtrage par BBOX + polygone IDF…")
    kept = []
    for h in cells:
        lat, lng = h3.cell_to_latlng(h)
        # d'abord BBOX grossière
        if not (min_lat <= lat <= max_lat and min_lng <= lng <= max_lng):
            continue
        # puis test précis dans le polygone
        if point_in_poly(lat, lng, poly):
            kept.append(h)

    print(f"➡️ Hexagones conservés dans l'IDF : {len(kept)}")

    os.makedirs("docs", exist_ok=True)

    # JSON backend
    zones = []
    for h in kept:
        zones.append({
            "uuid": str(uuid.uuid4()),
            "h3_index": h,
        })

    with open("docs/idf_hex_grid_res8.json", "w", encoding="utf-8") as f:
        json.dump(zones, f, indent=2, ensure_ascii=False)

    # GeoJSON pour Leaflet
    features = []
    for z in zones:
        h = z["h3_index"]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": h3_cell_to_polygon(h),
            },
            "properties": z,
        })

    geo = {"type": "FeatureCollection", "features": features}
    with open("docs/idf_hex_grid_res8.geojson", "w", encoding="utf-8") as f:
        json.dump(geo, f, indent=2, ensure_ascii=False)

    print("✅ Fichiers générés dans docs/:")
    print("   - idf_hex_grid_res8.json")
    print("   - idf_hex_grid_res8.geojson")


if __name__ == "__main__":
    main()

    