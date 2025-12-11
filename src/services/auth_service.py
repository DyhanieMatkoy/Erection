"""Authentication service"""
from typing import Optional
import hashlib
from ..data.repositories.user_repository import UserRepository
from ..data.models.user import User
from ..data.database_manager import DatabaseManager

# TEMPORARY: Using SHA256 for debugging (no bcrypt issues)
# TODO: Switch back to bcrypt after fixing the issue
USE_SIMPLE_HASH = True

def simple_hash(password: str) -> str:
    """Simple SHA256 hash for debugging (no salt, not secure for production)"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def simple_verify(password: str, hashed: str) -> bool:
    """Verify password against SHA256 hash"""
    return simple_hash(password) == hashed





class AuthService:
    _instance = None
    _current_user: Optional[User] = None
    _current_person_id: Optional[int] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def login(self, username: str, password: str) -> Optional[User]:
        """Login user"""
        # Debug logging
        print(f"[DEBUG] Login attempt for username: {username}")
        print(f"[DEBUG] Password length: {len(password)} bytes")
        print(f"[DEBUG] Password first 20 chars: {password[:20]}")
        
        repo = UserRepository()
        user = repo.find_by_username(username)
        
        if not user:
            print(f"[DEBUG] User not found")
            return None
        
        print(f"[DEBUG] User found, hash length: {len(user.password_hash)} bytes")
        print(f"[DEBUG] Hash starts with: {user.password_hash[:30]}")
        print(f"[DEBUG] About to verify password...")
        
        # Verify password
        try:
            if USE_SIMPLE_HASH:
                result = simple_verify(password, user.password_hash)
            else:
                # Bcrypt path (for later)
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                result = pwd_context.verify(password, user.password_hash)
            
            print(f"[DEBUG] Verification result: {result}")
            if not result:
                return None
        except Exception as e:
            print(f"[DEBUG] Verification error: {e}")
            print(f"[DEBUG] Error type: {type(e).__name__}")
            return None
        
        self._current_user = user
        self._load_person_id()
        return user
    
    def logout(self):
        """Logout current user"""
        self._current_user = None
        self._current_person_id = None
    
    def current_user(self) -> Optional[User]:
        """Get current user"""
        return self._current_user
    
    def current_person_id(self) -> Optional[int]:
        """Get current user's person ID"""
        return self._current_person_id
    
    def has_permission(self, action: str, resource: str = None, resource_id: int = None) -> bool:
        """
        Check if current user has permission for an action
        
        Args:
            action: Action to check (view, create, edit, delete, post, manage_references)
            resource: Resource type (estimate, daily_report, reference, analytics, settings)
            resource_id: Optional resource ID for ownership checks
        
        Returns:
            bool: True if user has permission
        """
        if not self._current_user:
            return False
        
        role = self._current_user.role
        
        # Administrators have full access
        if role == "Администратор":
            return True
        
        # Руководитель (Manager) permissions
        if role == "Руководитель":
            # Managers can do everything except manage system settings
            if action == "manage_system":
                return False
            return True
        
        # Бригадир (Foreman) permissions
        if role == "Бригадир":
            # Can view, create, edit own estimates
            if resource == "estimate":
                if action in ["view", "create"]:
                    return True
                if action in ["edit", "delete", "post"] and resource_id:
                    return self._can_access_estimate(resource_id)
                return False
            
            # Can view, create, edit own daily reports
            if resource == "daily_report":
                if action in ["view", "create"]:
                    return True
                if action in ["edit", "delete", "post"] and resource_id:
                    return self._can_access_daily_report(resource_id)
                return False
            
            # Can view analytics for own data
            if resource == "analytics" and action == "view":
                return True
            
            # Cannot manage references or settings
            if resource in ["reference", "settings"]:
                return False
            
            return False
        
        # Сотрудник (Employee) permissions
        if role == "Сотрудник":
            # Can only view estimates (read-only)
            if resource == "estimate" and action == "view":
                return True
            
            # Can only view own daily reports (where they are executor)
            if resource == "daily_report" and action == "view":
                return True
            
            # Can view analytics for own data
            if resource == "analytics" and action == "view":
                return True
            
            # Cannot create, edit, delete, or manage anything
            return False
        
        return False
    
    def can_create_estimate(self) -> bool:
        """Check if user can create estimates"""
        return self.has_permission("create", "estimate")
    
    def can_edit_estimate(self, estimate_id: int) -> bool:
        """Check if user can edit a specific estimate"""
        return self.has_permission("edit", "estimate", estimate_id)
    
    def can_delete_estimate(self, estimate_id: int) -> bool:
        """Check if user can delete a specific estimate"""
        return self.has_permission("delete", "estimate", estimate_id)
    
    def can_post_estimate(self, estimate_id: int) -> bool:
        """Check if user can post a specific estimate"""
        return self.has_permission("post", "estimate", estimate_id)
    
    def can_create_daily_report(self) -> bool:
        """Check if user can create daily reports"""
        return self.has_permission("create", "daily_report")
    
    def can_edit_daily_report(self, report_id: int) -> bool:
        """Check if user can edit a specific daily report"""
        return self.has_permission("edit", "daily_report", report_id)
    
    def can_delete_daily_report(self, report_id: int) -> bool:
        """Check if user can delete a specific daily report"""
        return self.has_permission("delete", "daily_report", report_id)
    
    def can_post_daily_report(self, report_id: int) -> bool:
        """Check if user can post a specific daily report"""
        return self.has_permission("post", "daily_report", report_id)
    
    def can_manage_references(self) -> bool:
        """Check if user can manage reference data"""
        return self.has_permission("manage_references", "reference")
    
    def can_view_analytics(self) -> bool:
        """Check if user can view analytics"""
        return self.has_permission("view", "analytics")
    
    def can_manage_settings(self) -> bool:
        """Check if user can manage settings"""
        return self.has_permission("manage_system", "settings")
    
    def _can_access_estimate(self, estimate_id: int) -> bool:
        """Check if current user can access a specific estimate"""
        if not self._current_user or not self._current_person_id:
            return False
        
        # Administrators and Managers can access all
        if self._current_user.role in ["Администратор", "Руководитель"]:
            return True
        
        # Foremen can only access estimates where they are responsible
        if self._current_user.role == "Бригадир":
            db = DatabaseManager().get_connection()
            cursor = db.cursor()
            cursor.execute("""
                SELECT responsible_id FROM estimates WHERE id = ?
            """, (estimate_id,))
            row = cursor.fetchone()
            if row and row['responsible_id'] == self._current_person_id:
                return True
        
        return False
    
    def _can_access_daily_report(self, report_id: int) -> bool:
        """Check if current user can access a specific daily report"""
        if not self._current_user or not self._current_person_id:
            return False
        
        # Administrators and Managers can access all
        if self._current_user.role in ["Администратор", "Руководитель"]:
            return True
        
        # Foremen can access reports where they are the foreman
        if self._current_user.role == "Бригадир":
            db = DatabaseManager().get_connection()
            cursor = db.cursor()
            cursor.execute("""
                SELECT foreman_id FROM daily_reports WHERE id = ?
            """, (report_id,))
            row = cursor.fetchone()
            if row and row['foreman_id'] == self._current_person_id:
                return True
        
        # Employees can access reports where they are an executor
        if self._current_user.role == "Сотрудник":
            db = DatabaseManager().get_connection()
            cursor = db.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM daily_report_lines drl
                INNER JOIN daily_report_executors dre ON drl.id = dre.report_line_id
                WHERE drl.daily_report_id = ? AND dre.executor_id = ?
            """, (report_id, self._current_person_id))
            row = cursor.fetchone()
            if row and row['count'] > 0:
                return True
        
        return False
    
    def is_foreman(self) -> bool:
        """Check if current user is a foreman (бригадир)"""
        if not self._current_user:
            return False
        return self._current_user.role == "Бригадир"
    
    def is_employee(self) -> bool:
        """Check if current user is an employee (сотрудник)"""
        if not self._current_user:
            return False
        return self._current_user.role == "Сотрудник"
    
    def _load_person_id(self):
        """Load person ID for current user"""
        if not self._current_user:
            self._current_person_id = None
            return
        
        db = DatabaseManager().get_connection()
        cursor = db.cursor()
        cursor.execute("""
            SELECT id FROM persons 
            WHERE user_id = ? AND marked_for_deletion = 0
        """, (self._current_user.id,))
        
        row = cursor.fetchone()
        if row:
            self._current_person_id = row['id']
        else:
            self._current_person_id = None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        if USE_SIMPLE_HASH:
            return simple_hash(password)
        else:
            # Bcrypt path (for later)
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.hash(password)
