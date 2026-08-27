# P3. Endpoint превью слайдов картинками

Ветка: `feat/slide-preview-images`
Статус: в работе. Код пишется.

P2 закрыта и влита в `main` — см. `docs/progress/P2-telegram-auth.md`.

---

## Цель

Mini App показывает результат генерации картинками, не поднимая тяжёлый
редактор (konva, tiptap, recharts — 63 зависимости, canvas 1280px на экране
390px). Бэкенд уже умеет рендерить слайды в PNG без браузера пользователя —
нужна HTTP-обёртка.

## Что переиспользуем (менять не нужно)

- `export_presentation(id, title, "pptx", cookie_header)` —
  `utils/export_utils.py`, тот же хелпер, что у `/generate` и `/{id}/export`;
- `render_pptx_slides_to_images(pptx_path, ...)` —
  `templates/fonts_and_slides_preview.py:724`: PPTX → JSON → PNG, headless
  Chromium на бэкенде;
- `resolve_app_path_to_filesystem` уже проверяет владельца app_data-пути —
  чужой `pptx_path` вернёт None;
- nginx отдаёт `/app_data/exports/` с `auth_request` — URL для Mini App
  защищены той же кукой из P2;
- owner-скоупинг `sql_session.get(PresentationModel, id)` покрыт
  `with_loader_criteria`.

## Контракт

```
POST /api/v1/ppt/presentation/{id}/preview
Body: { "pptx_path": "/app_data/exports/users/.../deck.pptx" }   # опционально

200: { "slides": ["/app_data/exports/users/<uid>/previews/<pid>/slide-1.png", ...],
       "width": 1280, "height": 720 }
403: pptx_path не принадлежит владельцу
404: презентация не найдена / чужая
422: путь не .pptx
```

`pptx_path` опционален: бот имеет `path` из завершённой async-задачи и не
гоняет puppeteer повторно. Без него экспортируем свежий PPTX сами.

## План работ

1. Эндпоинт `api/v1/ppt/endpoints/slide_preview.py` + регистрация в
   `api/v1/ppt/router.py`. Кэш: PNG в `previews/<pid>/` свежее PPTX → отдаём
   готовые (рендер — это запуск Chromium).
2. Тесты: юнит (чужой путь → 403, не-pptx → 422), интеграция с фейковым
   `EXPORT_TASK_SERVICE` (образец — `tests/test_pptx_font_utils.py`).
3. Записки разработчику бота — отдельными файлами в `docs/tg/`:
   `01-auth-telegram.md` (контракт P2, уже работает), `02-slide-previews.md`
   (контракт этой задачи). `fyi.md` — исходный бриф, не редактируем.
4. Гейт `make check`, коммит, мерж в `main`, архив.

## Ограничения v1 (осознанные)

- Кастомные загруженные шрифты в превью не подтягиваем
  (`font_paths_for_install=[]`) — добавим, когда попросят.
- Превью только из PPTX; pdf-экспорт на входе → 422.
- Лимиты и квоты — P4.

## Открытый вопрос к разработчику бота (без изменений)

Как бот (не Mini App) получает сессию — у него нет initData. Записано в
`docs/tg/01-auth-telegram.md`.
