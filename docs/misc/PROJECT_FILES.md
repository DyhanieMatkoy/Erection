# Список файлов проекта

## Документация (9 файлов)

1. **README.md** - Документация Qt/C++ версии
2. **README_PYQT6.md** - Документация PyQt6 версии
3. **INSTALL.md** - Инструкция по установке Qt/C++
4. **BUILD_STATUS.md** - Статус Qt/C++ версии
5. **PROJECT_SUMMARY.md** - Итоги Qt/C++ версии
6. **PYQT6_STATUS.md** - Статус PyQt6 версии
7. **FINAL_SUMMARY.md** - Итоговый отчет
8. **QUICKSTART.md** - Быстрый старт
9. **VERSIONS.md** - Сравнение версий

## Спецификации (.kiro/specs/)

1. **requirements.md** - Требования к системе
2. **design.md** - Архитектура (адаптирована под PyQt6)
3. **tasks.md** - Задачи Qt/C++ (автоформатирован)
4. **tasks_pyqt6.md** - Задачи PyQt6

## Python скрипты (3 файла)

1. **main.py** - Точка входа приложения
2. **load_test_data.py** - Загрузка тестовых данных
3. **check_status.py** - Проверка статуса проекта

## Batch скрипты (5 файлов)

1. **setup.bat** - Установка окружения PyQt6
2. **run.bat** - Запуск приложения PyQt6
3. **build.bat** - Сборка Qt/C++ (MinGW)
4. **build_msvc.bat** - Сборка Qt/C++ (MSVC)
5. **build_qmake.bat** - Сборка Qt/C++ (qmake)

## Конфигурация (4 файла)

1. **requirements.txt** - Зависимости Python
2. **CMakeLists.txt** - Конфигурация CMake (Qt/C++)
3. **ConstructionTimeManagement.pro** - Конфигурация qmake (Qt/C++)
4. **test_data.sql** - SQL скрипт с тестовыми данными

## Исходный код Python (src/)

### data/ (8 файлов)
1. **__init__.py**
2. **database_manager.py** - Менеджер базы данных

#### models/ (6 файлов)
3. **__init__.py**
4. **base_model.py** - Базовая модель
5. **estimate.py** - Модель сметы
6. **daily_report.py** - Модель ежедневного отчета
7. **references.py** - Справочники
8. **user.py** - Модель пользователя

#### repositories/ (3 файла)
9. **__init__.py**
10. **estimate_repository.py** - Репозиторий смет
11. **user_repository.py** - Репозиторий пользователей

### services/ (4 файла)
12. **__init__.py**
13. **auth_service.py** - Сервис аутентификации
14. **calculator_service.py** - Сервис расчетов
15. **estimate_service.py** - Сервис смет

### viewmodels/ (2 файла)
16. **__init__.py**
17. **estimate_view_model.py** - ViewModel сметы

### views/ (6 файлов)
18. **__init__.py**
19. **main_window.py** - Главное окно
20. **login_form.py** - Форма входа
21. **base_list_form.py** - Базовая форма списка
22. **base_document_form.py** - Базовая форма документа
23. **base_table_part.py** - Табличная часть

## Исходный код C++ (архив qt_cpp_version.zip)

### Заголовочные файлы (.h) - 40+ файлов
- data/database_manager.h
- data/models/*.h (11 файлов)
- data/repositories/*.h (5 файлов)
- services/*.h (7 файлов)
- viewmodels/*.h (5 файлов)
- views/*.h (5 файлов)

### Файлы реализации (.cpp) - 40+ файлов
- Соответствующие .cpp для всех .h файлов
- main.cpp

## База данных

1. **construction.db** - База данных SQLite (14 таблиц)

## Архивы

1. **qt_cpp_version.zip** - Полная Qt/C++ версия

## Итого

- **Документация**: 9 MD файлов
- **Python код**: 23 файла
- **C++ код**: 80+ файлов (в архиве)
- **Скрипты**: 8 файлов
- **Конфигурация**: 4 файла
- **База данных**: 1 файл
- **Архивы**: 1 файл

**Всего**: 126+ файлов

## Размеры

- PyQt6 проект: ~50 KB исходного кода
- Qt/C++ проект: ~200 KB исходного кода (в архиве)
- База данных: ~20 KB
- Документация: ~100 KB
- Виртуальное окружение: ~100 MB (PyQt6 + зависимости)

## Структура каталогов

```
.
├── .git/                          # Git репозиторий
├── .kiro/                         # Спецификации Kiro
│   └── specs/
│       └── construction-time-management/
├── build/                         # Сборка Qt/C++ (временная)
├── venv/                          # Виртуальное окружение Python
├── src/                           # Исходный код Python
│   ├── data/
│   │   ├── models/
│   │   └── repositories/
│   ├── services/
│   ├── viewmodels/
│   └── views/
├── *.md                           # Документация
├── *.py                           # Python скрипты
├── *.bat                          # Batch скрипты
├── *.txt                          # Конфигурация
├── *.sql                          # SQL скрипты
├── *.db                           # База данных
└── qt_cpp_version.zip             # Архив C++ версии
```
