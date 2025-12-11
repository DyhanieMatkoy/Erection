# Changelog - Детализация регистра выполнения работ

## Дата: 2025-11-23

### Добавлено

#### API
- Новый endpoint `GET /api/v1/registers/work-execution/movements` для получения детализированных движений по регистру
- Поддержка фильтрации по периоду, объекту, смете и работе
- Пагинация результатов

#### Веб-клиент
- Компонент `WorkExecutionDetailDialog.vue` для отображения детализации движений
- Возможность открытия детализации двойным кликом по строке в отчете
- Возможность перехода к исходному документу (смете или daily report) двойным кликом по движению
- Поддержка мобильной версии (клик вместо двойного клика)

#### Тесты
- Добавлены тесты для нового API endpoint в `api/tests/test_registers.py`

#### Документация
- `web-client/WORK_EXECUTION_DETAIL.md` - техническая документация
- `ДЕТАЛИЗАЦИЯ_РЕГИСТРА.md` - инструкция для пользователей

### Изменено

#### API
- `web-client/src/api/registers.ts` - добавлен метод `getWorkExecutionMovements()` и интерфейс `WorkExecutionDetailMovement`

#### Веб-клиент
- `web-client/src/views/registers/WorkExecutionView.vue`:
  - Добавлен обработчик двойного клика для строк таблицы
  - Добавлен компонент детализации
  - Добавлена функция `handleShowDetail()`
  - Добавлена подсказка для пользователя

### Desktop-приложение

Функционал уже был реализован ранее в:
- `src/views/work_execution_detail_dialog.py` - диалог детализации
- Поддержка открытия документов по двойному клику

## Технические детали

### Структура данных

Движение в детализации содержит:
```typescript
{
  id: number
  period: string
  recorder_type: 'estimate' | 'daily_report'
  recorder_id: number
  line_number: number
  object_id: number
  object_name: string
  estimate_id: number
  estimate_number: string
  work_id: number
  work_name: string
  quantity_income: number
  quantity_expense: number
  sum_income: number
  sum_expense: number
}
```

### Маршрутизация

При открытии документа из детализации:
- Смета: `/documents/estimates/{id}`
- Ежедневный отчет: `/documents/daily-reports/{id}`

## Использование

1. Откройте регистр выполнения работ
2. Примените фильтры (период обязателен)
3. Дважды кликните по строке для просмотра детализации
4. Дважды кликните по движению для открытия документа
