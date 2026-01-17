# Команды для упаковки десктопного приложения

## 🚀 Быстрые команды

### Базовая упаковка (рекомендуется)
```bash
# Windows
package_desktop.bat

# Или напрямую Python
python package_desktop.py
```

### Расширенная упаковка
```bash
# Стандартная расширенная упаковка
python package_desktop_advanced.py

# С тестированием
python package_desktop_advanced.py --test

# Режим отладки
python package_desktop_advanced.py --debug

# С пользовательской конфигурацией
python package_desktop_advanced.py --config my_config.ini

# Без очистки временных файлов
python package_desktop_advanced.py --no-clean
```

### Тестирование
```bash
# Тест упакованного приложения
test_packaged_app.bat

# Прямой запуск
.\desktop_package\ConstructionTimeManagement\ConstructionTimeManagement.exe
```

## 📋 Подготовка к упаковке

### Установка зависимостей
```bash
# Основные зависимости
pip install -r requirements.txt

# PyInstaller для упаковки
pip install pyinstaller

# Проверка версий
python --version
pip list | findstr PyQt6
```

### Проверка файлов
```bash
# Проверка структуры проекта
dir src
dir PrnForms
dir fonts

# Проверка базы данных
dir construction.db

# Проверка конфигурации
type env.ini
```

## 🔧 Устранение проблем

### Если упаковка не работает
```bash
# Переустановка PyInstaller
pip uninstall pyinstaller
pip install pyinstaller

# Очистка кэша pip
pip cache purge

# Обновление setuptools
pip install --upgrade setuptools
```

### Если не хватает модулей
```bash
# Установка отдельных пакетов
pip install PyQt6==6.7.1
pip install openpyxl==3.1.2
pip install reportlab==4.0.7
pip install sqlalchemy>=2.0.0
pip install alembic>=1.12.0
```

### Проблемы с правами доступа
```bash
# Запуск от администратора
# Правый клик на cmd -> "Запуск от имени администратора"

# Или через PowerShell
Start-Process cmd -Verb RunAs
```

## 📁 Структура результата

После успешной упаковки получите:

```
desktop_package/
├── ConstructionTimeManagement/
│   ├── ConstructionTimeManagement.exe
│   └── _internal/
├── install.bat
├── uninstall.bat
└── README.txt

ConstructionTimeManagement_Desktop_v1.0.zip  # Архив для клиента
```

## 🎯 Проверка результата

### Размеры файлов
```bash
# Проверка размера архива (должен быть ~60 МБ)
dir ConstructionTimeManagement_Desktop_v1.0.zip

# Проверка размера приложения
dir desktop_package\ConstructionTimeManagement /s
```

### Тестирование функций
```bash
# 1. Запуск приложения
.\desktop_package\ConstructionTimeManagement\ConstructionTimeManagement.exe

# 2. Проверка входа (admin/admin)
# 3. Проверка основных функций
# 4. Проверка создания базы данных
# 5. Проверка печати отчетов
```

## 📤 Передача клиенту

### Что передать
- `ConstructionTimeManagement_Desktop_v1.0.zip` - основной архив
- Инструкция по установке (в архиве есть README.txt)
- Контакты для поддержки

### Инструкция для клиента
```
1. Распакуйте архив в любую папку
2. Запустите install.bat от имени администратора
3. Дождитесь завершения установки
4. Найдите ярлык на рабочем столе
5. Войдите: admin / admin
6. Смените пароль администратора!
```

## 🔄 Обновление приложения

### Создание обновления
```bash
# 1. Внесите изменения в код
# 2. Протестируйте локально
# 3. Создайте новый пакет
python package_desktop.py

# 4. Передайте клиенту новый архив
```

### У клиента
```bash
# 1. Сделайте резервную копию данных
# 2. Запустите новый install.bat
# 3. Выберите "Y" для обновления
# 4. База данных сохранится автоматически
```

## 📊 Мониторинг

### Логи упаковки
- Все сообщения выводятся в консоль
- При ошибках проверьте последние сообщения
- Сохраните вывод для анализа проблем

### Логи у клиента
```
%PROGRAMFILES%\ConstructionTimeManagement\logs\
```

## 🆘 Экстренные команды

### Если что-то пошло не так
```bash
# Полная очистка и пересборка
rmdir /s /q desktop_package
rmdir /s /q build
rmdir /s /q dist
del *.spec
python package_desktop.py
```

### Восстановление после ошибок
```bash
# Проверка целостности Python
python -c "import sys; print(sys.executable)"

# Проверка PyQt6
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"

# Проверка SQLAlchemy
python -c "import sqlalchemy; print('SQLAlchemy OK')"
```

## 📞 Получение помощи

### Сбор информации для поддержки
```bash
# Версия Python
python --version

# Список установленных пакетов
pip list > installed_packages.txt

# Информация о системе
systeminfo > system_info.txt

# Последние ошибки упаковки
# Скопируйте вывод консоли
```

### Контакты
- Системный администратор
- Разработчик приложения
- Техническая поддержка

---

**Совет:** Сохраните этот файл для быстрого доступа к командам упаковки!