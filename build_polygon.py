# -*- coding: utf-8 -*-
# Build the Novaya Riga (M-9) test-launch corridor polygon: MKAD -> CKAD,
# +/- 6.5 km around the verified highway axis. Output: polygon.geojson.

import json
import math

OUT = r"C:\born_lion\Cloude\research_2026-09_novaya_riga_polygon\polygon.geojson"

# (lon, lat) anchors, same as match_and_filter.py AXIS_LONLAT
AXIS = [
    (37.4080, 55.8150),  # MKAD junction
    (37.2555, 55.8245),  # Opalikha
    (37.1771, 55.8350),  # Nakhabino south
    (37.1000, 55.8330),  # midway
    (37.0285, 55.8304),  # Pavlovskaya Sloboda
    (37.0000, 55.8600),  # bend
    (37.0100, 55.8800),  # CKAD x M-9 interchange
]
HALF_KM = 6.5


def offset(lon, lat, bearing_deg, dist_km):
    rad = math.radians(bearing_deg)
    lat2 = lat + dist_km * math.cos(rad) / 111.32
    lon2 = lon + dist_km * math.sin(rad) / (111.32 * math.cos(math.radians(lat)))
    return lon2, lat2


def corridor(axis, half_km):
    left, right = [], []
    for i, (lon, lat) in enumerate(axis):
        if i == 0:
            dx, dy = axis[1][0] - lon, axis[1][1] - lat
        elif i == len(axis) - 1:
            dx, dy = lon - axis[-2][0], lat - axis[-2][1]
        else:
            dx, dy = axis[i + 1][0] - axis[i - 1][0], axis[i + 1][1] - axis[i - 1][1]
        kx = 111.32 * math.cos(math.radians(lat))
        tx, ty = dx * kx, dy * 111.32
        n = math.hypot(tx, ty)
        tx, ty = tx / n, ty / n
        bearing = math.degrees(math.atan2(-ty, tx))
        left.append(offset(lon, lat, bearing, half_km))
        right.append(offset(lon, lat, bearing + 180, half_km))
    return left + right[::-1] + [left[0]]


def main():
    ring = corridor(AXIS, HALF_KM)
    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Novaya Riga test polygon: MKAD->CKAD, +/-6.5 km",
                    "ru": "Полигон Новая Рига: МКАД->ЦКАД, коридор 13 км",
                },
                "geometry": {"type": "Polygon", "coordinates": [[[round(x, 5), round(y, 5)] for x, y in ring]]},
            },
            {
                "type": "Feature",
                "properties": {"name": "M-9 axis (approx)", "ru": "Ось Новорижского шоссе (приблизительно)"},
                "geometry": {"type": "LineString", "coordinates": [[round(x, 5), round(y, 5)] for x, y in AXIS]},
            },
            {
                "type": "Feature",
                "properties": {"name": "CKAD x M-9 interchange (approx)", "ru": "Развязка ЦКАД x Новорижское (приблизительно)"},
                "geometry": {"type": "Point", "coordinates": [37.01, 55.88]},
            },
            {
                "type": "Feature",
                "properties": {"name": "MKAD x M-9 junction (approx)", "ru": "Развязка МКАД x Новорижское (приблизительно)"},
                "geometry": {"type": "Point", "coordinates": [37.408, 55.815]},
            },
        ],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=1)
    print(f"written {OUT}; ring vertices: {len(ring)}")


if __name__ == "__main__":
    main()
