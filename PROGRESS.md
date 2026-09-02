# Progress

## Активная задача

C1 — деплой на сервер (yarexlab.ru) через GitHub Actions. Код готов
(`f198b424`): `.github/workflows/deploy.yml` (build из main →
`ghcr.io/yarexlab/presenton:main-<sha>` → деплой по SSH `compose pull && up -d`
→ smoke `GET /api/v1/auth/status` на `127.0.0.1:50521`; откат —
workflow_dispatch с `deploy_tag=main-<sha>`), `docker-compose.server.yml`
добавлен `image:` (build остался fallback'ом), tsc добавлен в `test-all.yml`,
апстримовские `docker-release.yml`/`sync-releaes-to-r2.yml` удалены.

Осталось (на стороне владельца/сервера, не код):
1. Secrets в GitHub: `DEPLOY_SSH_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_SSH_KEY`,
   `DEPLOY_PATH` (каталог репо на сервере).
2. Разово на сервере: `docker login ghcr.io` (PAT c read:packages) — пакет
   приватный; либо сделать пакет public.
3. Settings → Environments → production: при желании добавить Required
   reviewer (тогда деплой ждёт approval).
4. Первый прогон: push в main → проверить в Actions, что pull/up/smoke
   зелёные.

Важно: до настройки secrets деплой-job на каждый пуш в main будет падать
(видно в Actions) — build при этом зелёный.

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
