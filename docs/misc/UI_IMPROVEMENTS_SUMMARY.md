# Улучшения пользовательского интерфейса

## Обзор изменений

Выполнены три ключевых улучшения пользовательского интерфейса:

1. **Замена модальных окон на статусную строку** для сообщений о сохранении и проведении
2. **Автоматический показ окна быстрой навигации** при запуске программы
3. **Использование форм списка документов** для выбора ссылок в реквизитах форм

---

## 1. Статусная строка вместо модальных окон

### Проблема
Модальные окна с сообщениями "Смета сохранена", "Документ проведен" и т.д. прерывали работу пользователя и требовали дополнительного клика для закрытия.

### Решение
Информационные сообщения о успешных операциях теперь отображаются в статусной строке главного окна на 3 секунды.

### Затронутые файлы
- `src/views/estimate_document_form.py`
- `src/views/daily_report_document_form.py`

### Изменения

#### Сохранение документа
**Было:**
```python
QMessageBox.information(self, "Успех", "Смета сохранена")
```

**Стало:**
```python
# Show message in status bar instead of modal dialog
if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
    self.parent().parent().statusBar().showMessage("Смета сохранена", 3000)
```

#### Проведение документа
**Было:**
```python
QMessageBox.information(self, "Успех", "Документ проведен")
```

**Стало:**
```python
# Show message in status bar instead of modal dialog
if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
    self.parent().parent().statusBar().showMessage("Документ проведен", 3000)
```

#### Отмена проведения
**Было:**
```python
QMessageBox.information(self, "Успех", "Проведение отменено")
```

**Стало:**
```python
# Show message in status bar instead of modal dialog
if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
    self.parent().parent().statusBar().showMessage("Проведение отменено", 3000)
```

### Преимущества
- ✅ Не прерывает работу пользователя
- ✅ Не требует дополнительных кликов
- ✅ Сообщение автоматически исчезает через 3 секунды
- ✅ Пользователь может продолжать работу сразу после операции

### Примечание
Сообщения об **ошибках** по-прежнему отображаются в модальных окнах, так как требуют внимания пользователя.

---

## 2. Окно быстрой навигации при запуске

### Проблема
Пользователю приходилось каждый раз искать нужную форму в меню или запоминать горячие клавиши.

### Решение
При запуске программы автоматически открывается окно быстрой навигации, позволяющее быстро перейти к нужной форме.

### Затронутые файлы
- `src/views/main_window.py`

### Изменения

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recent_forms = deque(maxlen=10)
        self.setup_ui()
        self.setup_shortcuts()
        
        # Show quick navigation on startup
        QTimer.singleShot(100, self.show_quick_navigation)
```

### Функциональность окна быстрой навигации

#### Доступные формы:
1. Сметы
2. Ежедневные отчеты
3. Контрагенты
4. Объекты
5. Организации
6. Физические лица
7. Виды работ
8. Выполнение работ (отчет)

#### Возможности:
- **Поиск по названию** - начните вводить название формы в поле поиска
- **Навигация стрелками** - используйте стрелки вверх/вниз для выбора
- **Enter** - открыть выбранную форму
- **Escape** - закрыть окно навигации
- **Двойной клик** - открыть форму

#### Горячая клавиша
Окно быстрой навигации можно вызвать в любой момент нажатием **Ctrl+K**

### Преимущества
- ✅ Быстрый доступ к любой форме при запуске
- ✅ Не нужно искать в меню
- ✅ Поддержка поиска по названию
- ✅ Можно закрыть Escape, если не нужно

---

## 3. Формы списка для выбора ссылок

### Проблема
В форме "Ежедневный отчет" смета выбиралась через ComboBox, который:
- Загружал все незавершенные сметы в память
- Не позволял видеть полную информацию о смете
- Не поддерживал поиск и фильтрацию

### Решение
Заменен ComboBox на кнопку "...", которая открывает полноценную форму списка смет с возможностью поиска, сортировки и фильтрации.

### Затронутые файлы
- `src/views/daily_report_document_form.py`

### Изменения

#### UI компонент
**Было:**
```python
self.estimate_combo = QComboBox()
self.estimate_combo.currentIndexChanged.connect(self.on_estimate_changed)
estimate_layout.addWidget(self.estimate_combo)
```

**Стало:**
```python
self.estimate_edit = QLineEdit()
self.estimate_edit.setReadOnly(True)
self.estimate_id = 0
estimate_layout.addWidget(self.estimate_edit)
self.estimate_button = QPushButton("...")
self.estimate_button.setMaximumWidth(30)
self.estimate_button.clicked.connect(self.on_select_estimate)
estimate_layout.addWidget(self.estimate_button)
```

#### Метод выбора
```python
def on_select_estimate(self):
    """Select estimate using list form"""
    from .estimate_list_form import EstimateListForm
    
    # Create estimate list form in selection mode
    dialog = QDialog(self)
    dialog.setWindowTitle("Выбор сметы")
    dialog.setModal(True)
    dialog.resize(800, 600)
    
    layout = QVBoxLayout()
    
    # Create list form
    list_form = EstimateListForm()
    list_form.setParent(dialog)
    layout.addWidget(list_form)
    
    # Add buttons
    button_layout = QHBoxLayout()
    button_layout.addStretch()
    
    select_button = QPushButton("Выбрать")
    select_button.clicked.connect(dialog.accept)
    button_layout.addWidget(select_button)
    
    cancel_button = QPushButton("Отмена")
    cancel_button.clicked.connect(dialog.reject)
    button_layout.addWidget(cancel_button)
    
    layout.addLayout(button_layout)
    dialog.setLayout(layout)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        # Get selected estimate
        current_row = list_form.table_view.currentRow()
        if current_row >= 0:
            estimate_id_item = list_form.table_view.item(current_row, 0)
            if estimate_id_item:
                estimate_id = int(estimate_id_item.text())
                self.load_estimate(estimate_id)
                self.modified = True
```

### Преимущества
- ✅ Полноценная форма списка с поиском и фильтрацией
- ✅ Видны все колонки: ID, номер, дата, заказчик, объект, сумма
- ✅ Можно сортировать по любой колонке
- ✅ Не загружает все данные в память сразу
- ✅ Единообразный интерфейс выбора ссылок

### Будущие улучшения
Этот подход можно применить к другим формам:
- Выбор заказчика в смете
- Выбор объекта в смете
- Выбор подрядчика в смете
- Выбор ответственного в смете
- Выбор бригадира в ежедневном отчете

---

## Инструкция по использованию

### Работа со статусной строкой
1. Выполните операцию (сохранение, проведение и т.д.)
2. Сообщение появится в нижней части окна (статусная строка)
3. Сообщение автоматически исчезнет через 3 секунды
4. Можно продолжать работу сразу, не закрывая окно

### Быстрая навигация
1. При запуске программы автоматически откроется окно навигации
2. Начните вводить название формы для поиска
3. Используйте стрелки для выбора нужной формы
4. Нажмите Enter или дважды кликните для открытия
5. Нажмите Escape для закрытия окна

**Вызов в любой момент:** Нажмите **Ctrl+K**

### Выбор сметы в ежедневном отчете
1. Откройте форму "Ежедневный отчет"
2. Нажмите кнопку "..." рядом с полем "Смета"
3. Откроется форма списка смет
4. Используйте поиск, фильтры, сортировку для поиска нужной сметы
5. Выберите смету (клик на строке)
6. Нажмите кнопку "Выбрать"
7. Смета будет установлена в форме отчета

---

## Технические детали

### Доступ к статусной строке
Формы документов получают доступ к статусной строке главного окна через иерархию родителей:
```python
if self.parent() and hasattr(self.parent().parent(), 'statusBar'):
    self.parent().parent().statusBar().showMessage("Сообщение", 3000)
```

Где:
- `self.parent()` - MDI sub-window
- `self.parent().parent()` - MainWindow
- `statusBar()` - статусная строка главного окна
- `3000` - время отображения в миллисекундах (3 секунды)

### Отложенный показ навигации
Используется `QTimer.singleShot` для отложенного показа окна навигации после полной инициализации главного окна:
```python
QTimer.singleShot(100, self.show_quick_navigation)
```

### Встраивание формы списка в диалог
Форма списка встраивается в диалоговое окно для режима выбора:
```python
dialog = QDialog(self)
list_form = EstimateListForm()
list_form.setParent(dialog)
layout.addWidget(list_form)
```

---

## Тестирование

### Тест 1: Статусная строка
1. Откройте смету
2. Внесите изменения
3. Нажмите "Сохранить"
4. Проверьте, что в статусной строке появилось сообщение "Смета сохранена"
5. Проверьте, что сообщение исчезло через 3 секунды
6. Проведите документ
7. Проверьте сообщение "Документ проведен"

### Тест 2: Быстрая навигация при запуске
1. Запустите программу
2. Проверьте, что автоматически открылось окно быстрой навигации
3. Введите "смет" в поле поиска
4. Проверьте, что отфильтровалась форма "Сметы"
5. Нажмите Enter
6. Проверьте, что открылась форма списка смет

### Тест 3: Выбор сметы через форму списка
1. Откройте "Ежедневный отчет"
2. Нажмите кнопку "..." рядом с полем "Смета"
3. Проверьте, что открылась форма списка смет
4. Выберите любую смету
5. Нажмите "Выбрать"
6. Проверьте, что смета установлена в форме отчета

---

## Связанные файлы

- `src/views/main_window.py` - главное окно с навигацией
- `src/views/estimate_document_form.py` - форма сметы
- `src/views/daily_report_document_form.py` - форма ежедневного отчета
- `src/views/estimate_list_form.py` - форма списка смет

---

## Заключение

Эти улучшения делают интерфейс более удобным и современным:
- Меньше модальных окон = меньше кликов
- Быстрая навигация = быстрее работа
- Формы списка для выбора = больше информации и контроля

Пользователи могут работать быстрее и эффективнее.
