# -*- coding: utf-8 -*-
# Generate map.html (Leaflet) with the corridor polygon, M-9 axis and village markers.

import json
import pathlib

BASE = str(pathlib.Path(__file__).parent)

with open(fr"{BASE}\polygon.geojson", encoding="utf-8") as f:
    geo = json.load(f)
with open(fr"{BASE}\villages_matched.json", encoding="utf-8") as f:
    vm = json.load(f)

in_corr = [m for m in vm["matched"] if m["in_corridor"]]
near = [m for m in vm["matched"] if not m["in_corridor"] and m["dist_to_m9_km"] <= 9
        and (m["km_catalog"] == "" or m["km_catalog"] <= 38)]

# Deduplicate by slug (cluster entries like Pavlovo keep the first name)
seen = set()
points = []
for m in sorted(in_corr, key=lambda x: (float(x["km_catalog"]) if x["km_catalog"] != "" else 999, x["name"])):
    key = m["slug"]
    if key in seen:
        for p in points:
            if p["slug"] == key:
                p["names"].append(m["name"])
        continue
    seen.add(key)
    points.append({"slug": key, "names": [m["name"]], "class": m["class"],
                   "km": m["km_catalog"], "d": m["dist_to_m9_km"], "lat": m["lat"], "lon": m["lon"]})

near_pts = []
seen_n = set()
for m in near:
    if m["slug"] in seen_n:
        continue
    seen_n.add(m["slug"])
    near_pts.append({"name": m["name"], "class": m["class"], "km": m["km_catalog"],
                     "d": m["dist_to_m9_km"], "lat": m["lat"], "lon": m["lon"]})

html = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Полигон Новая Рига — бизнес/элитные посёлки (МКАД→ЦКАД)</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  body { margin: 0; font-family: Segoe UI, Arial, sans-serif; }
  #map { width: 100vw; height: 100vh; }
  .legend { background: white; padding: 10px 14px; border-radius: 8px; box-shadow: 0 1px 6px rgba(0,0,0,.3); font-size: 13px; }
  .legend b { display:block; margin-bottom:4px; }
  .dot { display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:6px; vertical-align:middle; }
  .e { background:#c9a227; } .b { background:#2a6f97; } .n { background:#fff; border:2px solid #888; }
</style>
</head>
<body>
<div id="map"></div>
<script>
const geo = __GEO__;
const pts = __PTS__;
const nearPts = __NEAR__;
const map = L.map('map');
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18, attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);
const polys = L.geoJSON(geo, {
  style: f => f.geometry.type === 'Polygon'
    ? { color: '#d7263d', weight: 2, fillColor: '#f8d6dd', fillOpacity: 0.12 }
    : f.geometry.type === 'LineString'
      ? { color: '#555', weight: 3, dashArray: '8 6' }
      : { color: '#111', weight: 1 },
  pointToLayer: (f, latlng) => L.circleMarker(latlng, { radius: 5, color: '#111', fillOpacity: 1 })
}).addTo(map);
map.fitBounds(polys.getBounds().pad(0.12));
for (const p of pts) {
  L.circleMarker([p.lat, p.lon], {
    radius: p.class === 'E' ? 7 : 5.5,
    color: '#3b3000', weight: 1,
    fillColor: p.class === 'E' ? '#c9a227' : '#2a6f97', fillOpacity: 0.95
  }).bindPopup(`<b>${p.names.join(' + ')}</b><br>${p.class === 'E' ? 'элитный' : 'бизнес-класс'}${p.km !== '' ? ', ' + p.km + ' км от МКАД (каталог)' : ''}<br>~${p.d} км от оси М-9<br><a href="https://www.domzamkad.ru/villages/${p.slug}.html" target="_blank">domzamkad</a>`).addTo(map);
}
for (const p of nearPts) {
  L.circleMarker([p.lat, p.lon], {
    radius: 4.5, color: '#666', weight: 1.5, fillColor: '#fff', fillOpacity: 0.8
  }).bindPopup(`<b>${p.name}</b><br>${p.class === 'E' ? 'элитный' : 'бизнес-класс'} — у кромки полигона (~${p.d} км от оси)`).addTo(map);
}
const legend = L.control({ position: 'bottomright' });
legend.onAdd = () => {
  const d = L.DomUtil.create('div', 'legend');
  d.innerHTML = '<b>Полигон «Новая Рига»: МКАД → ЦКАД</b>'
    + '<span class="dot e"></span>элитные — ' + __NE__ + '<br>'
    + '<span class="dot b"></span>бизнес-класс — ' + __NB__ + '<br>'
    + '<span class="dot n"></span>у кромки коридора — ' + __NN__ + '<br>'
    + '<span style="font-size:11px;color:#555">Красная зона — полигон; пунктир — ось М-9<br>Источник: domzamkad.ru, 2026-09-10</span>';
  return d;
};
legend.addTo(map);
</script>
</body>
</html>
"""

ne = sum(1 for p in points if p["class"] == "E")
nb = sum(1 for p in points if p["class"] == "B")
nn = len(near_pts)
html = (html.replace("__GEO__", json.dumps(geo, ensure_ascii=False))
            .replace("__PTS__", json.dumps(points, ensure_ascii=False))
            .replace("__NEAR__", json.dumps(near_pts, ensure_ascii=False))
            .replace("__NE__", str(ne)).replace("__NB__", str(nb)).replace("__NN__", str(nn)))
out = fr"{BASE}\map.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written {out}; markers in-polygon: {len(points)} (elite {ne}, business {nb}), near: {nn}")
