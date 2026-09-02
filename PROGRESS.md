# Progress

## Активная задача

C1 — деплой на сервер (yarexlab.ru) через GitHub Actions. Режим уточнён
владельцем: **деплой только кнопкой** (workflow_dispatch, автозапуска нет),
тесты `test-all.yml` — только push в main (+dispatch), pull_request-триггер
убран. В deploy.yml добавлен шаг чистки старых образов на сервере после
успешного smoke (`docker rmi` старых `main-<sha>` + `docker image prune -f`).
Secrets (DEPLOY_SSH_*, DEPLOY_PATH) и docker login ghcr.io на сервере —
владелец настроил. Осталось: первый прогон кнопкой и проверка
pull/up/smoke/cleanup в Actions.

Последняя закрытая: P14 — обход HTTP 400 400001 от b.ai: флаг
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
