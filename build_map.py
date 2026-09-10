# -*- coding: utf-8 -*-
# Generate map.html (Leaflet, fully self-contained) with a no-JS fallback:
# header + full village table render as plain HTML even if JS is disabled,
# the interactive map is added on top when JS runs.

import json
import pathlib

BASE = pathlib.Path(__file__).parent

with open(BASE / "polygon.geojson", encoding="utf-8") as f:
    geo = json.load(f)
with open(BASE / "villages_matched.json", encoding="utf-8") as f:
    vm = json.load(f)

in_corr = [m for m in vm["matched"] if m["in_corridor"]]
near = [m for m in vm["matched"] if not m["in_corridor"] and m["dist_to_m9_km"] <= 9
        and (m["km_catalog"] == "" or m["km_catalog"] <= 38)]

# Deduplicate by slug (cluster entries like Pavlovo keep all names)
seen = set()
points = []
for m in sorted(in_corr, key=lambda x: (float(x["km_catalog"]) if x["km_catalog"] != "" else 999, x["name"])):
    if m["slug"] in seen:
        for p in points:
            if p["slug"] == m["slug"]:
                p["names"].append(m["name"])
        continue
    seen.add(m["slug"])
    points.append({"slug": m["slug"], "names": [m["name"]], "class": m["class"],
                   "km": m["km_catalog"], "d": m["dist_to_m9_km"], "lat": m["lat"], "lon": m["lon"]})

near_pts = []
seen_n = set()
for m in near:
    if m["slug"] in seen_n:
        continue
    seen_n.add(m["slug"])
    near_pts.append({"name": m["name"], "class": m["class"], "km": m["km_catalog"],
                     "d": m["dist_to_m9_km"], "lat": m["lat"], "lon": m["lon"]})

# ---- static fallback table (visible without JS) ----
def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

table_rows = []
for p in points:
    km = p["km"] if p["km"] != "" else "—"
    cls = "элитный" if p["class"] == "E" else "бизнес"
    table_rows.append(f"<tr><td>{esc(' / '.join(p['names']))}</td><td>{cls}</td><td>{km}</td></tr>")
static_table = "\n".join(table_rows)

near_html = ", ".join(esc(m["name"]) for m in sorted(near_pts, key=lambda x: x["km"] if x["km"] != "" else 999))

ne = sum(1 for p in points if p["class"] == "E")
nb = sum(1 for p in points if p["class"] == "B")
nn = len(near_pts)

leaflet_css = (BASE.parent.parent / "leaflet.css")
# assets were removed after previous build; re-embed from the committed copy if present
asset_dir = BASE.parent.parent
css_path = asset_dir / "leaflet.css"
js_path = asset_dir / "leaflet.js"
if not css_path.exists():
    css_path = BASE / "leaflet.css"
    js_path = BASE / "leaflet.js"

html = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Полигон Новая Рига — бизнес/элитные посёлки (МКАД→ЦКАД)</title>
<style>__LEAFLET_CSS__</style>
<style>
  body { margin: 0; font-family: Segoe UI, Arial, sans-serif; color: #222; }
  .page { max-width: 1100px; margin: 0 auto; padding: 16px 20px 60px; }
  h1 { font-size: 22px; margin: 12px 0 4px; }
  .sub { color: #555; font-size: 14px; margin-bottom: 12px; }
  #map { width: 100%; height: 70vh; min-height: 420px; border: 1px solid #ccc; border-radius: 8px; }
  table { border-collapse: collapse; font-size: 13px; width: 100%; margin-top: 8px; }
  th, td { border: 1px solid #ddd; padding: 4px 8px; text-align: left; }
  th { background: #f3f3f3; }
  tr:nth-child(even) td { background: #fafafa; }
  .legend { background: white; padding: 10px 14px; border-radius: 8px; box-shadow: 0 1px 6px rgba(0,0,0,.3); font-size: 13px; }
  .legend b { display:block; margin-bottom:4px; }
  .dot { display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:6px; vertical-align:middle; }
  .e { background:#c9a227; } .b { background:#2a6f97; } .n { background:#fff; border:2px solid #888; }
  #jserror { display:none; background:#fdecea; border:1px solid #f5c6cb; color:#7f1d1d; padding:10px 14px; border-radius:8px; margin:12px 0; font-size:14px; }
</style>
<script>__LEAFLET_JS__</script>
</head>
<body>
<div class="page">
  <h1>Полигон «Новая Рига»: МКАД → ЦКАД</h1>
  <div class="sub">Коридор ±6,5 км вдоль Новорижского шоссе (М-9). Внутри — __TOTAL__ посёлков
  бизнес-класса и элитных (элитных __NE__, бизнес __NB__), проверенных по координатам.
  Источник: domzamkad.ru, 2026-09-10.</div>
  <noscript><div class="sub" style="color:#b00">Интерактивная карта отключена: JavaScript не выполняется
  (предпросмотр в почте/мессенджере или старый браузер). Ниже — полная таблица посёлков.
  Чтобы увидеть карту, скачайте файл и откройте его в Chrome / Edge / Firefox.</div></noscript>
  <div id="jserror"></div>
  <div id="map"></div>
  <h2>Посёлки внутри полигона (__TOTAL__)</h2>
  <table id="villages">
    <tr><th>Посёлок</th><th>Класс</th><th>км от МКАД (каталог)</th></tr>
    __STATIC_TABLE__
  </table>
  <h2>У кромки коридора (__NN__)</h2>
  <p class="sub">__NEAR_LIST__</p>
</div>
<script>
window.onerror = function (msg, src, line) {
  var el = document.getElementById('jserror');
  el.style.display = 'block';
  el.innerHTML = '<b>Не удалось запустить карту</b> (ошибка: ' + msg + ').<br>Ниже — полная таблица посёлков, она не зависит от скриптов.';
  return false;
};
try {
  var geo = __GEO__;
  var pts = __PTS__;
  var nearPts = __NEAR__;
  var map = L.map('map');
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18, attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
  var polys = L.geoJSON(geo, {
    style: function (f) {
      if (f.geometry.type === 'Polygon') return { color: '#d7263d', weight: 2, fillColor: '#f8d6dd', fillOpacity: 0.12 };
      if (f.geometry.type === 'LineString') return { color: '#555', weight: 3, dashArray: '8 6' };
      return { color: '#111', weight: 1 };
    },
    pointToLayer: function (f, latlng) { return L.circleMarker(latlng, { radius: 5, color: '#111', fillOpacity: 1 }); }
  }).addTo(map);
  map.fitBounds(polys.getBounds().pad(0.12));
  for (var i = 0; i < pts.length; i++) {
    (function (p) {
      L.circleMarker([p.lat, p.lon], {
        radius: p.class === 'E' ? 7 : 5.5,
        color: '#3b3000', weight: 1,
        fillColor: p.class === 'E' ? '#c9a227' : '#2a6f97', fillOpacity: 0.95
      }).bindPopup('<b>' + p.names.join(' + ') + '</b><br>' +
        (p.class === 'E' ? 'элитный' : 'бизнес-класс') +
        (p.km !== '' ? ', ' + p.km + ' км от МКАД (каталог)' : '') +
        '<br>~' + p.d + ' км от оси М-9<br>' +
        '<a href="https://www.domzamkad.ru/villages/' + p.slug + '.html" target="_blank">domzamkad</a>').addTo(map);
    })(pts[i]);
  }
  for (var j = 0; j < nearPts.length; j++) {
    (function (p) {
      L.circleMarker([p.lat, p.lon], {
        radius: 4.5, color: '#666', weight: 1.5, fillColor: '#fff', fillOpacity: 0.8
      }).bindPopup('<b>' + p.name + '</b><br>' + (p.class === 'E' ? 'элитный' : 'бизнес-класс') +
        ' — у кромки полигона (~' + p.d + ' км от оси)').addTo(map);
    })(nearPts[j]);
  }
  var legend = L.control({ position: 'bottomright' });
  legend.onAdd = function () {
    var d = L.DomUtil.create('div', 'legend');
    d.innerHTML = '<b>Полигон «Новая Рига»: МКАД → ЦКАД</b>'
      + '<span class="dot e"></span>элитные — ' + __NE__L + '<br>'
      + '<span class="dot b"></span>бизнес-класс — ' + __NB__L + '<br>'
      + '<span class="dot n"></span>у кромки коридора — ' + __NN__L + '<br>'
      + '<span style="font-size:11px;color:#555">Красная зона — полигон; пунктир — ось М-9<br>Источник: domzamkad.ru, 2026-09-10</span>';
    return d;
  };
  legend.addTo(map);
} catch (e) {
  window.onerror(String(e));
}
</script>
</body>
</html>
"""

# Leaflet assets: cached next to the workspace root, or fallback in this folder
try:
    leaflet_css = css_path.read_text(encoding="utf-8")
    leaflet_js = js_path.read_text(encoding="utf-8")
except FileNotFoundError:
    raise SystemExit("leaflet.css / leaflet.js not found - re-download from "
                     "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/ before building")

html = (html.replace("__GEO__", json.dumps(geo, ensure_ascii=False))
            .replace("__PTS__", json.dumps(points, ensure_ascii=False))
            .replace("__NEAR__", json.dumps(near_pts, ensure_ascii=False))
            .replace("__NE__L", str(ne)).replace("__NB__L", str(nb)).replace("__NN__L", str(nn))
            .replace("__NE__", str(ne)).replace("__NB__", str(nb)).replace("__NN__", str(nn))
            .replace("__TOTAL__", str(len(points)))
            .replace("__STATIC_TABLE__", static_table)
            .replace("__NEAR_LIST__", near_html)
            .replace("__LEAFLET_CSS__", leaflet_css)
            .replace("__LEAFLET_JS__", leaflet_js))

out = BASE / "map.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written {out}; markers in-polygon: {len(points)} (elite {ne}, business {nb}), near: {nn}; "
      f"size {out.stat().st_size // 1024} KB")
