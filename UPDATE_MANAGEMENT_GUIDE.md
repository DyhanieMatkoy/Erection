# Управление обновлениями десктопного приложения

## 🔄 Да, дистрибутив нужно пересоздавать

**Короткий ответ:** Да, после изменений в коде нужно создавать новый дистрибутив.

**Но есть способы оптимизировать этот процесс!**

## 📋 Стратегии управления обновлениями

### 1. Автоматизированная сборка

Создайте автоматизированный процесс сборки:

```bash
# Скрипт полной пересборки
build_and_deploy.bat
```

### 2. Версионирование

Используйте семантическое версионирование:
- `1.0.0` - мажорные изменения
- `1.1.0` - новые функции
- `1.0.1` - исправления ошибок

### 3. Инкрементальные обновления

Для небольших изменений создавайте патчи вместо полной переустановки.

## 🚀 Оптимизированный процесс обновления

### Создание автоматизированного скрипта сборки

<function_calls>
<invoke name="fsWrite">
<parameter name="path">build_and_deploy.pyin/env python3
"""
Автоматизированная сборка и развертывание десктопного приложения
"""
import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime
import configparser


class AutomatedBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.version_file = self.project_root / "version.json"
        self.build_log = self.project_root / "build.log"
        
    def get_current_version(self):
        """Получить текущую версию"""
        if self.version_file.exists():
            with open(self.version_file, 'r') as f:
                version_data = json.load(f)
                return version_data.get('version', '1.0.0')
        return '1.0.0'
        
    def increment_version(self, version_type='patch'):
        """Увеличить версию"""
        current = self.get_current_version()
        major, minor, patch = map(int, current.split('.'))
        
        if version_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif version_type == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
            
        new_version = f"{major}.{minor}.{patch}"
        
        # Сохранить новую версию
        version_data = {
            'version': new_version,
            'build_date': datetime.now().isoformat(),
            'build_number': self.get_build_number() + 1
        }
        
        with open(self.version_file, 'w') as f:
            json.dump(version_data, f, indent=2)
            
        return new_version
        
    def get_build_number(self):
        """Получить номер сборки"""
        if self.version_file.exists():
            with open(self.version_file, 'r') as f:
                version_data = json.load(f)
                return version_data.get('build_number', 0)
        return 0
        
    def log_message(self, message):
        """Записать сообщение в лог"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        print(message)
        
        with open(self.build_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    def check_changes(self):
        """Проверить изменения в коде"""
        try:
            # Проверяем git статус
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                changes = result.stdout.strip()
                if changes:
                    self.log_message(f"Обнаружены изменения:\n{changes}")
                    return True
                else:
                    self.log_message("Изменений в коде не обнаружено")
                    return False
            else:
                self.log_message("Git не доступен, пропускаем проверку изменений")
                return True
                
        except FileNotFoundError:
            self.log_message("Git не установлен, пропускаем проверку изменений")
            return True
            
    def run_tests(self):
        """Запустить тесты"""
        self.log_message("Запуск тестов...")
        
        try:
            # Запускаем Python тесты
            result = subprocess.run([sys.executable, '-m', 'pytest', 'test/', '-v'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message("✅ Все тесты прошли успешно")
                return True
            else:
                self.log_message(f"❌ Тесты не прошли:\n{result.stderr}")
                return False
                
        except Exception as e:
            self.log_message(f"⚠️ Не удалось запустить тесты: {e}")
            return True  # Продолжаем сборку даже если тесты не запустились
            
    def build_desktop(self, version):
        """Собрать десктопное приложение"""
        self.log_message(f"Сборка десктопного приложения версии {version}...")
        
        try:
            # Обновляем версию в конфигурации
            self.update_version_in_config(version)
            
            # Запускаем упаковку
            result = subprocess.run([sys.executable, 'package_desktop.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message("✅ Десктопное приложение собрано успешно")
                return True
            else:
                self.log_message(f"❌ Ошибка сборки:\n{result.stderr}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Исключение при сборке: {e}")
            return False
            
    def update_version_in_config(self, version):
        """Обновить версию в конфигурационных файлах"""
        # Обновляем package_desktop.py
        package_file = self.project_root / "package_desktop.py"
        if package_file.exists():
            content = package_file.read_text(encoding='utf-8')
            content = content.replace("'version': '1.0.0'", f"'version': '{version}'")
            package_file.write_text(content, encoding='utf-8')
            
        # Обновляем main.py если есть версия там
        main_file = self.project_root / "main.py"
        if main_file.exists():
            content = main_file.read_text(encoding='utf-8')
            if 'VERSION = ' in content:
                import re
                content = re.sub(r'VERSION = ["\'][^"\']*["\']', 
                               f'VERSION = "{version}"', content)
                main_file.write_text(content, encoding='utf-8')
                
    def create_release_notes(self, version):
        """Создать заметки о релизе"""
        notes_file = self.project_root / f"RELEASE_NOTES_v{version}.md"
        
        notes_content = f"""# Release Notes v{version}

## Дата релиза: {datetime.now().strftime("%Y-%m-%d")}

## Изменения в этой версии:

### Новые функции
- [ ] Добавьте описание новых функций

### Исправления ошибок
- [ ] Добавьте описание исправленных ошибок

### Улучшения
- [ ] Добавьте описание улучшений

## Установка

1. Скачайте архив `ConstructionTimeManagement_Desktop_v{version}.zip`
2. Распакуйте в любую папку
3. Запустите `install.bat` от имени администратора

## Обновление с предыдущей версии

1. Сделайте резервную копию данных
2. Запустите `uninstall.bat` для удаления старой версии
3. Установите новую версию как описано выше
4. Данные сохранятся автоматически

## Системные требования

- Windows 10/11 или Windows Server 2016+
- 4 ГБ оперативной памяти
- 500 МБ свободного места на диске

## Техническая поддержка

При возникновении проблем обратитесь к системному администратору.
"""
        
        with open(notes_file, 'w', encoding='utf-8') as f:
            f.write(notes_content)
            
        self.log_message(f"Создан файл заметок о релизе: {notes_file}")
        
    def archive_old_builds(self):
        """Архивировать старые сборки"""
        archives_dir = self.project_root / "build_archives"
        archives_dir.mkdir(exist_ok=True)
        
        # Перемещаем старые архивы
        for zip_file in self.project_root.glob("ConstructionTimeManagement_Desktop_v*.zip"):
            if zip_file.name not in [f.name for f in archives_dir.glob("*.zip")]:
                shutil.move(str(zip_file), str(archives_dir / zip_file.name))
                self.log_message(f"Архивирован старый билд: {zip_file.name}")
                
    def commit_changes(self, version):
        """Зафиксировать изменения в git"""
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', f'Release v{version}'], check=True)
            subprocess.run(['git', 'tag', f'v{version}'], check=True)
            
            self.log_message(f"Изменения зафиксированы в git с тегом v{version}")
            
        except subprocess.CalledProcessError as e:
            self.log_message(f"⚠️ Не удалось зафиксировать в git: {e}")
        except FileNotFoundError:
            self.log_message("⚠️ Git не доступен")
            
    def build_and_deploy(self, version_type='patch', skip_tests=False, auto_commit=False):
        """Полный цикл сборки и развертывания"""
        self.log_message("=" * 60)
        self.log_message("🚀 Начинаем автоматизированную сборку")
        self.log_message("=" * 60)
        
        try:
            # 1. Проверяем изменения
            if not self.check_changes():
                response = input("Изменений не обнаружено. Продолжить сборку? (y/N): ")
                if response.lower() != 'y':
                    self.log_message("Сборка отменена пользователем")
                    return False
                    
            # 2. Увеличиваем версию
            new_version = self.increment_version(version_type)
            self.log_message(f"📋 Новая версия: {new_version}")
            
            # 3. Запускаем тесты
            if not skip_tests:
                if not self.run_tests():
                    response = input("Тесты не прошли. Продолжить сборку? (y/N): ")
                    if response.lower() != 'y':
                        self.log_message("Сборка отменена из-за неудачных тестов")
                        return False
                        
            # 4. Архивируем старые сборки
            self.archive_old_builds()
            
            # 5. Собираем приложение
            if not self.build_desktop(new_version):
                self.log_message("❌ Сборка не удалась")
                return False
                
            # 6. Создаем заметки о релизе
            self.create_release_notes(new_version)
            
            # 7. Фиксируем изменения в git
            if auto_commit:
                self.commit_changes(new_version)
                
            self.log_message("=" * 60)
            self.log_message(f"🎉 Сборка v{new_version} завершена успешно!")
            self.log_message("=" * 60)
            
            # Показываем результаты
            archive_path = self.project_root / f"ConstructionTimeManagement_Desktop_v{new_version}.zip"
            if archive_path.exists():
                size_mb = archive_path.stat().st_size / 1024 / 1024
                self.log_message(f"📦 Архив: {archive_path.name} ({size_mb:.1f} МБ)")
            
            self.log_message(f"📋 Заметки о релизе: RELEASE_NOTES_v{new_version}.md")
            self.log_message("🚀 Готово к передаче клиентам!")
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Критическая ошибка: {e}")
            return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Автоматизированная сборка десктопного приложения')
    parser.add_argument('--version-type', choices=['major', 'minor', 'patch'], 
                       default='patch', help='Тип увеличения версии')
    parser.add_argument('--skip-tests', action='store_true', 
                       help='Пропустить запуск тестов')
    parser.add_argument('--auto-commit', action='store_true', 
                       help='Автоматически зафиксировать изменения в git')
    
    args = parser.parse_args()
    
    builder = AutomatedBuilder()
    success = builder.build_and_deploy(
        version_type=args.version_type,
        skip_tests=args.skip_tests,
        auto_commit=args.auto_commit
    )
    
    if success:
        print("\n✅ Сборка завершена успешно!")
        sys.exit(0)
    else:
        print("\n❌ Сборка не удалась!")
        sys.exit(1)


if __name__ == "__main__":
    main()