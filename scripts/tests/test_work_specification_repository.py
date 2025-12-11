import sys
import os
import unittest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.data.models.sqlalchemy_models import Base, Work, Unit, WorkSpecification
from src.data.database_manager import DatabaseManager
from src.data.repositories.work_specification_repository import WorkSpecificationRepository

class TestWorkSpecificationRepository(unittest.TestCase):
    
    def setUp(self):
        # Use in-memory SQLite for testing
        self.db_manager = DatabaseManager()
        # Mock engine to use in-memory sqlite
        self.engine = create_engine('sqlite:///:memory:')
        self.db_manager._engine = self.engine
        self.db_manager._session_factory = sessionmaker(bind=self.engine)
        
        Base.metadata.create_all(self.engine)
        
        # Create test data
        Session = sessionmaker(bind=self.engine)
        session = Session()
        
        unit = Unit(name="kg")
        session.add(unit)
        session.flush()
        self.unit_id = unit.id
        
        work = Work(name="Test Work", code="W001")
        session.add(work)
        session.flush()
        self.work_id = work.id
        
        work2 = Work(name="Target Work", code="W002")
        session.add(work2)
        session.flush()
        self.target_work_id = work2.id
        
        session.commit()
        session.close()
        
        self.repo = WorkSpecificationRepository(self.db_manager)

    def test_create_and_get(self):
        data = {
            'work_id': self.work_id,
            'component_type': 'Material',
            'component_name': 'Test Material',
            'unit_id': self.unit_id,
            'consumption_rate': Decimal('1.5'),
            'unit_price': Decimal('10.0')
        }
        
        spec_id = self.repo.create(data)
        self.assertIsNotNone(spec_id)
        
        specs = self.repo.get_by_work_id(self.work_id)
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0]['component_name'], 'Test Material')
        # Check computed column if supported by sqlite version, otherwise it might be None or 0 until reloaded?
        # In SQLite computed columns are supported in recent versions.
        # But SQLAlchemy might need refresh.
        
    def test_update(self):
        data = {
            'work_id': self.work_id,
            'component_type': 'Labor',
            'component_name': 'Test Labor',
            'unit_id': self.unit_id,
            'consumption_rate': Decimal('2.0'),
            'unit_price': Decimal('50.0')
        }
        spec_id = self.repo.create(data)
        
        update_data = {
            'consumption_rate': Decimal('3.0')
        }
        result = self.repo.update(spec_id, update_data)
        self.assertTrue(result)
        
        specs = self.repo.get_by_work_id(self.work_id)
        updated_spec = next(s for s in specs if s['id'] == spec_id)
        self.assertEqual(updated_spec['consumption_rate'], Decimal('3.0'))

    def test_delete(self):
        data = {
            'work_id': self.work_id,
            'component_type': 'Equipment',
            'component_name': 'Test Equipment',
            'unit_id': self.unit_id,
            'consumption_rate': Decimal('1.0'),
            'unit_price': Decimal('100.0')
        }
        spec_id = self.repo.create(data)
        
        result = self.repo.delete(spec_id)
        self.assertTrue(result)
        
        specs = self.repo.get_by_work_id(self.work_id)
        deleted_spec = next((s for s in specs if s['id'] == spec_id), None)
        self.assertIsNone(deleted_spec) # Should be filtered out

    def test_copy_from_work(self):
        # Ensure source has specs
        specs = self.repo.get_by_work_id(self.work_id)
        if not specs:
             data = {
                'work_id': self.work_id,
                'component_type': 'Other',
                'component_name': 'Test Other',
                'unit_id': self.unit_id,
                'consumption_rate': Decimal('1.0'),
                'unit_price': Decimal('10.0')
            }
             self.repo.create(data)
        
        result = self.repo.copy_from_work(self.target_work_id, self.work_id)
        self.assertTrue(result)
        
        target_specs = self.repo.get_by_work_id(self.target_work_id)
        self.assertTrue(len(target_specs) > 0)
        
    def test_get_totals(self):
        totals = self.repo.get_totals_by_type(self.work_id)
        self.assertIsInstance(totals, dict)
        # We created Material and Labor (and maybe Equipment/Other)
        self.assertTrue('Material' in totals)

if __name__ == '__main__':
    unittest.main()
