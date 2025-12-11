# Быстрый старт

## Установка и запуск за 3 шага

### 1. Установка окружения
```bash
setup.bat
```

### 2. Загрузка тестовых данных
```bash
.\venv\Scripts\python.exe load_test_data.py
```

### 3. Запуск приложения
```bash
run.bat
```

## Вход в систему

Используйте один из тестовых аккаунтов:

| Логин | Пароль | Роль |
|-------|--------|------|
| admin | admin | Администратор |
| manager | manager | Руководитель |
| foreman | foreman | Бригадир |

## Проверка статуса

```bash
.\venv\Scripts\python.exe check_status.py
```

## Горячие клавиши

### В формах списков
- **Insert** или **F9** - Создать новый элемент
- **Enter** - Открыть выбранный элемент
- **Delete** - Пометить на удаление
- **Ctrl+F** - Быстрый поиск
- **Ctrl+D** - Копировать элемент

### В формах документов
- **Ctrl+S** - Сохранить
- **Ctrl+Shift+S** - Сохранить и закрыть
- **Esc** - Закрыть (с подтверждением)
- **Ctrl+P** - Печать

### В табличных частях
- **Insert** - Добавить строку
- **Delete** - Удалить строку
- **F4** - Выбор из справочника

## Структура проекта

```
.
├── main.py                 # Запуск приложения
├── load_test_data.py       # Загрузка тестовых данных
├── check_status.py         # Проверка статуса
├── requirements.txt        # Зависимости
├── setup.bat              # Установка
├── run.bat                # Запуск
└── src/                   # Исходный код
    ├── data/              # Данные и репозитории
    ├── services/          # Бизнес-логика
    ├── viewmodels/        # ViewModels
    └── views/             # UI формы
```

## Что дальше?

Смотрите:
- **README_PYQT6.md** - полная документация
- **PYQT6_STATUS.md** - статус выполнения задач
- **FINAL_SUMMARY.md** - итоговый отчет

## Помощь

Если что-то не работает:

1. Проверьте версию Python: `python --version` (нужен 3.10+)
2. Проверьте статус: `.\venv\Scripts\python.exe check_status.py`
3. Переустановите зависимости: `.\venv\Scripts\pip.exe install -r requirements.txt`

### Ошибка "DLL load failed while importing QtCore"

Если видите эту ошибку, переустановите PyQt6:
```bash
.\venv\Scripts\pip.exe uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip
.\venv\Scripts\pip.exe install PyQt6==6.7.1
```

Подробнее см. **TROUBLESHOOTING.md**
