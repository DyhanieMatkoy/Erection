# Tasks - Work List Improvements

## Implementation

- [x] 1. Implement Navigation Shortcuts
  - Override `eventFilter` or `keyPressEvent` in `WorkListForm`.
  - Handle `Qt.Key.Key_Left` to call `go_up()`.
  - Handle `Qt.Key.Key_Right` to call `go_down()` if a group is selected.

- [x] 2. Update UI Layout
  - Move `up_button` to the beginning of `search_layout`.
  - Set icon using `QStyle.StandardPixmap.SP_ArrowUp`.
  - Remove text label and add tooltip.

- [x] 3. Fix Search Logic
  - Modify `WorkRepository.search_by_name` to use `OR` condition for `name` and `code`.
  - Ensure case-insensitive search (`ilike`) for both fields.
