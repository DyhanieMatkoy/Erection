# Добавлена возможность выбора отображения отклонений в ежедневных отчетах

## Проблемы
1. **Ошибка валидации** - отсутствовало поле `line_number` при отправке данных на сервер
2. **Новое требование** - добавить возможность выбора отображения отклонений в единицах или процентах

## Решение

### 1. Исправлена ошибка с line_number

**Файл:** `web-client/src/views/documents/DailyReportFormView.vue`

При автозаполнении из сметы теперь добавляется поле `line_number`:

```typescript
.map((line, index) => {
  return {
    line_number: index + 1,  // Добавлено
    estimate_line_id: line.id!,
    work_id: line.work_id || undefined,
    // ...
  }
})
```

**Файл:** `web-client/src/types/models.ts`

Добавлено поле `line_number` в интерфейс `DailyReportLine`:

```typescript
export interface DailyReportLine {
  id?: number
  daily_report_id?: number
  line_number?: number  // Добавлено
  estimate_line_id: number
  // ...
}
```

### 2. Добавлен переключатель режима отображения отклонений

**Файл:** `web-client/src/components/documents/DailyReportLines.vue`

#### Интерфейс

Добавлен выпадающий список в заголовке компонента:

```vue
<div class="flex items-center space-x-2">
  <label class="text-sm text-gray-700">Отклонение:</label>
  <select v-model="deviationMode">
    <option value="units">В единицах</option>
    <option value="percent">В процентах</option>
  </select>
</div>
```

#### Логика

1. **Хранение данных** - отклонение всегда хранится в процентах в поле `deviation`

2. **Режим отображения** - переменная `deviationMode` определяет как показывать:
   - `'units'` - в единицах (факт - план)
   - `'percent'` - в процентах (по умолчанию)

3. **Функции**:

```typescript
// Получить значение отклонения в выбранном режиме
function getDeviationValue(line: DailyReportLine): number {
  const planned = parseFloat(String(line.planned_labor)) || 0
  const actual = parseFloat(String(line.actual_labor)) || 0
  
  if (deviationMode.value === 'units') {
    return actual - planned  // В единицах
  } else {
    return line.deviation    // В процентах
  }
}

// Форматировать отклонение для отображения
function formatDeviation(line: DailyReportLine): string {
  const value = getDeviationValue(line)
  const formatted = formatNumber(Math.abs(value))
  const sign = value >= 0 ? '+' : '-'
  const unit = deviationMode.value === 'percent' ? '%' : ''
  
  return `${sign}${formatted}${unit}`
}
```

## Примеры отображения

### Режим "В единицах"
- План: 10, Факт: 12 → Отклонение: **+2.00**
- План: 10, Факт: 8 → Отклонение: **-2.00**
- План: 10, Факт: 0 → Отклонение: **-10.00**

### Режим "В процентах"
- План: 10, Факт: 12 → Отклонение: **+20.00%**
- План: 10, Факт: 8 → Отклонение: **-20.00%**
- План: 10, Факт: 0 → Отклонение: **-100.00%**

## Цветовая индикация

- **Зеленый цвет** - положительное отклонение (факт больше плана)
- **Красный цвет** - отрицательное отклонение (факт меньше плана)

## Результат

✅ Исправлена ошибка валидации при проведении документа
✅ Добавлен переключатель режима отображения отклонений
✅ Отклонения корректно отображаются в обоих режимах
✅ Работает на desktop и mobile версиях
✅ Сборка проходит без ошибок
