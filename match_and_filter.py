# -*- coding: utf-8 -*-
# Match catalog village names to domzamkad map-polygon slugs, test centroids
# against the M-9 corridor (MKAD -> CKAD interchange), output JSON + report.

import difflib
import json
import math
import pathlib
import re
import statistics
import sys

sys.path.insert(0, r"C:\born_lion\Cloude\research_2026-09_novaya_riga_polygon")
from catalog_data import BUSINESS_P1, BUSINESS_P2_7, ELITE

MAP_JSON = str(pathlib.Path(__file__).parent / "data" / "domzamkad_map_h3_full.json")
OUT = r"C:\born_lion\Cloude\research_2026-09_novaya_riga_polygon\villages_matched.json"

# Manual name -> slug bindings (verified against slug list 2026-09-10).
ALIASES = {
    "Береста": "beresta",
    "Береста-2": "beresta",
    "Резиденция Рублево": "rezidentsiya-rublevo",
    "Строгинская бухта": "stroginskaya-buhta",
    "Берег столицы": "bereg-stolitcy",
    "Архангельское-5": "arhangelskoe5",
    "Архангельское II": "arhangelskoe-2",
    "Архангельское (эл)": "arhangelskoe-2",
    "Гринфилд": "greenfield",
    "Риверсайд": "riverside",
    "Шервуд": "sherwood",
    "Нахабино Кантри Клаб": "nahabino-country-club",
    "Ильинское Клаб Хаус": "ilinskoe-klab-haus",
    "Голландский квартал": "gollandskij-kvartal",
    "Грибаново": "gribanovo",
    "Никологорские дачи": "nikologorskie-dachy",
    "Роща": "rosha",
    "Манихино": "manihino",
    "Новорижский": "novorizhsky",
    "Истра Кантри Клаб": "istra-country-club",
    "Аист": "aist",
    "Маслово Forest Club": "maslovo-forest-club",
    "Старый Свет": "stary-svet2",
    "Старый Свет-2": "stary-svet2",
    "Славково": "slavkovo",
    "Подмосковные просторы": "podmoskovnie-prostory",
    "Тимошкино Парк": "timoshkino",
    "Тимошкино": "timoshkino",
    "Миллениум парк": "millenium-park",
    "Монтевиль": "monteville",
    "Грин Хилл": "greenhill",
    "Княжье Озеро": "knyazhe-ozero",
    "Резиденция Монолит": "rezidentsiya-monolit",
    "Павловская слобода (эл)": "pavlovskaya-sloboda",
    "Истринская слобода": "ustrinskaya-sloboda",
    "Резиденции Бенилюкс": "residentsii-benilux",
    "Близкий берег": "blizkij-bereg",
}
# Names that must stay unmatched (no polygon on the map / wrong candidates).
NO_MATCH = {
    "Лес и Река", "Лёс", "Новоархангельское", "Слобода", "Ривьера на Истре",
    "Дубрава", "Русская деревня", "Скоково Парк", "Аисты", "Crystal Istra",
    "Нахабино (Зеленый шум-2)", "Озерна Residence".replace("Озерна", "Ozerna"),
}

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ы": "y", "э": "e", "ю": "u", "я": "ya",
}


def translit(s: str) -> str:
    return "".join(TRANSLIT.get(c, c) for c in s.lower() if TRANSLIT.get(c, c).isalnum() or c.isascii())


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def centroid(geom) -> tuple[float, float]:
    ring = geom["coordinates"][0]
    return statistics.mean(p[0] for p in ring), statistics.mean(p[1] for p in ring)


# M-9 axis anchors (lon, lat), MKAD -> CKAD, verified against domzamkad polygons
# and OSM Nominatim landmarks:
AXIS_LONLAT = [
    (37.4080, 55.8150),  # MKAD junction (Krasnopresnensky prospekt continuation, Strogino)
    (37.2555, 55.8245),  # Opalikha
    (37.1771, 55.8350),  # Nakhabino south (A-107 interchange zone)
    (37.1000, 55.8330),  # midway
    (37.0285, 55.8304),  # Pavlovskaya Sloboda
    (37.0000, 55.8600),  # bend north-west
    (37.0100, 55.8800),  # CKAD x M-9 interchange (approx, +/-1.5 km)
]
HALF_KM = 6.5


def dist_to_axis(lon: float, lat: float) -> float:
    best = 1e9
    for i in range(len(AXIS_LONLAT) - 1):
        (x1, y1), (x2, y2) = AXIS_LONLAT[i], AXIS_LONLAT[i + 1]
        kx = 111.32 * math.cos(math.radians(lat))
        ky = 111.32
        ax, ay, bx, by, px, py = x1 * kx, y1 * ky, x2 * kx, y2 * ky, lon * kx, lat * ky
        dx, dy = bx - ax, by - ay
        t = 0.0 if (dx == dy == 0) else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(px - (ax + t * dx), py - (ay + t * dy)))
    return best


def main() -> None:
    data = json.load(open(MAP_JSON, encoding="utf-8"))
    polys: dict[str, tuple[float, float]] = {}
    for e in data:
        slug = e["properties"]["url"].split("/")[1]
        lat, lon = centroid(e["geometry"])
        polys[slug] = (lat, lon)
    slug_norms = {s: norm(s) for s in polys}

    rows = BUSINESS_P1 + BUSINESS_P2_7 + ELITE
    slugs_iter = list(polys)
    matched, unmatched = [], []
    for name, km, district, roads, cls in rows:
        slug = None
        if name in NO_MATCH:
            slug = None
        elif name in ALIASES:
            slug = ALIASES[name] if ALIASES[name] in polys else None
        else:
            n = translit(name)
            for s, sn in slug_norms.items():
                if n and (n == sn or n in sn or sn in n):
                    slug = s
                    break
            if not slug:
                cands = difflib.get_close_matches(n, list(slug_norms.values()), n=1, cutoff=0.85)
                if cands:
                    slug = next(s for s in slugs_iter if norm(s) == cands[0])
        if slug:
            lat, lon = polys[slug]
            d = dist_to_axis(lon, lat)
            matched.append({
                "name": name, "slug": slug, "class": cls, "km_catalog": km,
                "district": district, "roads": roads,
                "lat": round(lat, 5), "lon": round(lon, 5),
                "dist_to_m9_km": round(d, 2), "in_corridor": d <= HALF_KM,
            })
        else:
            unmatched.append({"name": name, "km_catalog": km, "class": cls, "district": district})

    json.dump({"matched": matched, "unmatched": unmatched}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    in_c = [m for m in matched if m["in_corridor"]]
    near = [m for m in matched if not m["in_corridor"] and m["dist_to_m9_km"] <= 9 and (m["km_catalog"] == "" or m["km_catalog"] <= 38)]
    print(f"matched: {len(matched)}/{len(rows)}   in corridor(<= {HALF_KM}): {len(in_c)}   near-belt: {len(near)}")
    print("\n-- IN CORRIDOR --")
    for m in sorted(in_c, key=lambda x: (float(x["km_catalog"]) if x["km_catalog"] != "" else 999, x["name"])):
        print(f"{m['class']} {m['name'][:30]:32s} km={str(m['km_catalog']):>3s} d={m['dist_to_m9_km']:>5.1f}  ({m['lat']},{m['lon']}) {m['district']}")
    print("\n-- NEAR BELT (6.5-9 km, catalog <=38) --")
    for m in sorted(near, key=lambda x: x["dist_to_m9_km"]):
        print(f"{m['class']} {m['name'][:30]:32s} km={str(m['km_catalog']):>3s} d={m['dist_to_m9_km']:>5.1f}")
    print("\n-- UNMATCHED (no polygon) --")
    for u in sorted(unmatched, key=lambda x: (float(x["km_catalog"]) if x["km_catalog"] != "" else 999)):
        print(f"{u['class']} {u['name'][:40]:42s} km={u['km_catalog']}")


if __name__ == "__main__":
    main()
