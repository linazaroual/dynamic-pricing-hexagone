import json
import uuid
import argparse
from shapely.geometry import shape, Point
from tqdm import tqdm
import h3


def load_communes(communes_path):

    with open(communes_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    communes = []
    for feat in data["features"]:
        props = feat.get("properties", {})

        code = (
            props.get("code")
            or props.get("insee")
            or props.get("code_insee")
        )
        name = (
            props.get("nom")
            or props.get("name")
            or props.get("nom_commune")
            or ""
        )

        if not code:
            continue

        dept = str(code)[:2]

        communes.append({
            "code": str(code),
            "name": str(name),
            "dept": dept,
            "geom": shape(feat["geometry"])
        })

    return communes


def find_commune(lat, lng, communes):
    point = Point(lng, lat)
    for c in communes:
        if c["geom"].contains(point):
            return c
    return None


def main():
    parser = argparse.ArgumentParser(description="Enrich H3 hex grid with city metadata")
    parser.add_argument("--grid", required=True, help="Input hex grid GeoJSON")
    parser.add_argument("--communes", required=True, help="Communes GeoJSON")
    parser.add_argument("--output", required=True, help="Output enriched GeoJSON")
    parser.add_argument("--prefix", default="", help="City prefix (IDF, LYO, MAR, etc.)")
    args = parser.parse_args()

    # Charger grille hexagonale
    with open(args.grid, "r", encoding="utf-8") as f:
        grid = json.load(f)

    features = grid["features"]

    # Charger communes
    communes = load_communes(args.communes)

    # Enrichissement
    for feat in tqdm(features, desc="Enriching hexagons"):
        props = feat["properties"]
        h3_index = props["h3_index"]

        lat, lng = h3.cell_to_latlng(h3_index)
        commune = find_commune(lat, lng, communes)

        if commune:
            city_code = commune["code"]
            city_name = commune["name"]
            dept_code = commune["dept"]
        else:
            city_code = "00000"
            city_name = "Unknown"
            dept_code = "00"

        base_id = f"{dept_code}-{city_code}"
        if args.prefix:
            base_id = f"{args.prefix}-{base_id}"

        props.update({
            "uuid": str(uuid.uuid4()),
            "latitude": float(lat),
            "longitude": float(lng),
            "city_code": city_code,
            "city_name": city_name,
            "dept_code": dept_code,
            "id": base_id,
            "manual_surge": props.get("manual_surge", 0),
            "available": props.get("available", True),
            "status": props.get("status", "active"),
        })

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(
            {"type": "FeatureCollection", "features": features},
            f,
            ensure_ascii=False,
            indent=2
        )



if __name__ == "__main__":
    main()