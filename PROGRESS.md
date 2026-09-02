# Progress

## Активная задача

No active task.

Последняя закрытая: P15 — Telegram WebApp авто-логин в веб-редакторе
(`components/Auth/AuthGate.tsx`): вход по initData через
`POST /api/v1/auth/telegram` без пароля + возврат на исходную ссылку
(редактор по ссылке из бота открывается без ручного логина). Контракт для
бота: кнопка «Открыть в редакторе» должна быть web_app-кнопкой. Подробности
в TASKS.md (P15).

Ранее: P14 — переход движка на DeepSeek (`LLM=deepseek`,
`DEEPSEEK_MODEL=deepseek-v4-flash`): `LLM_STRUCTURED_OUTPUTS` вернуть к
дефолту `true` (DeepSeek умеет structured outputs через tools в llmai),
`DISABLE_THINKING=true` для скорости; промпт outline требует JSON +
толерантный парсинг в эндпоинтах. Исходный флаг-фикс под b.ai остаётся в
коде (`docs/engine-response-format-issue.md`).

Ещё ранее: P10 — ребрендинг Yarex + hardening внутренней админки
(servers/nextjs): видимый ребренд + иконки, рестайл purple→blue,
телеметрия default off, регистрация закрыта по дизайну (setup 409).
Подробности: docs/progress/P10-yarex-rebrand-admin.md.

И ранее: T-04 — cookie samesite=none+secure за https-прокси (десктоп-Telegram),
мерж в main `c8c97f44`. Следующая связанная: T-09 — живой smoke против
движка (ждёт сервера/домена; вайтлист testers вписан в .env движка).
