# Progress

## Активная задача

No active task.

Последняя закрытая: P16 (M4, движковая часть) — editor-state (undo/redo),
op add_element (text/image/rectangle), op set_data (text-list/chart), rich
text-разметка **/*/<latex> в set_text, ui и complex-предпросмотр в
editor-view. Подробности: docs/tg/04-editor-api.md.

Последняя закрытая: P15 — редакторский REST для редактирования из
Telegram Mini App (слайд-операции duplicate/delete/add/order/layout-catalog,
editor-view + editor-ops, preview refresh). `make check` зелёный (fastapi
877 passed). Подробности: docs/progress/P15-deck-editor-api.md.

Ранее: C1 — деплой на сервер (yarexlab.ru) через GitHub
Actions: кнопка workflow_dispatch (build → `ghcr.io/yarexlab/presenton:
main-<sha>` → SSH `git pull` + compose pull/up → smoke `/api/v1/auth/status`
→ чистка старых образов), тесты — только push в main. Проверено живым
деплоем 2026-09-02. Откат — кнопкой с `deploy_tag`. Подробности:
docs/progress/C1-deploy-github-actions.md.

Ранее: P14 — обход HTTP 400 400001 от b.ai: флаг
`LLM_STRUCTURED_OUTPUTS=false` (не слать `response_format`/`json_schema`,
парсить JSON из текста; гейты в `get_generate_kwargs` и
`templates/v2/generation.py`, толерантный `extract_structured_content`).
Источник: инцидент 2026-09-01 (`docs/engine-response-format-issue.md`),
задача в TASKS.md репо presenton. На сервере: выставить
`LLM_STRUCTURED_OUTPUTS=false` в `.env` движка и перезапустить контейнер.

Ранее: P10 — ребрендинг Yarex + hardening внутренней админки
(servers/nextjs): видимый ребренд + иконки, рестайл purple→blue,
телеметрия default off, регистрация закрыта по дизайну (setup 409).
Подробности: docs/progress/P10-yarex-rebrand-admin.md.

Ещё ранее: T-04 — cookie samesite=none+secure за https-прокси (десктоп-Telegram),
мерж в main `c8c97f44`. Следующая связанная: T-09 — живой smoke против
движка (ждёт сервера/домена; вайтлист testers вписан в .env движка).
