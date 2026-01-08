import os
import json
import uuid
import h3
from shapely.geometry import shape, Point


CITY_NAME = "Lille"
CITY_INSEE = "59350"
COMMUNES_GEOJSON = "docs/communes-59-nord.geojson"
RES = 8

OUTPUT_PREFIX = "lille"



def load_city_polygon():
    with open(COMMUNES_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    for feat in data["features"]:
        props = feat["properties"]
        code = props.get("code") or props.get("insee") or props.get("code_insee")

        if code == CITY_INSEE:
            geom = shape(feat["geometry"])
            return geom

    raise ValueError(f"Commune {CITY_NAME} ({CITY_INSEE}) not found")


def h3_cell_to_polygon(h):
    boundary = h3.cell_to_boundary(h)
    ring = [[lng, lat] for lat, lng in boundary]
    ring.append(ring[0])
    return [ring]




def main():
    print(f"Building H3 grid for {CITY_NAME}")

    city_geom = load_city_polygon()
    minx, miny, maxx, maxy = city_geom.bounds

    seed_lat = (miny + maxy) / 2
    seed_lng = (minx + maxx) / 2

    seed = h3.latlng_to_cell(seed_lat, seed_lng, RES)

    cells = set()
    MAX_K = 80

    for k in range(MAX_K + 1):
        cells.update(h3.grid_disk(seed, k))

    kept = []
    for h in cells:
        lat, lng = h3.cell_to_latlng(h)
        if city_geom.contains(Point(lng, lat)):
            kept.append(h)


    os.makedirs("docs", exist_ok=True)

    features = []
    for h in kept:
        lat, lng = h3.cell_to_latlng(h)
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": h3_cell_to_polygon(h),
            },
            "properties": {
                "uuid": str(uuid.uuid4()),
                "h3_index": h,
                "city_code": CITY_INSEE,
                "city_name": CITY_NAME,
                "latitude": lat,
                "longitude": lng,
                "manual_surge": 0,
                "available": True,
                "status": "active"
            }
        })

    geo = {
        "type": "FeatureCollection",
        "features": features
    }

    out = f"docs/{OUTPUT_PREFIX}_hex_grid.geojson"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(geo, f, indent=2, ensure_ascii=False)



if __name__ == "__main__":
    main()