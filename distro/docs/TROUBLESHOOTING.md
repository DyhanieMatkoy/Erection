# Решение проблем

## Проблема: DLL load failed while importing QtCore

### Симптомы
```
ImportError: DLL load failed while importing QtCore: Не найдена указанная процедура.
```

### Решение
Используйте PyQt6 версии 6.7.1 вместо 6.10.0:

```bash
.\venv\Scripts\pip.exe uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip
.\venv\Scripts\pip.exe install PyQt6==6.7.1
```

Или переустановите окружение:
```bash
# Удалить старое окружение
rmdir /s /q venv

# Создать новое
python -m venv venv

# Установить зависимости
.\venv\Scripts\pip.exe install -r requirements.txt
```

### Причина
Несовместимость PyQt6 6.10.0 с некоторыми версиями Windows или отсутствие необходимых системных библиотек.

---

## Проблема: Python не найден

### Симптомы
```
'python' is not recognized as an internal or external command
```

### Решение
1. Установите Python 3.10 или выше с [python.org](https://www.python.org/downloads/)
2. При установке отметьте "Add Python to PATH"
3. Перезапустите командную строку

---

## Проблема: База данных не создается

### Симптомы
Приложение запускается, но нет файла `construction.db`

### Решение
Проверьте права доступа к папке проекта. Запустите от имени администратора:
```bash
.\venv\Scripts\python.exe main.py
```

---

## Проблема: Тестовые данные не загружаются

### Симптомы
Не могу войти с admin/admin

### Решение
Загрузите тестовые данные:
```bash
.\venv\Scripts\python.exe load_test_data.py
```

Проверьте статус:
```bash
.\venv\Scripts\python.exe check_status.py
```

---

## Проблема: Виртуальное окружение не активируется

### Симптомы
```
.\venv\Scripts\activate : File cannot be loaded because running scripts is disabled
```

### Решение (PowerShell)
Разрешите выполнение скриптов:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Или используйте напрямую:
```bash
.\venv\Scripts\python.exe main.py
```

---

## Проблема: Медленная работа приложения

### Решение
1. Проверьте индексы в БД
2. Используйте транзакции для массовых операций
3. Оптимизируйте SQL запросы

---

## Проблема: Кириллица отображается некорректно

### Решение
Убедитесь, что файлы сохранены в UTF-8:
```python
# В начале Python файлов
# -*- coding: utf-8 -*-
```

Для SQL файлов:
```bash
# Загрузка с указанием кодировки
.\venv\Scripts\python.exe load_test_data.py
```

---

## Проблема: Не работают горячие клавиши

### Решение
Убедитесь, что форма имеет фокус. Проверьте реализацию `keyPressEvent`:

```python
def keyPressEvent(self, event):
    # Ваша обработка
    if event.key() == Qt.Key.Key_F9:
        self.on_create()
    else:
        super().keyPressEvent(event)  # Важно!
```

---

## Проблема: Ошибка при импорте модулей

### Симптомы
```
ModuleNotFoundError: No module named 'src'
```

### Решение
Запускайте из корневой папки проекта:
```bash
cd F:\traeRepo\Vibe1Co\Erection\Erection
.\venv\Scripts\python.exe main.py
```

---

## Получение помощи

Если проблема не решена:

1. Проверьте статус: `.\venv\Scripts\python.exe check_status.py`
2. Посмотрите логи в консоли
3. Проверьте версии:
   ```bash
   .\venv\Scripts\python.exe --version
   .\venv\Scripts\pip.exe list
   ```

## Полезные команды

### Переустановка окружения
```bash
rmdir /s /q venv
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

### Обновление зависимостей
```bash
.\venv\Scripts\pip.exe install --upgrade pip
.\venv\Scripts\pip.exe install --upgrade -r requirements.txt
```

### Проверка целостности БД
```bash
sqlite3 construction.db "PRAGMA integrity_check;"
```

### Бэкап БД
```bash
copy construction.db construction_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db
```
