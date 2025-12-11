# Requirements - Work List Improvements

## Overview
Improvements to the Work List interface to enhance navigation and usability.

## Requirements

### 1. Navigation Shortcuts
- **Arrow Keys**:
  - **Right Arrow**: If a group is selected, drill down into the group (same as Enter or Double Click on a group).
  - **Left Arrow**: Go up one level in the hierarchy (same as "Up" button).
- These shortcuts should work when the table has focus.

### 2. UI Adjustments
- **Up Button**:
  - Move the "Up" (Вверх) button to the left of the search bar.
  - Change the button label from text "Вверх" to a standard "Arrow Up" icon.
  - Add tooltip "На уровень выше".

### 3. Search Functionality
- **Search Scope**:
  - Search should match text against both **Name** (Наименование) and **Code** (Код).
  - Example: Searching for "1.01-00006" should find the work with that code.
