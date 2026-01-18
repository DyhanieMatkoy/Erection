#!/usr/bin/env python3
"""
Скрипт для упаковки десктопного приложения для развертывания у клиентов
"""
import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
import configparser


class DesktopPackager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.output_dir = self.project_root / "desktop_package"
        self.temp_dir = self.project_root / "temp_build"
        
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
            
        # Проверяем основные зависимости
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
        
    def create_pyinstaller_spec(self):
        """Создание spec файла для PyInstaller"""
        print("📝 Создание PyInstaller spec файла...")
        
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('PrnForms', 'PrnForms'),
        ('fonts', 'fonts'),
        ('construction.db', '.'),
        ('env.ini', '.'),
    ],
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
        'src.data.initial_data',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'fastapi',
        'uvicorn',
        'pytest',
        'numpy',
        'pandas',
        'matplotlib',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ConstructionTimeManagement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='fonts/icon.ico' if os.path.exists('fonts/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ConstructionTimeManagement',
)
'''
        
        spec_path = self.project_root / "desktop_app.spec"
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
            
        return spec_path
        
    def prepare_database(self):
        """Подготовка базы данных для развертывания"""
        print("🗄️ Подготовка базы данных...")
        
        # Копируем базу данных
        source_db = self.project_root / "construction.db"
        if source_db.exists():
            shutil.copy2(source_db, self.temp_dir / "construction.db")
            print("✅ База данных скопирована")
        else:
            print("⚠️ База данных не найдена, будет создана при первом запуске")
            
    def prepare_config(self):
        """Подготовка конфигурационных файлов"""
        print("⚙️ Подготовка конфигурации...")
        
        # Создаем env.ini для десктопного приложения
        config = configparser.ConfigParser()
        
        config['Database'] = {
            'type': 'sqlite',
            'path': 'construction.db',
            'backup_enabled': 'true',
            'backup_interval_hours': '24'
        }
        
        config['Application'] = {
            'name': 'Система управления рабочим временем',
            'version': '1.0.0',
            'debug': 'false',
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
        
        # Копируем папки с ресурсами
        resources = ['PrnForms', 'fonts']
        for resource in resources:
            source = self.project_root / resource
            if source.exists():
                dest = self.temp_dir / resource
                shutil.copytree(source, dest, dirs_exist_ok=True)
                print(f"✅ {resource} скопирован")
                
    def build_executable(self):
        """Сборка исполняемого файла"""
        print("🔨 Сборка исполняемого файла...")
        
        spec_path = self.create_pyinstaller_spec()
        
        # Переходим в корневую директорию проекта
        original_cwd = os.getcwd()
        os.chdir(self.project_root)
        
        try:
            # Запускаем PyInstaller
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "--noconfirm",
                str(spec_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Ошибка сборки: {result.stderr}")
                return False
                
            print("✅ Исполняемый файл собран")
            return True
            
        finally:
            os.chdir(original_cwd)
            
    def create_installer_files(self):
        """Создание файлов установщика"""
        print("📦 Создание файлов установщика...")
        
        # Создаем install.bat
        install_bat = '''@echo off
chcp 65001 > nul
echo Установка системы управления рабочим временем...
echo.

REM Создаем папку приложения
if not exist "%PROGRAMFILES%\\ConstructionTimeManagement" (
    mkdir "%PROGRAMFILES%\\ConstructionTimeManagement"
)

REM Копируем файлы
echo Копирование файлов...
xcopy /E /I /Y "ConstructionTimeManagement" "%PROGRAMFILES%\\ConstructionTimeManagement\\"

REM Создаем ярлык на рабочем столе
echo Создание ярлыка...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\Система управления рабочим временем.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\\ConstructionTimeManagement\\ConstructionTimeManagement.exe'; $Shortcut.Save()"

REM Создаем ярлык в меню Пуск
if not exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\ConstructionTimeManagement" (
    mkdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\ConstructionTimeManagement"
)
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\ConstructionTimeManagement\\Система управления рабочим временем.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\\ConstructionTimeManagement\\ConstructionTimeManagement.exe'; $Shortcut.Save()"

echo.
echo Установка завершена!
echo Ярлык создан на рабочем столе и в меню Пуск.
echo.
pause
'''
        
        # Создаем uninstall.bat
        uninstall_bat = '''@echo off
chcp 65001 > nul
echo Удаление системы управления рабочим временем...
echo.

REM Удаляем ярлыки
del "%USERPROFILE%\\Desktop\\Система управления рабочим временем.lnk" 2>nul
rmdir /S /Q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\ConstructionTimeManagement" 2>nul

REM Удаляем папку приложения
rmdir /S /Q "%PROGRAMFILES%\\ConstructionTimeManagement" 2>nul

echo.
echo Удаление завершено!
echo.
pause
'''
        
        # Создаем README.txt
        readme_txt = '''СИСТЕМА УПРАВЛЕНИЯ РАБОЧИМ ВРЕМЕНЕМ СТРОИТЕЛЬНЫХ БРИГАД
========================================================

УСТАНОВКА:
1. Запустите install.bat от имени администратора
2. Дождитесь завершения установки
3. Запустите приложение через ярлык на рабочем столе

СИСТЕМНЫЕ ТРЕБОВАНИЯ:
- Windows 10/11 или Windows Server 2016+
- 4 ГБ оперативной памяти
- 500 МБ свободного места на диске
- Разрешение экрана не менее 1024x768

ПЕРВЫЙ ЗАПУСК:
- Логин: admin
- Пароль: admin

ВАЖНО: Обязательно смените пароль администратора после первого входа!

УДАЛЕНИЕ:
Запустите uninstall.bat от имени администратора

ТЕХНИЧЕСКАЯ ПОДДЕРЖКА:
При возникновении проблем обратитесь к системному администратору.

База данных автоматически создается при первом запуске.
Резервные копии создаются автоматически каждые 24 часа.
'''
        
        # Сохраняем файлы
        with open(self.output_dir / "install.bat", 'w', encoding='utf-8') as f:
            f.write(install_bat)
            
        with open(self.output_dir / "uninstall.bat", 'w', encoding='utf-8') as f:
            f.write(uninstall_bat)
            
        with open(self.output_dir / "README.txt", 'w', encoding='utf-8') as f:
            f.write(readme_txt)
            
        print("✅ Файлы установщика созданы")
        
    def package_application(self):
        """Упаковка приложения"""
        print("📦 Упаковка приложения...")
        
        # Копируем собранное приложение
        dist_dir = self.project_root / "dist" / "ConstructionTimeManagement"
        if dist_dir.exists():
            dest_dir = self.output_dir / "ConstructionTimeManagement"
            shutil.copytree(dist_dir, dest_dir, dirs_exist_ok=True)
            print("✅ Приложение скопировано")
        else:
            print("❌ Собранное приложение не найдено")
            return False
            
        # Создаем архив
        archive_name = f"ConstructionTimeManagement_Desktop_v1.0.zip"
        archive_path = self.project_root / archive_name
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(self.output_dir)
                    zipf.write(file_path, arc_path)
                    
        print(f"✅ Архив создан: {archive_name}")
        return True
        
    def cleanup(self):
        """Очистка временных файлов"""
        print("🧹 Очистка временных файлов...")
        
        # Удаляем временные директории
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
        # Удаляем файлы PyInstaller
        build_dir = self.project_root / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            
        spec_file = self.project_root / "desktop_app.spec"
        if spec_file.exists():
            spec_file.unlink()
            
        print("✅ Очистка завершена")
        
    def run(self):
        """Основной процесс упаковки"""
        print("🚀 Начинаем упаковку десктопного приложения...")
        print("=" * 60)
        
        try:
            # Проверяем зависимости
            if not self.check_dependencies():
                print("❌ Не все зависимости установлены")
                return False
                
            # Очищаем директории
            self.clean_directories()
            
            # Подготавливаем файлы
            self.prepare_database()
            self.prepare_config()
            self.copy_resources()
            
            # Собираем исполняемый файл
            if not self.build_executable():
                return False
                
            # Создаем файлы установщика
            self.create_installer_files()
            
            # Упаковываем приложение
            if not self.package_application():
                return False
                
            print("=" * 60)
            print("🎉 Упаковка завершена успешно!")
            print(f"📁 Результат в папке: {self.output_dir}")
            print(f"📦 Архив для распространения создан")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка упаковки: {e}")
            return False
            
        finally:
            # Очищаем временные файлы
            self.cleanup()


if __name__ == "__main__":
    packager = DesktopPackager()
    success = packager.run()
    
    if success:
        print("\n✅ Готово! Теперь вы можете:")
        print("1. Передать архив клиенту")
        print("2. Клиент должен распаковать архив")
        print("3. Запустить install.bat от имени администратора")
        sys.exit(0)
    else:
        print("\n❌ Упаковка не удалась")
        sys.exit(1)