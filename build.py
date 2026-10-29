#!/usr/bin/env python3
"""Сборка /reviews/level-2/: мозаика hero + стена кружочков + карусель «было/стало» + проверка + FAQ.

Основа — reviews-level-1/build.py. Общий код (ссылки на профили коучей, даты, FAQ, замена
блоков) не копируется, а импортируется оттуда же, и карта коучей одна на обе страницы:
reviews-level-1/data/coaches.json (матч по key, затем по имени без учёта регистра и ё/е).

Данные: data/quotes_l2p*.json (items — ролики, cases — было/стало; ключ человека = item.key),
data/kinescope.json (key → embed), data/faq.json (блок «Как проверить» + FAQ).
Порядок: свежий выпуск сверху, внутри потока — порядок вручения (как в JSON).
Фото: assets/people/<key>.jpg, иначе кадр assets/posters/<key>.jpg.

Запуск:  python3 build.py [--media local|kinescope]
"""
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
INDEX = HERE / "index.html"
PEOPLE = HERE / "assets" / "people"
L1_DIR = HERE.parent / "reviews-level-1"

_spec = importlib.util.spec_from_file_location("reviews_l1_build", L1_DIR / "build.py")
l1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(l1)

MEDIA_MODE = "kinescope" if "--media" in sys.argv and "kinescope" in sys.argv else "local"

BASE_URL = "https://iakuban.com/reviews/level-2"
PAGE_URL = BASE_URL + "/"
PUBLISHED = "2026-10-29"

# Мозаика hero: 12 плиток (4×3 на десктопе, 3×4 на мобиле). Первыми — featured из quotes.
MOSAIC = [
    "l2p1_06_polina_kartashova", "l2p1_12_olga_timonina", "l2p1_08_andrey_konovalov", "l2p1_14_olga_yilmaz",
    "l2p1_01_leysan_akhmetshina", "l2p1_10_dmitriy_melikhov", "l2p1_13_ekaterina_volobueva", "l2p1_09_katerina_kurteva",
    "l2p1_04_viktoriya_dovgal", "l2p1_03_marina_doroshko", "l2p1_11_ekaterina_snetkova", "l2p1_07_mariya_kokourova",
]
AVATARS = MOSAIC
MALE = {"l2p1_08_andrey_konovalov", "l2p1_10_dmitriy_melikhov"}
COHORT_WORD = {1: "первого", 2: "второго", 3: "третьего", 4: "четвёртого", 5: "пятого"}


def load_cohorts():
    cs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(DATA.glob("quotes_l2p*.json"))]
    cs.sort(key=lambda c: c["graduation"], reverse=True)
    return cs


def kinescope_map():
    f = DATA / "kinescope.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def face_src(key):
    p = PEOPLE / f"{key}.jpg"
    rel = f"assets/people/{key}.jpg"
    if not p.exists():
        p = HERE / "assets" / "posters" / f"{key}.jpg"
        rel = f"assets/posters/{key}.jpg"
    return f"{rel}?v={int(p.stat().st_mtime)}"


def video_src(cohort, item, kmap):
    if MEDIA_MODE == "kinescope":
        if item["key"] not in kmap:
            raise SystemExit(f'нет kinescope-ссылки для {item["key"]}')
        return kmap[item["key"]]
    return f'media/p{cohort["cohort"]}/{item["file"]}'


def coach_slug(key, name):
    return l1.coach_slug(key, name)


def pcard(cohort, item, kmap):
    key = item["key"]
    name = html.escape(item["name"])
    quote = html.escape(item["quote"])
    src = html.escape(video_src(cohort, item, kmap))
    grad = cohort["graduation"]
    slug = coach_slug(key, item["name"])
    title, tag = name, ""
    if slug:
        title, tag_a = l1.coach_links(slug, name)
        tag = f"\n  {tag_a}"
    return (
        f'<article class="pcard reveal">\n'
        f'  <button class="pcircle" data-video="{src}" data-name="{name}" data-quote="«{quote}»" '
        f'aria-label="Видеоотзыв: {name}">'
        f'<img src="{face_src(key)}" alt="{name}" width="560" height="560" loading="lazy">'
        f'<span class="pplay" aria-hidden="true"></span>'
        f'</button>\n'
        f'  <h3>{title}</h3>{tag}\n'
        f'  <blockquote class="pquote">«{quote}»</blockquote>\n'
        f'  <footer class="pdur"><time datetime="{grad}">{l1.date_ru(grad)}</time></footer>\n'
        f'</article>'
    )


def ccard(case, cohort, index, kmap):
    """Кейс «было/стало». В L2 строки «было» может не быть (Коновалов: человек её не назвал),
    тогда показываем только «стало». Цитаты в кейсе нет: она уже под кружочком и в лайтбоксе."""
    key = case["key"]
    name = html.escape(case["name"])
    role = ("выпускник " if key in MALE else "выпускница ") + f'{COHORT_WORD.get(cohort["cohort"], "")} потока'
    slug = coach_slug(key, case["name"])
    title, tag = name, ""
    if slug:
        title, tag = l1.coach_links(slug, name)
    c, it = index[key]
    video = html.escape(video_src(c, it, kmap))
    rows = []
    if case.get("was"):
        rows.append(f'    <div class="row was"><dt class="sr-only">До программы</dt><dd>{html.escape(case["was"])}</dd></div>')
    rows.append(f'    <div class="row now"><dt class="sr-only">После программы</dt><dd>{html.escape(case["now"])}</dd></div>')
    return (
        f'<article class="ccard">\n'
        f'  <div class="ccard-top">'
        f'<img src="{face_src(key)}" alt="{name}" width="120" height="120" loading="lazy">'
        f'<div><h3 class="cname">{title}</h3><div class="crole">{role}</div>{tag}</div></div>\n'
        f'  <dl class="cab">\n' + "\n".join(rows) + '\n  </dl>\n'
        f'  <button class="cvideo" data-video="{video}" data-name="{name}" '
        f'data-quote="«{html.escape(it["quote"])}»"><span class="ic" aria-hidden="true"></span>'
        f'Смотреть видеоотзыв</button>\n'
        f'</article>'
    )


def jsonld(ordered, kmap, faq, ctx):
    items = []
    for pos, (c, it) in enumerate(ordered, 1):
        video = {
            "@type": "VideoObject",
            "name": f'Видеоотзыв: {it["name"]}',
            "description": it["quote"],
            "thumbnailUrl": f'{BASE_URL}/assets/posters/{it["key"]}.jpg',
            "uploadDate": l1.upload_iso(c["graduation"]),
            "duration": l1.dur_iso(it["duration"]),
            "inLanguage": "ru",
        }
        if MEDIA_MODE == "kinescope" and it["key"] in kmap:
            video["embedUrl"] = kmap[it["key"]]
        items.append({"@type": "ListItem", "position": pos, "item": video})
    org = {
        "@type": "EducationalOrganization",
        "@id": "https://iakuban.com/#organization",
        "name": "Iakuban Coaching Academy",
        "alternateName": [
            "Академия коучинга Алексея Якубана",
            "Академия Алексея Якубана",
            "Академия Якубана",
            "IAKUBAN COACHING ACADEMY S.L.",
        ],
        "url": "https://iakuban.com",
        "logo": "https://iakuban.com/logo-512.png",
        "sameAs": [
            "https://www.youtube.com/@iakuban",
            "https://t.me/iakuban",
            "https://yandex.ru/maps/org/86349660849/",
        ],
        "founder": {
            "@type": "Person",
            "@id": "https://iakuban.com/#person",
            "name": "Алексей Якубан",
            "alternateName": "Aleksei Iakuban",
            "description": "Основатель Iakuban Coaching Academy, коуч PCC ICF, 2 500+ часов коучинговой практики",
        },
    }
    page = {
        "@type": "CollectionPage",
        "@id": PAGE_URL + "#webpage",
        "name": "Отзывы выпускников: аккредитованная ICF программа, Level 2. Академия Алексея Якубана",
        "description": f"Отзывы выпускников второй ступени академии коучинга Алексея Якубана (аккредитованная ICF программа обучения, уровень Level 2, программа «Путь Алхимика»): {len(ordered)} видеоисторий, записанных в день вручения сертификатов, без сценария.",
        "url": PAGE_URL,
        "inLanguage": "ru",
        "datePublished": PUBLISHED,
        "about": {"@id": "https://iakuban.com/#organization"},
        "publisher": org,
        "isPartOf": {"@type": "WebSite", "@id": "https://iakuban.com/#website", "name": "Iakuban Coaching Academy", "url": "https://iakuban.com"},
        "mainEntity": {"@type": "ItemList", "numberOfItems": len(ordered), "itemListElement": items},
    }
    graph = [page]
    if faq:
        page["dateModified"] = faq["updated"]
        graph.append({
            "@type": "FAQPage",
            "@id": PAGE_URL + "#faq",
            "url": PAGE_URL + "#faq",
            "name": faq["faq_title"],
            "inLanguage": "ru",
            "isPartOf": {"@id": PAGE_URL + "#webpage"},
            "mainEntity": [
                {"@type": "Question", "name": it["q"],
                 "acceptedAnswer": {"@type": "Answer", "text": l1.strip_tags(l1.fill(it["a"], ctx))}}
                for it in faq["items"]
            ],
        })
    data = {"@context": "https://schema.org", "@graph": graph}
    return ('<script type="application/ld+json">\n'
            + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            + "\n</script>")


def main():
    l1.COACH_BY_KEY, l1.COACH_BY_NAME = l1.load_coaches()  # тот же файл карты, что у L1
    cohorts = load_cohorts()
    kmap = kinescope_map()
    faq = json.loads((DATA / "faq.json").read_text(encoding="utf-8"))

    index, ordered, cohort_of = {}, [], {}
    for c in cohorts:
        for it in c["items"]:
            index[it["key"]] = (c, it)
            ordered.append((c, it))

    mosaic_html = []
    for i, k in enumerate(MOSAIC):
        c, it = index[k]
        name = html.escape(it["name"])
        mosaic_html.append(
            f'<button class="mtile" data-video="{html.escape(video_src(c, it, kmap))}" data-name="{name}" '
            f'data-quote="«{html.escape(it["quote"])}»" aria-label="Видеоотзыв: {name}">'
            f'<img src="{face_src(k)}" alt="{name}" width="560" height="560" '
            f'{"" if i < 8 else "loading=lazy "}>'
            f'<span class="mname" aria-hidden="true">{name}</span>'
            f'<span class="mplay" aria-hidden="true"></span>'
            f'</button>'
        )
    grid_html = "\n".join(pcard(c, it, kmap) for c, it in ordered)
    cases_html = "\n".join(ccard(cs, c, index, kmap) for c in cohorts for cs in c.get("cases", []))
    avatars_html = "\n".join(
        f'<img src="{face_src(k)}" alt="" width="52" height="52" loading="lazy">' for k in AVATARS)

    total = len(ordered)
    ctx = {
        "total": str(total),
        "total_word": l1.plural(total, "видеоотзыв", "видеоотзыва", "видеоотзывов"),
        "updated_time": f'<time datetime="{faq["updated"]}">{l1.date_ru(faq["updated"])} года</time>',
    }
    rb = l1.replace_block
    src = INDEX.read_text(encoding="utf-8")
    src = rb(src, "<!-- MOSAIC:START -->", "<!-- MOSAIC:END -->", "\n".join(mosaic_html))
    src = rb(src, "<!-- GRID:START -->", "<!-- GRID:END -->", grid_html)
    src = rb(src, "<!-- CASES:START -->", "<!-- CASES:END -->", cases_html)
    src = rb(src, "<!-- AVATARS:START -->", "<!-- AVATARS:END -->", avatars_html)
    src = rb(src, "<!-- VERIFY:START -->", "<!-- VERIFY:END -->", l1.verify_html(faq, ctx))
    src = rb(src, "<!-- FAQ:START -->", "<!-- FAQ:END -->", l1.faq_html(faq, ctx))
    for fid in ("verify-title", "verify-intro", "faq-title", "faq-intro"):
        val = html.escape(faq[fid.replace("-", "_")])
        src = re.sub(rf'(id="{fid}"[^>]*>)[^<]*', lambda m, v=val: m.group(1) + v, src)
    src = rb(src, "<!-- JSONLD:START -->", "<!-- JSONLD:END -->", jsonld(ordered, kmap, faq, ctx))
    src = re.sub(r'(data-stat="total"[^>]*>)[^<]*', rf"\g<1>{total}", src)
    src = re.sub(r"\d+ видеоистори", f"{total} видеоистори", src)
    src = re.sub(r"\d+ видео выпускников", f"{total} видео выпускников", src)
    INDEX.write_text(src, encoding="utf-8")

    n_wall = sum(1 for c, it in ordered if coach_slug(it["key"], it["name"]))
    n_cases = sum(1 for c in cohorts for cs in c.get("cases", []) if coach_slug(cs["key"], cs["name"]))
    n_photo = sum(1 for k in index if (PEOPLE / f"{k}.jpg").exists())
    print(f"ok: total={total}, mosaic={len(MOSAIC)}, фото={n_photo}, фолбэк-постер={total - n_photo}, "
          f"media={MEDIA_MODE}, коучи: стена={n_wall} кейсы={n_cases}, faq={len(faq['items'])}")


if __name__ == "__main__":
    main()
