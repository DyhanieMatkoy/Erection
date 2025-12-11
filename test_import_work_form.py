
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

try:
    from src.views.work_form import WorkForm
    print("WorkForm imported successfully")
except Exception as e:
    print(f"Failed to import WorkForm: {e}")
    import traceback
    traceback.print_exc()
