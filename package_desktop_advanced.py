#!/usr/bin/env python3
"""
Расширенный скрипт для упаковки десктопного приложения
Поддерживает различные режимы упаковки и конфигурации
"""
import os
import sys
import shutil
import subprocess
import zipfile
import argparse
from pathlib import Path
import configparser
import json
from datetime import datetime


class AdvancedDesktopPackager:
    def __init__(self, config_file=None):
        self.project_root = Path(__file__).parent
        self.config = self.load_config(config_file)
        self.output_dir = self.project_root / self.config['output']['directory']
        self.temp_dir = self.project_root / "temp_build"
        
    def load_config(self, config_file):
        """Загрузка конфигурации упаковки"""
        default_config = {
            'app': {
                'name': 'ConstructionTimeManagement',
                'display_name': 'Система управления рабочим временем',
                'version': '1.0.0',
                'description': 'Система управления рабочим временем строительных бригад',
                'author': 'Construction Management Team'
            },
            'build': {
                'console': False,
                'debug': False,
                'upx': True,
                'onefile': False,
                'exclude_modules': ['fastapi', 'uvicorn', 'pytest', 'numpy', 'pandas', 'matplotlib']
            },
            'database': {
                'include_sample': True,
                'type': 'sqlite',
                'path': 'construction.db'
            },
            'output': {
                'directory': 'desktop_package',
                'create_installer': True,
                'create_archive': True,
                'archive_format': 'zip'
            },
            'resources': {
                'folders': ['PrnForms', 'fonts'],
                'files': ['env.ini']
            }
        }
        
        if config_file and Path(config_file).exists():
            # Загружаем пользовательскую конфигурацию
            user_config = {}
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file)
            
            for section in config_parser.sections():
                user_config[section] = dict(config_parser[section])
                
            # Объединяем с дефолтной конфигурацией
            for section, values in user_config.items():
                if section in default_config:
                    default_config[section].update(values)
                else:
                    default_config[section] = values
                    
        return default_config
        
    def create_build_info(self):
        """Создание информации о сборке"""
        build_info = {
            'app_name': self.config['app']['name'],
            'version': self.config['app']['version'],
            'build_date': datetime.now().isoformat(),
            'python_version': sys.version,
            'platform': sys.platform,
            'build_machine': os.environ.get('COMPUTERNAME', 'unknown')
        }
        
        info_path = self.temp_dir / "build_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(build_info, f, indent=2, ensure_ascii=False)
            
        return build_info
        
    def create_advanced_spec(self):
        """Создание расширенного spec файла"""
        print("📝 Создание расширенного PyInstaller spec файла...")
        
        exclude_modules = self.config['build']['exclude_modules']
        app_name = self.config['app']['name']
        console = self.config['build']['console']
        debug = self.config['build']['debug']
        upx = self.config['build']['upx']
        onefile = self.config['build']['onefile']
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Автоматически сгенерированный spec файл для {app_name}

import os
from pathlib import Path

block_cipher = None

# Определяем пути
project_root = Path(__file__).parent
src_path = project_root / "src"
resources_path = project_root

# Данные для включения
datas = [
    (str(src_path), 'src'),
    (str(resources_path / 'PrnForms'), 'PrnForms'),
    (str(resources_path / 'fonts'), 'fonts'),
]

# Добавляем базу данных если существует
db_path = project_root / 'construction.db'
if db_path.exists():
    datas.append((str(db_path), '.'))

# Добавляем конфигурацию
env_path = project_root / 'env.ini'
if env_path.exists():
    datas.append((str(env_path), '.'))

# Добавляем информацию о сборке
build_info_path = project_root / 'temp_build' / 'build_info.json'
if build_info_path.exists():
    datas.append((str(build_info_path), '.'))

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'openpyxl',
        'reportlab',
        'sqlalchemy',
        'alembic',
        'sqlite3',
        'configparser',
        'json',
        'datetime',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={exclude_modules},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    {'[] if not onefile else "a.binaries, a.zipfiles, a.datas,"}
    exclude_binaries={'True' if not onefile else 'False'},
    name='{app_name}',
    debug={str(debug).lower()},
    bootloader_ignore_signals=False,
    strip=False,
    upx={str(upx).lower()},
    console={str(console).lower()},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='fonts/icon.ico' if os.path.exists('fonts/icon.ico') else None,
)

{'coll = COLLECT(' if not onefile else ''}
{'    exe,' if not onefile else ''}
{'    a.binaries,' if not onefile else ''}
{'    a.zipfiles,' if not onefile else ''}
{'    a.datas,' if not onefile else ''}
{'    strip=False,' if not onefile else ''}
{'    upx=' + str(upx).lower() + ',' if not onefile else ''}
{'    upx_exclude=[],' if not onefile else ''}
{'    name="' + app_name + '",' if not onefile else ''}
{')' if not onefile else ''}
'''
        
        spec_path = self.project_root / f"{app_name}.spec"
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
            
        return spec_path
        
    def create_advanced_installer(self):
        """Создание расширенного установщика"""
        print("📦 Создание расширенного установщика...")
        
        app_name = self.config['app']['name']
        display_name = self.config['app']['display_name']
        version = self.config['app']['version']
        
        # Создаем install.bat с дополнительными возможностями
        install_bat = f'''@echo off
chcp 65001 > nul
title Установка {display_name} v{version}

echo ========================================
echo   УСТАНОВКА {display_name.upper()}
echo   Версия: {version}
echo ========================================
echo.

REM Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Требуются права администратора!
    echo Запустите установщик от имени администратора.
    echo.
    pause
    exit /b 1
)

echo ✅ Права администратора подтверждены
echo.

REM Определяем папку установки
set "INSTALL_DIR=%PROGRAMFILES%\\{app_name}"
echo 📁 Папка установки: %INSTALL_DIR%

REM Проверяем существующую установку
if exist "%INSTALL_DIR%" (
    echo ⚠️ Обнаружена существующая установка
    echo Хотите обновить приложение? (Y/N)
    set /p "choice=Ваш выбор: "
    if /i not "%choice%"=="Y" (
        echo Установка отменена.
        pause
        exit /b 0
    )
    echo 🔄 Обновление существующей установки...
    rmdir /S /Q "%INSTALL_DIR%" 2>nul
)

REM Создаем папку приложения
echo 📂 Создание папки приложения...
mkdir "%INSTALL_DIR%" 2>nul

REM Копируем файлы
echo 📋 Копирование файлов...
xcopy /E /I /Y "{app_name}" "%INSTALL_DIR%\\" >nul
if %errorlevel% neq 0 (
    echo ❌ Ошибка копирования файлов!
    pause
    exit /b 1
)

REM Создаем ярлык на рабочем столе
echo 🔗 Создание ярлыка на рабочем столе...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\{display_name}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{app_name}.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = '{display_name} v{version}'; $Shortcut.Save()"

REM Создаем ярлык в меню Пуск
echo 📋 Создание ярлыка в меню Пуск...
set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{display_name}"
mkdir "%START_MENU%" 2>nul
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU%\\{display_name}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{app_name}.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = '{display_name} v{version}'; $Shortcut.Save()"

REM Создаем ярлык деинсталлятора
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU%\\Удалить {display_name}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\uninstall.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Удалить {display_name}'; $Shortcut.Save()"

REM Копируем деинсталлятор
copy /Y "uninstall.bat" "%INSTALL_DIR%\\uninstall.bat" >nul

REM Регистрируем в реестре (для Programs and Features)
echo 🔧 Регистрация в системе...
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}" /v "DisplayName" /t REG_SZ /d "{display_name}" /f >nul
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}" /v "DisplayVersion" /t REG_SZ /d "{version}" /f >nul
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}" /v "Publisher" /t REG_SZ /d "{self.config['app']['author']}" /f >nul
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}" /v "UninstallString" /t REG_SZ /d "%INSTALL_DIR%\\uninstall.bat" /f >nul
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}" /v "InstallLocation" /t REG_SZ /d "%INSTALL_DIR%" /f >nul

echo.
echo ========================================
echo   УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!
echo ========================================
echo.
echo ✅ Приложение установлено в: %INSTALL_DIR%
echo 🔗 Ярлык создан на рабочем столе
echo 📋 Ярлык добавлен в меню Пуск
echo.
echo 🚀 Для запуска используйте ярлык на рабочем столе
echo    или найдите "{display_name}" в меню Пуск
echo.
echo 📖 Первый вход: admin / admin
echo ⚠️  Обязательно смените пароль после входа!
echo.
pause
'''
        
        # Создаем расширенный uninstall.bat
        uninstall_bat = f'''@echo off
chcp 65001 > nul
title Удаление {display_name} v{version}

echo ========================================
echo   УДАЛЕНИЕ {display_name.upper()}
echo   Версия: {version}
echo ========================================
echo.

REM Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Требуются права администратора!
    echo Запустите деинсталлятор от имени администратора.
    echo.
    pause
    exit /b 1
)

echo ⚠️ Вы действительно хотите удалить {display_name}?
echo Все данные приложения будут удалены!
echo.
set /p "choice=Продолжить удаление? (Y/N): "
if /i not "%choice%"=="Y" (
    echo Удаление отменено.
    pause
    exit /b 0
)

echo.
echo 🗑️ Удаление приложения...

REM Завершаем процесс если запущен
taskkill /F /IM "{app_name}.exe" 2>nul

REM Удаляем ярлыки
echo 🔗 Удаление ярлыков...
del "%USERPROFILE%\\Desktop\\{display_name}.lnk" 2>nul
rmdir /S /Q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{display_name}" 2>nul

REM Удаляем из реестра
echo 🔧 Удаление из реестра...
reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}" /f >nul 2>&1

REM Удаляем папку приложения (с задержкой для завершения процессов)
echo 📂 Удаление файлов приложения...
timeout /t 2 /nobreak >nul
rmdir /S /Q "%PROGRAMFILES%\\{app_name}" 2>nul

echo.
echo ========================================
echo   УДАЛЕНИЕ ЗАВЕРШЕНО
echo ========================================
echo.
echo ✅ {display_name} успешно удален из системы
echo.
pause
'''
        
        # Сохраняем файлы
        with open(self.output_dir / "install.bat", 'w', encoding='utf-8') as f:
            f.write(install_bat)
            
        with open(self.output_dir / "uninstall.bat", 'w', encoding='utf-8') as f:
            f.write(uninstall_bat)
            
        print("✅ Расширенный установщик создан")
        
    def run_advanced(self, clean_build=True, test_run=False):
        """Запуск расширенной упаковки"""
        print("🚀 Начинаем расширенную упаковку десктопного приложения...")
        print("=" * 70)
        
        try:
            # Создаем информацию о сборке
            build_info = self.create_build_info()
            print(f"📋 Сборка: {build_info['app_name']} v{build_info['version']}")
            
            # Основные этапы упаковки
            if clean_build:
                self.clean_directories()
                
            if not self.check_dependencies():
                return False
                
            self.prepare_database()
            self.prepare_config()
            self.copy_resources()
            
            # Создаем расширенный spec файл
            spec_path = self.create_advanced_spec()
            
            # Собираем приложение
            if not self.build_executable_advanced(spec_path):
                return False
                
            # Создаем расширенный установщик
            if self.config['output']['create_installer']:
                self.create_advanced_installer()
                
            # Упаковываем
            if not self.package_application_advanced():
                return False
                
            # Тестовый запуск
            if test_run:
                self.test_application()
                
            print("=" * 70)
            print("🎉 Расширенная упаковка завершена успешно!")
            print(f"📁 Результат в папке: {self.output_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка упаковки: {e}")
            return False
            
        finally:
            if clean_build:
                self.cleanup()
                
    def build_executable_advanced(self, spec_path):
        """Расширенная сборка исполняемого файла"""
        print("🔨 Расширенная сборка исполняемого файла...")
        
        original_cwd = os.getcwd()
        os.chdir(self.project_root)
        
        try:
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "--noconfirm",
                str(spec_path)
            ]
            
            if self.config['build']['debug']:
                cmd.append("--debug=all")
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Ошибка сборки: {result.stderr}")
                return False
                
            print("✅ Исполняемый файл собран")
            return True
            
        finally:
            os.chdir(original_cwd)
            
    def package_application_advanced(self):
        """Расширенная упаковка приложения"""
        print("📦 Расширенная упаковка приложения...")
        
        app_name = self.config['app']['name']
        version = self.config['app']['version']
        
        # Копируем собранное приложение
        dist_dir = self.project_root / "dist" / app_name
        if dist_dir.exists():
            dest_dir = self.output_dir / app_name
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(dist_dir, dest_dir)
            print("✅ Приложение скопировано")
        else:
            print("❌ Собранное приложение не найдено")
            return False
            
        # Создаем архив если нужно
        if self.config['output']['create_archive']:
            archive_format = self.config['output']['archive_format']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{app_name}_Desktop_v{version}_{timestamp}.{archive_format}"
            archive_path = self.project_root / archive_name
            
            if archive_format == 'zip':
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(self.output_dir):
                        for file in files:
                            file_path = Path(root) / file
                            arc_path = file_path.relative_to(self.output_dir)
                            zipf.write(file_path, arc_path)
            else:
                # Можно добавить поддержку других форматов
                print(f"⚠️ Формат архива {archive_format} не поддерживается")
                
            print(f"✅ Архив создан: {archive_name}")
            
        return True
        
    def test_application(self):
        """Тестирование упакованного приложения"""
        print("🧪 Тестирование упакованного приложения...")
        
        app_name = self.config['app']['name']
        exe_path = self.output_dir / app_name / f"{app_name}.exe"
        
        if exe_path.exists():
            print(f"✅ Исполняемый файл найден: {exe_path}")
            
            # Можно добавить дополнительные тесты
            file_size = exe_path.stat().st_size
            print(f"📏 Размер файла: {file_size / 1024 / 1024:.1f} МБ")
            
            # Проверяем зависимости
            deps_dir = exe_path.parent / "_internal"
            if deps_dir.exists():
                deps_count = len(list(deps_dir.rglob("*")))
                print(f"📦 Файлов зависимостей: {deps_count}")
                
        else:
            print("❌ Исполняемый файл не найден")
            
    # Наследуем методы из базового класса
    def clean_directories(self):
        """Очистка временных и выходных директорий"""
        print("🧹 Очистка директорий...")
        
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
    def check_dependencies(self):
        """Проверка необходимых зависимостей"""
        print("🔍 Проверка зависимостей...")
        
        try:
            import PyInstaller
            print(f"✅ PyInstaller найден: {PyInstaller.__version__}")
        except ImportError:
            print("❌ PyInstaller не найден. Устанавливаю...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            
        required_packages = {
            "PyQt6": "PyQt6.QtCore",
            "openpyxl": "openpyxl", 
            "reportlab": "reportlab",
            "sqlalchemy": "sqlalchemy",
            "alembic": "alembic"
        }
        for package_name, import_name in required_packages.items():
            try:
                __import__(import_name)
                print(f"✅ {package_name} найден")
            except ImportError:
                print(f"❌ {package_name} не найден")
                return False
        return True
        
    def prepare_database(self):
        """Подготовка базы данных для развертывания"""
        print("🗄️ Подготовка базы данных...")
        
        if self.config['database']['include_sample']:
            source_db = self.project_root / self.config['database']['path']
            if source_db.exists():
                shutil.copy2(source_db, self.temp_dir / self.config['database']['path'])
                print("✅ База данных скопирована")
            else:
                print("⚠️ База данных не найдена, будет создана при первом запуске")
                
    def prepare_config(self):
        """Подготовка конфигурационных файлов"""
        print("⚙️ Подготовка конфигурации...")
        
        config = configparser.ConfigParser()
        
        config['Database'] = {
            'type': self.config['database']['type'],
            'path': self.config['database']['path'],
            'backup_enabled': 'true',
            'backup_interval_hours': '24'
        }
        
        config['Application'] = {
            'name': self.config['app']['display_name'],
            'version': self.config['app']['version'],
            'debug': str(self.config['build']['debug']).lower(),
            'auto_backup': 'true'
        }
        
        config['Sync'] = {
            'enabled': 'true',
            'server_url': 'https://your-server.com',
            'node_code': 'DESKTOP-CLIENT-1',
            'auto_sync': 'true',
            'sync_interval': '300',
            'compression_enabled': 'true',
            'auth_token': '',
            'last_sync': ''
        }
        
        config['UI'] = {
            'theme': 'default',
            'language': 'ru',
            'font_size': '10',
            'window_state_save': 'true'
        }
        
        config_path = self.temp_dir / "env.ini"
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
            
        print("✅ Конфигурация создана")
        
    def copy_resources(self):
        """Копирование ресурсов"""
        print("📁 Копирование ресурсов...")
        
        for resource in self.config['resources']['folders']:
            source = self.project_root / resource
            if source.exists():
                dest = self.temp_dir / resource
                shutil.copytree(source, dest, dirs_exist_ok=True)
                print(f"✅ {resource} скопирован")
                
        for resource in self.config['resources']['files']:
            source = self.project_root / resource
            if source.exists():
                dest = self.temp_dir / resource
                shutil.copy2(source, dest)
                print(f"✅ {resource} скопирован")
                
    def cleanup(self):
        """Очистка временных файлов"""
        print("🧹 Очистка временных файлов...")
        
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
        build_dir = self.project_root / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            
        # Удаляем spec файлы
        for spec_file in self.project_root.glob("*.spec"):
            spec_file.unlink()
            
        print("✅ Очистка завершена")


def main():
    parser = argparse.ArgumentParser(description='Расширенная упаковка десктопного приложения')
    parser.add_argument('--config', '-c', help='Файл конфигурации упаковки')
    parser.add_argument('--no-clean', action='store_true', help='Не очищать временные файлы')
    parser.add_argument('--test', '-t', action='store_true', help='Запустить тестирование после сборки')
    parser.add_argument('--debug', '-d', action='store_true', help='Режим отладки')
    
    args = parser.parse_args()
    
    packager = AdvancedDesktopPackager(args.config)
    
    if args.debug:
        packager.config['build']['debug'] = True
        packager.config['build']['console'] = True
        
    success = packager.run_advanced(
        clean_build=not args.no_clean,
        test_run=args.test
    )
    
    if success:
        print("\n✅ Готово! Расширенная упаковка завершена успешно.")
        sys.exit(0)
    else:
        print("\n❌ Упаковка не удалась")
        sys.exit(1)


if __name__ == "__main__":
    main()