# P12. Выпилить Electron

Ветка: `feat/remove-electron`
Статус: в работе.

---

## Граница (по разведке)

- `DISABLE_AUTH` остаётся — это режим деплоя без лимитов (tg/03-quota.md),
  опора 6 тест-файлов, к Electron-рантайму не привязан.
- Cypress `--browser electron` в test-all.yml — их браузерный движок, не наше
  приложение.

## Фаза 1. Next.js фронт (эта часть)

Удалены все ветки `window.electron` из рантайм-кода, 8 файлов:

- `utils/api.ts` — `isElectronRuntime()`, прямое FastAPI-начало для electron;
  остался только query-override.
- `utils/providerUtils.ts` — `isElectronRuntime()`; дефолтный Ollama URL
  всегда `http://host.docker.internal:11434`, localhost-fallback остался
  (полезен и в docker, когда Ollama в том же контейнере).
- `components/OllamaConfig.tsx` — electron-плейсхолдер и подсказка.
- `app/(presentation-generator)/(dashboard)/dashboard/components/DashboardPage.tsx`
  — стейт `isElectronApp`, эффект, баннер «Update Presenton» (electron-only).
- `app/(presentation-generator)/presentation/components/PresentationHeader.tsx`
  — `exportViaIpc`, обе electron-ветки экспорта PPTX/PDF, `exportRuntime`
  в `trackExportLifecycle` (параметр и payload `export_runtime` удалены,
  аналитическое событие осталось).
- `presentation/components/chat/chat-utils.ts` и
  `documents-preview/components/DocumentPreviewPage.tsx` — ветки
  `window.electron.readFile`; чтение всегда через `/api/read-file`.
- `components/OnBoarding/OnboardingPresentonAccount.tsx` — обход
  about:blank-попапа для electron и fallback `window.open` — удалены,
  попап открывается всегда.
- `components/Auth/AuthGate.tsx` + `utils/serverAuth.ts` — сентинел-юзернейм
  `electron` переименован в `local` (это не Electron API, просто строка).
- `types/global.d.ts` — интерфейс `ElectronAPI` и `window.electron` удалены.
- Комментарии в `proxy.ts` и `utils/image-url-converter.ts` переписаны без
  упоминания electron.

## Что НЕ тронуто

- `image-url-converter.ts` — функция осталась, только комментарий; она
  нормализует `<img>` через общий резолвер и нужна docker/web.
- `trackExportLifecycle` — события аналитики сохранены, убран только
  параметр рантайма.
- Сервер (`PRESENTON_ELECTRON`, `is_presenton_electron_desktop`), CI-workflow
  electron, каталог `electron/` — отдельные фазы.

## Проверка

- `grep -rn "electron" servers/nextjs --include=*.ts,*.tsx` (без node_modules
  и .next) — 0 совпадений.
- `tsc --noEmit` — 0 ошибок.
- eslint по 13 затронутым файлам — 0 ошибок; 4 предупреждения, из них новое
  только `formatGitHubStars` unused (предупреждение существовало и до
  правок — функция стала неиспользуемой раньше, удаление вне скоупа фазы,
  помечено на P13-зачистку).
- `npm run build` — успешно.
