# -*- coding: utf-8 -*-
# Generate 01_poselki.md from villages_matched.json.

import json
import pathlib

BASE = str(pathlib.Path(__file__).parent)
vm = json.load(open(fr"{BASE}\villages_matched.json", encoding="utf-8"))

in_corr = [m for m in vm["matched"] if m["in_corridor"]]
near = [m for m in vm["matched"] if not m["in_corridor"] and m["dist_to_m9_km"] <= 9
        and (m["km_catalog"] == "" or m["km_catalog"] <= 38)]
no_poly = [u for u in vm["unmatched"]
           if u["km_catalog"] != "" and u["km_catalog"] <= 38]

# merge duplicate slugs in corridor (cluster names)
by_slug = {}
for m in in_corr:
    by_slug.setdefault(m["slug"], []).append(m)
rows = []
for slug, ms in by_slug.items():
    m0 = ms[0]
    names = " / ".join(dict.fromkeys(x["name"] for x in ms))
    cls = "элитный" if any(x["class"] == "E" for x in ms) else "бизнес"
    rows.append({
        "name": names, "cls": cls, "km": m0["km_catalog"], "district": m0["district"],
        "d": m0["dist_to_m9_km"], "lat": m0["lat"], "lon": m0["lon"], "slug": slug,
    })
rows.sort(key=lambda r: (float(r["km"]) if r["km"] != "" else 999, r["name"]))

n_e = sum(1 for r in rows if r["cls"] == "элитный")
n_b = len(rows) - n_e

def belt(km):
    if km == "" or float(km) <= 10: return "0–10"
    if float(km) <= 20: return "10–20"
    if float(km) <= 30: return "20–30"
    return "30–38"

lines = []
lines.append("# Посёлки бизнес-класса и элитные внутри полигона «Новая Рига»\n")
lines.append("Источник: каталог domzamkad.ru (Новорижское шоссе, бизнес-класс 250 / элитные 96, собраны 2026-09-10); ")
lines.append("координаты — полигоны посёлков с карты domzamkad; принадлежность полигону — геометрически (центроид ≤ 6,5 км от оси М-9, МКАД→ЦКАД).\n")
lines.append(f"**Итог: {len(rows)} посёлков внутри полигона** (элитных {n_e}, бизнес {n_b}); ещё {len(near)} — у кромки (6,5–9 км); {len(no_poly)} — включены по каталогу без координат (таблица B).\n")

lines.append("## Таблица A. Внутри полигона (проверено по координатам)\n")
lines.append("| Пояс | Посёлок | Класс | км от МКАД (каталог) | Район | ~км от оси М-9 |")
lines.append("|---|---|---|---|---|---|")
for r in rows:
    km = r["km"] if r["km"] != "" else "—"
    lines.append(f"| {belt(r['km'])} | {r['name']} | {r['cls']} | {km} | {r['district'] or '—'} | {r['d']} |")

lines.append("\n## Таблица B. У кромки коридора (6,5–9 км от оси, км ≤ 38)\n")
lines.append("| Посёлок | Класс | км от МКАД | ~км от оси |")
lines.append("|---|---|---|---|")
for m in sorted(near, key=lambda x: x["dist_to_m9_km"]):
    lines.append(f"| {m['name']} | {'элитный' if m['class']=='E' else 'бизнес'} | {m['km_catalog']} | {m['dist_to_m9_km']} |")

lines.append("\n## Таблица C. По каталогу Новорижского шоссе, ≤ 38 км, но без полигона на карте (не проверено геометрически)\n")
lines.append("Формально привязаны каталогом к Новорижскому шоссе; часть — Ильинское/Рублёвка-кластер у южной кромки. Для запуска — кандидаты «второй волны».\n")
lines.append("| Посёлок | Класс | км от МКАД | Район |")
lines.append("|---|---|---|---|")
for u in sorted(no_poly, key=lambda x: (float(x["km_catalog"]), x["name"])):
    lines.append(f"| {u['name']} | {'элитный' if u['class']=='E' else 'бизнес'} | {u['km_catalog']} | {u['district'] or '—'} |")

lines.append("\n## Кластеры для приоритизации\n")
lines.append("- **МКАД–10 км (Красногорск / Ильинка / Архангельское):** плотный элитный пояс — Резиденция Рублево, Береста, Строгинская бухта, Архангельское (-5, II), Генеральские дачи, Ильинский Квартал, Никольская слобода, Третья Охота, Oasis и др.")
lines.append("- **10–20 км (Павловское плато):** Павлово (+House, -2, Village), Николо-Урюпино, Ольгино, VillaNova, Маленькая Италия, Пенаты, Веледниково, Скипер + Миллениум Парк.")
lines.append("- **20–30 км (Павловская Слобода — Москва-река):** Павловская слобода, Княжье Озеро, Истринская слобода, Рига Клаб Хаус, Резиденция Монолит, Монтевиль, Гринфилд, Риверсайд, Шервуд, Мэдисон Парк (кромка), Грин Хилл, Белая гора, Старая Рига, Снегири — у самой развязки ЦКАД.")
lines.append("- Свыше 30 км и за ЦКАД (Духанино 43, Дачи Honka 43, Эссенс 43, Русский Лес 41 и далее) — вне полигона по границе «до ЦКАД».")

with open(fr"{BASE}\01_poselki.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"written 01_poselki.md: A={len(rows)} (E {n_e}/B {n_b}), near={len(near)}, catalog-only={len(no_poly)}")
