# Design - Work List Improvements

## Navigation Shortcuts
- **Implementation**: Use `eventFilter` on the `QTableWidget` (`self.table_view`).
- **Logic**:
  - Intercept `KeyPress` events.
  - `Key_Left`: Check `current_parent_id`. If set, navigate up.
  - `Key_Right`: Get selected row. Check `UserRole` data. If `is_group` is true, navigate down.
- **Reasoning**: `QTableWidget` consumes arrow keys for internal navigation. Using `eventFilter` allows us to intercept specific keys while letting others (Up/Down) pass through for row navigation.

## UI Layout
- **Button Placement**: Place `up_button` before the search label in `search_layout`.
- **Icon**: Use `self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp)` for consistency with OS theme.

## Search Logic
- **Repository**: Update `WorkRepository.search_by_name`.
- **Query**:
  ```python
  session.query(...)
      .filter(or_(
          Work.name.ilike(f'%{search_term}%'),
          Work.code.ilike(f'%{search_term}%')
      ))
  ```
- **Dependencies**: Import `or_` from `sqlalchemy`.
