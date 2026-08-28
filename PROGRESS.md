# Активная задача: P12 — выпилить Electron

Ветка: `feat/remove-electron`

**Цель.** Не тащить неподдерживаемый рантайм: десктоп не нужен.

**Суть.** Удалить `electron/` (89 файлов), `PRESENTON_ELECTRON_BUILD` в
`next.config.mjs`, ветки `window.electron` в 8 файлах фронта, CI-workflow
electron, `PRESENTON_ELECTRON`/`is_presenton_electron_desktop` в бэке.

**Граница (по разведке):** `DISABLE_AUTH` остаётся — это режим деплоя без
лимитов (tg/03-quota.md) + опора 6 тест-файлов, к Electron-рантайму не
привязан. Cypress `--browser electron` в test-all.yml — это их браузерный
движок, не наше приложение.

**Прогресс.** Фаза 1 (Next.js фронт) готова: 0 упоминаний electron в
`servers/nextjs`, tsc/build зелёные. Детали —
`docs/progress/P12-remove-electron.md`. Дальше: бэкенд
(`PRESENTON_ELECTRON`), CI-workflow, каталог `electron/`.
