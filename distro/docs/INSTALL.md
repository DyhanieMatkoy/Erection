# Инструкция по установке и сборке

## Требования

1. **Visual Studio 2022** с компонентами C++
2. **Qt 6.x** (рекомендуется 6.5.0 или выше)
3. **CMake** (встроен в Visual Studio)

## Установка Qt

1. Скачайте Qt Online Installer с https://www.qt.io/download-qt-installer
2. Установите Qt 6.x с компонентом MSVC 2019 64-bit
3. Запомните путь установки (например, `C:\Qt\6.5.0\msvc2019_64`)

## Сборка проекта

### Вариант 1: Автоматическая сборка

1. Откройте `build_msvc.bat` в текстовом редакторе
2. Измените `QT_PATH` на ваш путь к Qt:
   ```batch
   SET QT_PATH=C:\Qt\6.5.0\msvc2019_64
   ```
3. Запустите `build_msvc.bat`

### Вариант 2: Ручная сборка

1. Откройте **Developer Command Prompt for VS 2022**
2. Перейдите в папку проекта
3. Выполните команды:

```cmd
set QT_PATH=C:\Qt\6.5.0\msvc2019_64
set PATH=%QT_PATH%\bin;%PATH%
set CMAKE_PREFIX_PATH=%QT_PATH%

cmake -S . -B build -G "NMake Makefiles"
cd build
nmake
```

### Вариант 3: Использование Qt Creator

1. Откройте Qt Creator
2. Откройте файл `CMakeLists.txt`
3. Настройте Kit (MSVC 2019 64-bit)
4. Нажмите Build

## Запуск

После успешной сборки:

```cmd
cd build
ConstructionTimeManagement.exe
```

## Инициализация базы данных

При первом запуске база данных создастся автоматически. Для загрузки тестовых данных:

1. Откройте SQLite клиент (например, DB Browser for SQLite)
2. Откройте файл `construction.db`
3. Выполните SQL из файла `test_data.sql`

## Тестовые пользователи

После загрузки тестовых данных:

- **admin** / **admin** - Администратор
- **manager** / **manager** - Руководитель  
- **foreman** / **foreman** - Бригадир

## Возможные проблемы

### Qt не найден

Убедитесь, что:
- Qt установлен
- Путь `QT_PATH` указан правильно
- В PATH добавлен `%QT_PATH%\bin`

### Ошибка компилятора

Убедитесь, что:
- Visual Studio 2022 установлена с компонентами C++
- Используется Developer Command Prompt

### Ошибки линковки

Проверьте, что версия Qt совместима с компилятором MSVC 2019/2022.
