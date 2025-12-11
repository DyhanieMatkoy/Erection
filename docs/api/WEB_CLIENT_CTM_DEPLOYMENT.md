# Развертывание Web-клиента с базовым путем /ctm

## Краткая инструкция

### 1. Сборка web-клиента

```bash
# Windows
build_web.bat

# Linux/Mac
cd web-client
npm install
npm run build
cd ..
```

### 2. Развертывание на сервере

#### Вариант A: Nginx (Linux)

```bash
# Копируем конфигурацию
sudo cp deploy-to-prod/nginx-ctm.conf /etc/nginx/sites-available/construction-app
sudo ln -s /etc/nginx/sites-available/construction-app /etc/nginx/sites-enabled/

# Копируем файлы приложения
sudo mkdir -p /var/www/construction-app
sudo cp -r web-client/dist/* /var/www/construction-app/

# Проверяем и перезагружаем nginx
sudo nginx -t
sudo systemctl reload nginx
```

#### Вариант B: IIS (Windows Server)

1. Скопируйте содержимое `web-client/dist/` в `C:\inetpub\wwwroot\construction-app\`
2. Создайте новый сайт в IIS Manager
3. Настройте Application Pool (.NET CLR Version: No Managed Code)
4. Добавьте URL Rewrite правила (см. web-client/CTM_BASE_PATH_SETUP.md)

### 3. Проверка

Откройте браузер и перейдите на:
- http://servut.npksarmat.ru/ctm/

## Новые возможности

### Групповые операции

В списках документов теперь доступны:
- ✅ Выбор нескольких документов через чекбоксы
- ✅ Групповое удаление
- ✅ Групповое проведение (для администраторов)
- ✅ Групповая отмена проведения (для администраторов)

### Использование

1. Откройте список документов (Сметы, Отчеты или Табели)
2. Выберите нужные документы с помощью чекбоксов
3. Используйте кнопки групповых операций в верхней части списка
4. Подтвердите операцию

## Изменения в коде

### Frontend (web-client/)
- `vite.config.ts` - добавлен `base: '/ctm/'`
- `src/router/index.ts` - изменен базовый путь на `/ctm/`
- `src/components/common/DataTable.vue` - добавлена поддержка выбора строк
- `src/api/documents.ts` - добавлены функции групповых операций
- `src/views/documents/*.vue` - добавлены обработчики групповых операций

### Backend (api/)
- `api/endpoints/documents.py` - добавлены endpoints для групповых операций:
  - `/documents/estimates/bulk-delete`
  - `/documents/estimates/bulk-post`
  - `/documents/estimates/bulk-unpost`
  - `/documents/daily-reports/bulk-delete`
  - `/documents/daily-reports/bulk-post`
  - `/documents/daily-reports/bulk-unpost`
  - `/documents/timesheets/bulk-delete`
  - `/documents/timesheets/bulk-post`
  - `/documents/timesheets/bulk-unpost`

## Документация

Подробная документация доступна в:
- `web-client/CTM_BASE_PATH_SETUP.md` - настройка базового пути
- `web-client/BULK_OPERATIONS_GUIDE.md` - руководство по групповым операциям
- `deploy-to-prod/nginx-ctm.conf` - пример конфигурации nginx

## Откат изменений

Если нужно вернуться к корневому пути `/`:

1. В `web-client/vite.config.ts` удалите строку `base: '/ctm/',`
2. В `web-client/src/router/index.ts` измените:
   ```typescript
   history: createWebHistory(import.meta.env.BASE_URL)
   ```
3. Пересоберите приложение: `build_web.bat`
4. Обновите конфигурацию веб-сервера

## Поддержка

При возникновении проблем проверьте:
1. Логи nginx: `/var/log/nginx/construction-app-error.log`
2. Логи API: `journalctl -u construction-api -f`
3. Консоль браузера (F12 → Console)
4. Network tab в DevTools для проверки загрузки ресурсов
