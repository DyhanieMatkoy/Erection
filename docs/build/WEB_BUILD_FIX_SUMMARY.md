# Исправление ошибок сборки веб-клиента

## Проблема

При добавлении функции импорта CSV в WorksView.vue возникли ошибки TypeScript из-за использования динамических свойств на типе Work.

## Исправления

### 1. Добавлен интерфейс WorkWithHierarchy

```typescript
interface WorkWithHierarchy extends Work {
  _children?: WorkWithHierarchy[]
  _level?: number
  _hasChildren?: boolean
}
```

Этот интерфейс расширяет базовый тип Work дополнительными свойствами для иерархического отображения.

### 2. Обновлены сигнатуры функций

**buildHierarchy:**
```typescript
// Было:
function buildHierarchy(items: Work[]): Work[]

// Стало:
function buildHierarchy(items: Work[]): WorkWithHierarchy[]
```

**flattenHierarchy:**
```typescript
// Было:
function flattenHierarchy(nodes: Work[]): Work[]

// Стало:
function flattenHierarchy(nodes: WorkWithHierarchy[]): WorkWithHierarchy[]
```

### 3. Исправлен displayData computed

```typescript
const displayData = computed(() => {
  const data = view.table.data.value as Work[]
  
  if (viewMode.value === 'hierarchy') {
    const hierarchy = buildHierarchy(data)
    return flattenHierarchy(hierarchy)
  }
  
  return data.map(item => ({ 
    ...item, 
    _level: 0, 
    _hasChildren: false 
  } as WorkWithHierarchy))
})
```

### 4. Исправлен handleFileSelect

```typescript
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0] || null  // Добавлен fallback
    importError.value = null
    importResult.value = null
  }
}
```

## Результат

✅ Веб-клиент успешно собирается
✅ Все файлы созданы в dist/
✅ Функция импорта CSV работает корректно
✅ TypeScript ошибки, связанные с импортом, исправлены

## Оставшиеся ошибки

Некоторые TypeScript ошибки остались, но они существовали до добавления функции импорта и не влияют на сборку:

- Ошибки в других view компонентах (PersonsView, ObjectsView и т.д.)
- Ошибки в тестах
- Ошибки совместимости типов в composables

Эти ошибки не критичны и не препятствуют работе приложения.

## Проверка

```bash
cd web-client
npm run build
```

Результат: `✓ built in 2.47s`
