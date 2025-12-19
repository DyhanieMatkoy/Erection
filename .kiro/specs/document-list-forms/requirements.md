# Requirements for Document List Forms in 1C Platform

## Introduction

Document list forms are a key element of the user interface in the 1C platform, providing efficient display, navigation, and management of document collections. This specification defines requirements for designing and implementing document list forms to ensure a consistent user experience and high performance.

## Glossary

- **List_Form**: Interface element of the 1C platform for displaying tabular document data
- **Document**: Metadata object of the 1C platform representing a business document with temporal characteristics
- **Platform_System**: Runtime environment of the 1C:Enterprise platform
- **User**: End user of the system working with documents
- **Administrator**: User with rights to configure the system and forms
- **List_Column**: Column in the tabular representation of the list form
- **Quick_Filter**: Mechanism for rapid data filtering in list forms
- **Command_Bar**: Toolbar containing standard actions for working with documents
- **Table_Part**: Tabular section within a document form

## Requirements

### Requirement 1

**User Story:** As a system user, I want to see a list of documents in a convenient tabular format, so that I can quickly find and analyze the information I need.

#### Acceptance Criteria

1. WHEN a user opens a document list form THEN the Platform_System SHALL display a tabular representation with configured columns
2. WHEN the list form contains more than 1000 records THEN the Platform_System SHALL use a pagination mechanism for data loading
3. WHEN a user changes the window size THEN the List_Form SHALL adapt column widths proportionally
4. WHEN data in the list is updated THEN the Platform_System SHALL automatically refresh the display without losing the current position
5. WHEN the list is empty THEN the List_Form SHALL display an informative message about the absence of data

### Requirement 2

**User Story:** As a user, I want to customize the display of columns in the document list, so that I can see only information relevant to my work.

#### Acceptance Criteria

1. WHEN a user right-clicks on a column header THEN the Platform_System SHALL display a context menu with configuration options
2. WHEN a user hides a column THEN the List_Form SHALL save this setting in user preferences and apply it when the form is next opened
3. WHEN a user changes column order by dragging THEN the Platform_System SHALL save the new order in user settings and restore it in subsequent sessions
4. WHEN a user drags a column header edge to resize the column THEN the List_Form SHALL adjust the column width in real-time and save the new width in user settings for subsequent form openings
5. WHEN a user hovers over a column header edge THEN the Platform_System SHALL display a resize cursor to indicate the column can be resized by dragging
6. WHEN a user resets column settings THEN the Platform_System SHALL restore default settings

### Requirement 3

**User Story:** As a user, I want to quickly filter and sort documents in the list, so that I can efficiently find the information I need.

#### Acceptance Criteria

1. WHEN a user clicks on a column header THEN the Platform_System SHALL apply sorting by that column and save the sorting setting between sessions
2. WHEN a user enters text in the quick search field THEN the List_Form SHALL filter records in real time
3. WHEN the list form opens for the first time THEN the Platform_System SHALL set a date filter from the last document date to infinity
4. WHEN multiple filters are applied THEN the List_Form SHALL display an indicator of active filters
5. WHEN a user clears all filters THEN the Platform_System SHALL restore the full document list

### Requirement 4

**User Story:** As a user, I want to perform bulk operations on documents in the list, so that I can increase work efficiency.

#### Acceptance Criteria

1. WHEN a user selects multiple documents using Ctrl+Click THEN the List_Form SHALL highlight the selected rows
2. WHEN a user selects a range of documents using Shift+Click THEN the Platform_System SHALL highlight all rows in the range
3. WHEN multiple documents are selected THEN the List_Form SHALL activate bulk operation buttons
4. WHEN a user performs a bulk operation THEN the Platform_System SHALL display execution progress
5. WHEN a bulk operation is completed THEN the List_Form SHALL update the status of processed documents

### Requirement 5

**User Story:** As a user, I want to see additional information about a document without opening its form, so that I can make quick decisions.

#### Acceptance Criteria

1. WHEN a user hovers over a document row THEN the Platform_System SHALL display a tooltip with additional information
2. WHEN a user clicks the preview button THEN the List_Form SHALL display a panel with detailed information
3. WHEN a document has attachments THEN the Platform_System SHALL display a corresponding indicator in the list
4. WHEN a document is being processed THEN the List_Form SHALL show a status indicator
5. WHEN a document has validation errors THEN the Platform_System SHALL highlight the row with an appropriate color

### Requirement 6

**User Story:** As a system administrator, I want to configure the behavior of document list forms, so that I can adapt them to the specifics of the organization's business processes.

#### Acceptance Criteria

1. WHEN an administrator opens the list form designer THEN the Platform_System SHALL provide an interface for configuring columns and their properties
2. WHEN an administrator sets a column as mandatory THEN the List_Form SHALL prohibit its hiding by users
3. WHEN an administrator configures conditional formatting THEN the Platform_System SHALL apply styles to corresponding rows
4. WHEN an administrator sets access restrictions THEN the List_Form SHALL hide inaccessible columns for corresponding users
5. WHEN an administrator saves form settings THEN the Platform_System SHALL apply them to all new users

### Requirement 7

**User Story:** As a user, I want to export data from the document list in various formats, so that I can use them in other applications.

#### Acceptance Criteria

1. WHEN a user selects export to Excel THEN the Platform_System SHALL create a file preserving column formatting
2. WHEN a user exports filtered data THEN the List_Form SHALL include only visible records in the export
3. WHEN exporting large amounts of data THEN the Platform_System SHALL display operation progress
4. WHEN export is completed THEN the List_Form SHALL offer to open or save the created file
5. WHEN a user cancels export THEN the Platform_System SHALL correctly interrupt the operation without creating a file

### Requirement 8

**User Story:** As a user, I want to use a command bar above the document list to perform standard actions, so that I can efficiently manage documents.

#### Acceptance Criteria

1. WHEN a user opens a document list form THEN the Platform_System SHALL display a command bar with standard CRUD action buttons including Create, Copy, Edit, Delete, Post, Print
2. WHEN a user clicks the "Print" button THEN the List_Form SHALL provide printing options for selected documents
3. WHEN a user customizes the command bar THEN the Platform_System SHALL move hidden commands to the "More" submenu
4. WHEN a user selects a command from the "More" submenu THEN the List_Form SHALL execute the corresponding action on selected documents
5. WHEN a user saves command bar settings THEN the Platform_System SHALL save them in user settings and automatically apply them in all subsequent form openings

### Requirement 9

**User Story:** As a user, I want to configure the displayed date interval in the document list, so that I can control the volume of loaded data and focus on the needed period.

#### Acceptance Criteria

1. WHEN a user clicks on the current period indicator THEN the Platform_System SHALL open a date interval selection window
2. WHEN a user changes the period start date THEN the List_Form SHALL update the document list according to the new range
3. WHEN a user changes the period end date THEN the Platform_System SHALL apply filtering up to the specified date inclusive
4. WHEN a user saves period settings THEN the List_Form SHALL use them as default settings for the current list
5. WHEN a user resets period settings THEN the Platform_System SHALL restore filtering from the last document date to infinity

### Requirement 10

**User Story:** As a user, I want to configure the display of table parts in document forms similarly to lists, so that I have a consistent interface for working with tabular data.

#### Acceptance Criteria

1. WHEN a user opens a document form with a table part THEN the Platform_System SHALL apply saved user settings for table part columns
2. WHEN a user drags a table part column header edge to resize the column THEN the Document_Form SHALL adjust the column width in real-time and save these settings in user preferences for this document type
3. WHEN a user configures sorting in a table part THEN the Platform_System SHALL save the sort order and apply it when opening subsequent documents of this type
4. WHEN a user uses filtering in a table part THEN the Document_Form SHALL provide the same quick search capabilities as in list forms
5. WHEN a user resets table part settings THEN the Platform_System SHALL restore default settings defined by the administrator for this document type

### Requirement 11

**User Story:** As a user, I want to access standard CRUD commands from both document list forms and document table parts, so that I have consistent functionality across all tabular interfaces.

#### Acceptance Criteria

1. WHEN a user works with a document list or table part THEN the Platform_System SHALL provide standard commands: Create, Copy, Edit, Delete, Post (for documents), Unpost (for documents)
2. WHEN a user works with document lists THEN the Command_Bar SHALL include additional commands: Print, Print Preview, Email Send, Find in List, Set Filter, Clear Filter, Configure List, Export List
3. WHEN a user works with table parts THEN the Platform_System SHALL provide row-level commands: Add Row, Copy Row, Delete Row, Move Up, Move Down
4. WHEN commands are not applicable to current context THEN the Platform_System SHALL disable or hide inappropriate commands
5. WHEN a user customizes command visibility THEN the Platform_System SHALL maintain command availability while allowing personalization of the interface

### Requirement 12: Keyboard Shortcuts

**User Story:** As a user, I want to use keyboard shortcuts for common actions in lists and fields, so that I can work faster without using the mouse.

#### Acceptance Criteria

1. WHEN a user is in a list form, the following shortcuts SHALL be available:
   - **Ins**: Create new item
   - **F9**: Copy selected item
   - **F2**: Edit selected item
   - **Del**: Delete selected item(s)
   - **F5**: Refresh list
   - **F8**: Print selected item(s) or list
2. WHEN a user is in a reference type field (selector), the following shortcuts SHALL be available:
   - **F4**: Open selector/dropdown
   - **F2**: Start editing search substring (open dropdown and focus search)
