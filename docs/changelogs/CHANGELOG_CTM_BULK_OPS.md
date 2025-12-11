# Changelog - Базовый путь /ctm и групповые операции

## Дата: 30 ноября 2025

### Новые возможности

#### 1. Базовый путь /ctm для web-клиента
- Web-приложение теперь работает по адресу `/ctm/` вместо корневого `/`
- Упрощает развертывание на серверах с несколькими приложениями
- Совместимо с nginx, Apache и IIS

**Изменения:**
- `web-client/vite.config.ts` - добавлен `base: '/ctm/'`
- `web-client/src/router/index.ts` - обновлен базовый путь роутера
- `web-client/index.html` - обновлен title и lang
- `deploy-to-prod/nginx-ctm.conf` - пример конфигурации nginx

#### 2. Групповые операции над документами
- Выбор нескольких документов в списках через чекбоксы
- Групповое удаление документов
- Групповое проведение документов (только администраторы)
- Групповая отмена проведения (только администраторы)

**Поддерживаемые документы:**
- Сметы (Estimates)
- Ежедневные отчеты (Daily Reports)
- Табели (Timesheets)

**Изменения Frontend:**
- `web-client/src/components/common/DataTable.vue` - добавлена поддержка выбора строк
- `web-client/src/api/documents.ts` - добавлены функции групповых операций
- `web-client/src/views/documents/EstimateListView.vue` - добавлены обработчики
- `web-client/src/views/documents/DailyReportListView.vue` - добавлены обработчики
- `web-client/src/views/documents/TimesheetListView.vue` - добавлены обработчики

**Изменения Backend:**
- `api/endpoints/documents.py` - добавлены 9 новых endpoints для групповых операций

### API Endpoints

#### Новые endpoints для групповых операций:

**Сметы:**
- `POST /api/documents/estimates/bulk-delete`
- `POST /api/documents/estimates/bulk-post`
- `POST /api/documents/estimates/bulk-unpost`

**Ежедневные отчеты:**
- `POST /api/documents/daily-reports/bulk-delete`
- `POST /api/documents/daily-reports/bulk-post`
- `POST /api/documents/daily-reports/bulk-unpost`

**Табели:**
- `POST /api/documents/timesheets/bulk-delete`
- `POST /api/documents/timesheets/bulk-post`
- `POST /api/documents/timesheets/bulk-unpost`

### Документация

**Новые файлы:**
- `WEB_CLIENT_CTM_DEPLOYMENT.md` - краткая инструкция по развертыванию
- `web-client/CTM_BASE_PATH_SETUP.md` - подробная настройка базового пути
- `web-client/BULK_OPERATIONS_GUIDE.md` - руководство по групповым операциям
- `deploy-to-prod/nginx-ctm.conf` - пример конфигурации nginx
- `CHANGELOG_CTM_BULK_OPS.md` - этот файл

### Обратная совместимость

- API endpoints остались без изменений
- Существующие функции работают как прежде
- Добавлены только новые endpoints для групповых операций
- Базовый путь можно легко изменить обратно на `/` (см. документацию)

### Безопасность

- Групповые операции проведения/отмены требуют роль администратора
- Проверка прав выполняется на backend
- Транзакции обеспечивают целостность данных
- Нельзя удалить проведенные документы

### Производительность

- Операции выполняются последовательно для каждого документа
- Для больших объемов (>50 документов) рекомендуется разбивать на части
- Таймаут операции: 60 секунд

### Тестирование

Рекомендуется протестировать:
1. Доступ к приложению по новому пути `/ctm/`
2. Выбор документов в списках
3. Групповое удаление непроведенных документов
4. Групповое проведение (для администраторов)
5. Групповую отмену проведения (для администраторов)
6. Обработку ошибок при групповых операциях

### Развертывание

#### Шаг 1: Сборка
```bash
build_web.bat
```

#### Шаг 2: Развертывание
```bash
# Nginx (Linux)
sudo cp deploy-to-prod/nginx-ctm.conf /etc/nginx/sites-available/construction-app
sudo ln -s /etc/nginx/sites-available/construction-app /etc/nginx/sites-enabled/
sudo cp -r web-client/dist/* /var/www/construction-app/
sudo nginx -t && sudo systemctl reload nginx
```

#### Шаг 3: Проверка
Откройте http://servut.npksarmat.ru/ctm/

### Откат изменений

Если нужно вернуться к корневому пути:
1. Удалите `base: '/ctm/'` из `vite.config.ts`
2. Измените роутер на `createWebHistory(import.meta.env.BASE_URL)`
3. Пересоберите: `build_web.bat`
4. Обновите конфигурацию веб-сервера

### Известные ограничения

- Групповые операции выполняются последовательно (не параллельно)
- Максимум рекомендуется 50 документов за раз
- Partial success - успешные операции не откатываются при ошибках

### Поддержка

При проблемах проверьте:
- Логи nginx: `/var/log/nginx/construction-app-error.log`
- Логи API: `journalctl -u construction-api -f`
- Консоль браузера (F12)
- Network tab в DevTools

### Авторы

- Базовый путь /ctm: реализовано
- Групповые операции: реализовано
- Документация: создана
- Тестирование: требуется

### Следующие шаги

1. Протестировать на production сервере
2. Обучить пользователей работе с групповыми операциями
3. Собрать обратную связь
4. При необходимости оптимизировать производительность
