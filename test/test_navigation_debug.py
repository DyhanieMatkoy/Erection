#!/usr/bin/env python3
"""
Отладочный тест навигации в селекторе работ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from src.views.reference_picker_dialog import ReferencePickerDialog

class DebugReferencePickerDialog(ReferencePickerDialog):
    """Отладочная версия селектора с дополнительным логированием"""
    
    def on_navigate_up(self):
        """Navigate to parent level with debug output"""
        print(f"[DEBUG] on_navigate_up called, current_parent_id = {self.current_parent_id}")
        
        if self.current_parent_id is not None:
            cursor = self.db.cursor()
            cursor.execute(f"""
                SELECT parent_id FROM {self.table_name}
                WHERE id = ?
            """, (self.current_parent_id,))
            row = cursor.fetchone()
            
            print(f"[DEBUG] Query result: {row}")
            
            if row:
                old_parent_id = self.current_parent_id
                self.current_parent_id = row['parent_id'] if row['parent_id'] else None
                print(f"[DEBUG] Changed parent_id from {old_parent_id} to {self.current_parent_id}")
            else:
                print(f"[DEBUG] No row found for id {self.current_parent_id}, setting to None")
                self.current_parent_id = None
            
            print(f"[DEBUG] Calling load_data()")
            self.load_data()
        else:
            print(f"[DEBUG] current_parent_id is None, nothing to do")
    
    def on_drill_down(self):
        """Drill down into selected group with debug output"""
        print(f"[DEBUG] on_drill_down called")
        
        if not self.is_hierarchical:
            print(f"[DEBUG] Not hierarchical, returning")
            return

        current_row = self.table_view.currentRow()
        print(f"[DEBUG] Current row: {current_row}")
        
        if current_row >= 0:
            id_item = self.table_view.item(current_row, 0)
            if id_item:
                selected_id = int(id_item.text())
                print(f"[DEBUG] Selected ID: {selected_id}")
                
                # Check if this item has children
                cursor = self.db.cursor()
                cursor.execute(f"""
                    SELECT COUNT(*) as cnt FROM {self.table_name}
                    WHERE parent_id = ? AND marked_for_deletion = 0
                """, (selected_id,))
                has_children = cursor.fetchone()['cnt'] > 0
                
                print(f"[DEBUG] Has children: {has_children}")
                
                if has_children:
                    old_parent_id = self.current_parent_id
                    self.current_parent_id = selected_id
                    print(f"[DEBUG] Changed parent_id from {old_parent_id} to {self.current_parent_id}")
                    self.load_data()
    
    def update_navigation_state(self):
        """Update navigation buttons and label with debug output"""
        print(f"[DEBUG] update_navigation_state called, current_parent_id = {self.current_parent_id}")
        
        # Enable/disable up button
        up_enabled = self.current_parent_id is not None
        self.up_button.setEnabled(up_enabled)
        print(f"[DEBUG] Up button enabled: {up_enabled}")
        
        self.up_button.setVisible(self.is_hierarchical)
        self.drill_down_button.setVisible(self.is_hierarchical)
        self.parent_label.setVisible(self.is_hierarchical)
        
        # Update parent label
        if self.current_parent_id is None:
            self.parent_label.setText("Корень")
            print(f"[DEBUG] Parent label set to 'Корень'")
        else:
            cursor = self.db.cursor()
            cursor.execute(f"""
                SELECT {self.display_column} FROM {self.table_name}
                WHERE id = ?
            """, (self.current_parent_id,))
            row = cursor.fetchone()
            if row:
                label_text = f"Группа: {row[self.display_column]}"
                self.parent_label.setText(label_text)
                print(f"[DEBUG] Parent label set to '{label_text}'")

def test_navigation():
    """Тест навигации с отладкой"""
    app = QApplication(sys.argv)
    
    print("=== Отладочный тест селектора работ ===")
    
    # Создаем отладочный диалог селектора работ
    dialog = DebugReferencePickerDialog("works", "Отладочный тест селектора работ")
    
    # Показываем диалог
    dialog.show()
    
    print("Диалог открыт. Проверьте:")
    print("1. Есть ли группы работ (с иконкой 📁)")
    print("2. Войдите в группу (двойной клик или Enter)")
    print("3. Попробуйте кнопку 'Вверх' - смотрите отладочный вывод")
    print("4. Попробуйте клавишу Backspace")
    
    # Запускаем приложение
    sys.exit(app.exec())

if __name__ == "__main__":
    test_navigation()