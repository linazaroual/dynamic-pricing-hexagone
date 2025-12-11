import json
import uuid
from shapely.geometry import shape, Point
from tqdm import tqdm
import h3

GRID = "docs/idf_hex_grid_res8.geojson"
COMMUNES = "docs/communes_idf.geojson"
OUTPUT = "docs/idf_hex_grid_final.json"


def load_communes():
    with open(COMMUNES, "r", encoding="utf-8") as f:
        data = json.load(f)

    communes = []
    for feat in data["features"]:
        props = feat["properties"]

        code = props.get("code") or props.get("insee") or props.get("code_insee")
        name = props.get("nom") or props.get("name")
        dept = code[:2]  

        communes.append({
            "code": code,
            "name": name,
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
    with open(GRID, "r", encoding="utf-8") as f:
        grid = json.load(f)
    features = grid["features"]

    communes = load_communes()

    for feat in tqdm(features):
        h3_index = feat["properties"]["h3_index"]
        lat, lng = h3.cell_to_latlng(h3_index)

        commune = find_commune(lat, lng, communes)

        if commune:
            city_code = commune["code"]
            city_name = commune["name"]
            dept_code = commune["dept"]
        else:
            city_code = "00000"
            city_name = "Hors IDF"
            dept_code = "00"

        feat["properties"].update({
            "uuid": str(uuid.uuid4()),
            "latitude": lat,
            "longitude": lng,
            "city_code": city_code,
            "city_name": city_name,
            "dept_code": dept_code,
            "id": f"{dept_code}-{city_code}",
            "manual_surge": 0,
            "available": True,
            "status": "active"
        })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features},
                  f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

    