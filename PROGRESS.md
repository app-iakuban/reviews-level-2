# Видеоотзывы выпускников «Пути Алхимика» — iakuban.com/reviews/level-2/

Снимок 29.10.2026. Статус: **живая на проде**, поток 1 (14 роликов). Канон решений и грабли —
`../reviews-level-1/PROGRESS.md` (решения Алексея 1–13 действуют и здесь).

## Структура
Hero (h1 «Видеоотзывы выпускников «Пути Алхимика»», CTA «Записаться на собеседование» — тот же
префилл, что на /icf-level-2/; «О программе «Путь Алхимика»»; ссылка на отзывы L1; мозаика 12)
→ стена 14 кружочков в порядке вручения → карусель «было/стало» (9 кейсов из quotes) →
«Как проверить академию» (verify скопирован из L1 faq.json) → FAQ 4 вопроса → CTA-полоса →
тёмный финал с аватарками → подвал.

## Как устроено
- `build.py` импортирует функции из `../reviews-level-1/build.py` (coach_links, даты, FAQ,
  replace_block) и читает ту же карту `../reviews-level-1/data/coaches.json`. Не копировать.
- Данные: `data/quotes_l2p1.json` (копия из `Mascotta/_media/2026-10-29_vypusknoy_l2/`),
  `data/kinescope.json`, `data/faq.json`. Ключ человека = `item.key` (`l2p1_NN_имя`).
- Кейс без «было» (Коновалов) рендерится одной строкой «стало». Цитаты в кейсе нет.
- Kinescope: `upload_kinescope.py`, тайтлы «L2 поток N — Имя» (идемпотентно по тайтлу).
- Фото: 10 из `../reviews-level-1/assets/people/` (та же обработка), 4 новых из Telegram
  (Довгаль, Снеткова, Волобуева, Йылмаз; `photos_raw/_manifest.json`). Постеры = кадр ролика.
- OG: `assets/og-src.html` → headless Chrome → `assets/og.jpg` (вечнозелёная, без чисел).
- Коучи залинкованы: стена 4 (Карташова, Дорошко, Снеткова, Волобуева), кейсы 3.

## Деплой
Зеркало `../../deploy/reviews/level-2/` = github.com/app-iakuban/reviews-level-2.
Path-домен Dokploy `/reviews/level-2` (domainId `1AWCVp_FivYd2FlwPgF3F`), папка сервера
`/etc/dokploy/landings/reviews/level-2/`. Порядок: `python3 build.py --media kinescope` →
`rsync -a ./ ../../deploy/reviews/level-2/ --exclude .git` → коммит/пуш → `bash deploy/publish.sh reviews/level-2`.
В sitemap — `seoRoutes.ts` (коммит b2bc72a4).

## Новый поток
quotes_l2pN.json (+ cases) → фото → `python3 upload_kinescope.py` → обновить MOSAIC в build.py
→ сборка → зеркало → publish. Поправить тексты hero/«Истории выпускников» (там дата и «первый поток»).

## Грабли
- `.ccard` обязан быть `position:relative`: `dt.sr-only` (absolute) иначе вылезает за карусель и
  раздувает документ, на мобиле layout-вьюпорт уезжал до 1500px (было и на L1, исправлено 29.10).
- Неполный последний ряд стены (14 = 3×4 + 2) центрируется CSS при 4 колонках.
- В меню шапки отдельного пункта «Отзывы» нет (в меню только программы) — не добавляли.
