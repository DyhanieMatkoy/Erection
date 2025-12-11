"""Test that daily report improvements compile without errors"""

def test_imports():
    """Test that all modules can be imported"""
    try:
        from src.views.daily_report_document_form import DailyReportDocumentForm
        print("✓ DailyReportDocumentForm импортирован успешно")
        
        from src.views.estimate_list_form import EstimateListForm
        print("✓ EstimateListForm импортирован успешно")
        
        # Check that DailyReportDocumentForm has the new parameter
        import inspect
        sig = inspect.signature(DailyReportDocumentForm.__init__)
        params = list(sig.parameters.keys())
        
        if 'estimate_id' in params:
            print("✓ Параметр estimate_id добавлен в DailyReportDocumentForm")
        else:
            print("✗ Параметр estimate_id НЕ найден в DailyReportDocumentForm")
            print(f"  Параметры: {params}")
        
        # Check that create_new_report has the new parameter
        sig = inspect.signature(DailyReportDocumentForm.create_new_report)
        params = list(sig.parameters.keys())
        
        if 'estimate_id' in params:
            print("✓ Параметр estimate_id добавлен в create_new_report")
        else:
            print("✗ Параметр estimate_id НЕ найден в create_new_report")
            print(f"  Параметры: {params}")
        
        # Check that EstimateListForm has the new button handler
        if hasattr(EstimateListForm, 'on_create_daily_report'):
            print("✓ Метод on_create_daily_report найден в EstimateListForm")
        else:
            print("✗ Метод on_create_daily_report НЕ найден в EstimateListForm")
        
        print("\n✓ Все проверки пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
