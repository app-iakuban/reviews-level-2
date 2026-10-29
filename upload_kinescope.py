#!/usr/bin/env python3
"""Заливка роликов Level 2 в Kinescope + data/kinescope.json (key → embed_link).

Копия механики reviews-level-1/upload_kinescope.py. Тот же проект Kinescope, но тайтл
человекочитаемый: «L2 поток N — Имя» (по нему же идемпотентность: уже залитое не льём).
Токен: ~/.config/iakuban/secrets/kinescope-token (с правом Upload files).
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
TOKEN = (Path.home() / ".config/iakuban/secrets/kinescope-token").read_text().strip()
PARENT_ID = "192aea8b-a47d-45d4-83e5-5fd38c52d289"  # проект "My project"
VIDEOS_DIR = Path.home() / "Desktop" / "Отзывы выпускников Level 2"


def api(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def existing_videos():
    out, page = {}, 1
    while True:
        d = api(f"https://api.kinescope.io/v1/videos?per_page=100&page={page}")
        for v in d["data"]:
            out[v["title"]] = v
        if page * 100 >= d["meta"]["pagination"]["total"]:
            return out
        page += 1


def cohort_folder(n):
    hits = [p for p in VIDEOS_DIR.iterdir() if p.is_dir() and p.name.startswith(f"{n} поток")]
    assert len(hits) == 1, f"папка потока {n}: {hits}"
    return hits[0]


def upload(path, title):
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", "https://uploader.kinescope.io/v2/video",
         "-H", f"Authorization: Bearer {TOKEN}",
         "-H", f"X-Parent-ID: {PARENT_ID}",
         "-H", f"X-Video-Title: {title}",
         "-H", "Content-Type: video/mp4",
         "--data-binary", f"@{path}"],
        capture_output=True, text=True, timeout=1800)
    resp = json.loads(r.stdout)
    if "error" in resp:
        raise RuntimeError(f"{title}: {resp['error']}")
    return resp["data"]


def main():
    cohorts = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(DATA.glob("quotes_l2p*.json"))]
    have = existing_videos()
    links, todo = {}, []
    for c in cohorts:
        folder = cohort_folder(c["cohort"])
        for it in c["items"]:
            title = f'L2 поток {c["cohort"]} — {it["name"]}'
            if title in have:
                links[it["key"]] = have[title]["embed_link"]
            else:
                todo.append((it["key"], title, folder / it["file"]))
    print(f"уже в кинескопе {len(links)}, заливаем {len(todo)}", flush=True)
    for i, (key, title, path) in enumerate(todo, 1):
        assert path.exists(), f"нет файла {path}"
        for attempt in (1, 2):
            try:
                links[key] = upload(path, title)["embed_link"]
                print(f"[{i}/{len(todo)}] {title} ok", flush=True)
                break
            except Exception as e:
                print(f"[{i}/{len(todo)}] {title} {'FAIL' if attempt == 2 else 'retry'}: {e}", flush=True)
                time.sleep(5)
    (DATA / "kinescope.json").write_text(json.dumps(dict(sorted(links.items())), ensure_ascii=False, indent=1), encoding="utf-8")
    missing = [it["key"] for c in cohorts for it in c["items"] if it["key"] not in links]
    if missing:
        print("НЕ ЗАЛИТО:", ", ".join(missing), flush=True)
        sys.exit(1)
    print(f"ГОТОВО: {len(links)} роликов в Kinescope", flush=True)


if __name__ == "__main__":
    main()
