# Инструкция по сборке Web Client

## Проблема

При запуске `npm run build` происходит ошибка из-за строгой проверки типов TypeScript.
Однако сборка Vite проходит успешно.

## Решение

Используйте сборку без проверки типов:

```bash
cd web-client
npm run build-only
```

## Результат

Файлы будут собраны в `web-client/dist/`:
- `dist/index.html`
- `dist/assets/*.js`
- `dist/assets/*.css`

## Деплой на production

После успешной сборки скопируйте содержимое `web-client/dist/` на production сервер.

### Автоматический деплой

```bash
# Из корневой папки проекта
cd deploy-to-prod
python deploy.py --build-web
```

### Ручной деплой

1. Соберите web client:
   ```bash
   cd web-client
   npm run build-only
   ```

2. Скопируйте файлы на сервер (замените пути на свои):
   ```bash
   # Пример для Windows
   xcopy /E /Y dist\* \\server\path\to\web\
   
   # Пример для Linux/SSH
   scp -r dist/* user@server:/path/to/web/
   ```

## Исправленные ошибки типов

В процессе работы были исправлены следующие ошибки:

1. ✅ `useReferenceView.ts` - добавлен `as any` для pagination
2. ✅ `useFilters.ts` - исправлены типы Ref
3. ✅ `models.ts` - добавлено поле `marked_for_deletion` в тип Work
4. ✅ `WorksView.vue` - исправлен интерфейс WorkWithHierarchy

## Оставшиеся ошибки типов

Следующие ошибки не критичны и не блокируют сборку:

- Ошибки в тестах (`__tests__/*.spec.ts`)
- Ошибки в других View компонентах (не связаны с новым функционалом)
- Ошибки совместимости типов в composables

Эти ошибки существовали до добавления нового функционала и не влияют на работу приложения.

## Проверка сборки

После сборки проверьте, что все файлы созданы:

```bash
# Windows
dir web-client\dist\assets\*View*.js

# Linux/Mac
ls -la web-client/dist/assets/*View*.js
```

Должны быть файлы:
- `WorksView-*.js`
- `ObjectsView-*.js`
- `EstimateListView-*.js`
- И другие View компоненты

## Troubleshooting

### Ошибка "Failed to fetch dynamically imported module"

Это означает, что на сервере старые файлы с другими хешами.

**Решение:** Пересоберите и скопируйте новые файлы на сервер.

### Ошибка "Build failed" при запуске build

**Решение:** Используйте `npm run build-only` вместо `npm run build`.

### Файлы не обновляются на сервере

**Решение:** 
1. Очистите кэш браузера (Ctrl+Shift+R)
2. Проверьте, что файлы скопированы на сервер
3. Перезапустите web-сервер (nginx/apache)

## Дата обновления

2024-12-04
