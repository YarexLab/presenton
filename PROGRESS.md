# Активная задача: P11 — удалить мёртвый код связи с фронтом

Ветка: `feat/remove-dead-layout-code`

**Цель.** Не путать себя и новых людей мёртвыми файлами прошлой архитектуры.

**Суть.** `api/v1/ppt/endpoints/layouts.py` (роутер не зарегистрирован,
хардкод `localhost:3000`), `templates/layout_code_validation.py` (не
вызывается), `http://localhost/api/template` в
`templates/get_layout_by_name.py`. Шаблоны теперь декларативный JSON —
генерация к фронту не обращается.

P10 закрыта — см. `docs/progress/P10-remove-trigger-webhook.md`.
