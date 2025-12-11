# Requirements Document - Timesheet (Табель)

## Introduction

Документ "Табель" предназначен для учета рабочего времени сотрудников бригады за месяц. Бригадир вводит данные о количестве отработанных часов каждым сотрудником по дням месяца. При проведении документ создает записи в регистре начислений и удержаний.

## Glossary

- **Timesheet_System**: Система управления табелями учета рабочего времени
- **Timesheet_Document**: Документ табеля учета рабочего времени
- **Payroll_Register**: Регистр начислений и удержаний по сотрудникам
- **Foreman**: Бригадир, ответственный за ввод данных табеля
- **Employee**: Сотрудник бригады, физическое лицо
- **Work_Object**: Объект строительства
- **Estimate**: Смета
- **Hourly_Rate**: Тарифная ставка за час работы
- **Working_Hours**: Количество отработанных часов
- **Month_Period**: Календарный месяц, за который ведется учет

## Requirements

### Requirement 1: Создание и редактирование табеля

**User Story:** Как бригадир, я хочу создавать и редактировать табели учета рабочего времени, чтобы фиксировать отработанное время сотрудников моей бригады.

#### Acceptance Criteria

1. WHEN Foreman создает новый Timesheet_Document, THE Timesheet_System SHALL создать документ с уникальным номером и текущей датой
2. THE Timesheet_System SHALL требовать заполнения реквизитов: номер, дата, Work_Object, Estimate
3. WHEN Foreman добавляет Employee в табличную часть, THE Timesheet_System SHALL отобразить поля: Employee, Hourly_Rate, колонки для каждого дня Month_Period
4. THE Timesheet_System SHALL автоматически определять количество дней в Month_Period на основе даты документа
5. THE Timesheet_System SHALL создавать колонки для ввода Working_Hours для каждого дня месяца

### Requirement 2: Расчет итоговых показателей

**User Story:** Как бригадир, я хочу видеть автоматически рассчитанные итоги по каждому сотруднику, чтобы контролировать общее отработанное время и начисленную сумму.

#### Acceptance Criteria

1. WHEN Foreman вводит Working_Hours для любого дня, THE Timesheet_System SHALL автоматически пересчитать колонку "Итого"
2. THE Timesheet_System SHALL рассчитывать "Итого" как сумму всех Working_Hours за Month_Period для Employee
3. THE Timesheet_System SHALL рассчитывать "Сумма" по формуле: Итого × Hourly_Rate
4. WHEN Foreman изменяет Hourly_Rate, THE Timesheet_System SHALL автоматически пересчитать "Сумма" для данного Employee
5. THE Timesheet_System SHALL отображать рассчитанные значения в режиме реального времени

### Requirement 3: Проведение документа

**User Story:** Как бригадир, я хочу проводить табель, чтобы данные о начислениях были зафиксированы в системе.

#### Acceptance Criteria

1. WHEN Foreman проводит Timesheet_Document, THE Timesheet_System SHALL создать записи в Payroll_Register для каждого Employee
2. THE Timesheet_System SHALL создавать записи с полями: Work_Object, Estimate, Employee, дата, отработано (часы), сумма
3. WHEN Timesheet_Document проводится, THE Timesheet_System SHALL создать по одной записи в Payroll_Register для каждого дня с ненулевыми Working_Hours
4. THE Timesheet_System SHALL установить флаг is_posted в значение TRUE после успешного проведения
5. THE Timesheet_System SHALL сохранить дату и время проведения в поле posted_at

### Requirement 4: Контроль уникальности записей

**User Story:** Как система, я должна предотвращать дублирование записей в регистре начислений, чтобы обеспечить корректность данных.

#### Acceptance Criteria

1. WHEN Timesheet_System создает запись в Payroll_Register, THE Timesheet_System SHALL проверить уникальность комбинации (Work_Object, Estimate, Employee, дата)
2. IF запись с такой комбинацией уже существует в Payroll_Register, THEN THE Timesheet_System SHALL отменить проведение Timesheet_Document
3. WHEN проведение отменяется из-за дубликата, THE Timesheet_System SHALL отобразить сообщение об ошибке с указанием конфликтующих записей
4. THE Timesheet_System SHALL сохранить Timesheet_Document в непроведенном состоянии при обнаружении дубликата
5. WHEN Foreman отменяет проведение Timesheet_Document, THE Timesheet_System SHALL удалить все связанные записи из Payroll_Register

### Requirement 5: Права доступа

**User Story:** Как бригадир, я хочу иметь доступ только к табелям моей бригады, чтобы данные других бригад были защищены.

#### Acceptance Criteria

1. WHEN Foreman открывает список табелей, THE Timesheet_System SHALL отображать только табели, где Foreman является ответственным
2. WHEN Foreman создает новый Timesheet_Document, THE Timesheet_System SHALL автоматически установить Foreman как ответственного
3. THE Timesheet_System SHALL запретить Foreman редактировать табели других бригадиров
4. WHEN администратор открывает список табелей, THE Timesheet_System SHALL отображать все табели без ограничений
5. THE Timesheet_System SHALL разрешить администратору редактировать любые табели

### Requirement 6: Валидация данных

**User Story:** Как система, я должна проверять корректность вводимых данных, чтобы предотвратить ошибки учета.

#### Acceptance Criteria

1. WHEN Foreman вводит Working_Hours, THE Timesheet_System SHALL принимать только неотрицательные числовые значения
2. THE Timesheet_System SHALL ограничить максимальное значение Working_Hours до 24 часов в день
3. WHEN Foreman вводит Hourly_Rate, THE Timesheet_System SHALL принимать только положительные числовые значения
4. THE Timesheet_System SHALL требовать заполнения хотя бы одного дня с ненулевыми Working_Hours перед проведением
5. WHEN Foreman пытается провести пустой Timesheet_Document, THE Timesheet_System SHALL отобразить сообщение об ошибке

### Requirement 7: Интерфейс табличной части

**User Story:** Как бригадир, я хочу удобно вводить данные по дням месяца, чтобы быстро заполнять табель.

#### Acceptance Criteria

1. THE Timesheet_System SHALL отображать заголовки колонок с номерами дней месяца (1, 2, 3, ..., 31)
2. THE Timesheet_System SHALL выделять выходные дни (суббота, воскресенье) другим цветом в заголовках
3. WHEN Month_Period содержит менее 31 дня, THE Timesheet_System SHALL скрывать неиспользуемые колонки
4. THE Timesheet_System SHALL поддерживать навигацию по ячейкам с помощью клавиш Tab и Enter
5. THE Timesheet_System SHALL отображать итоговую строку с суммой по всем сотрудникам

### Requirement 8: Отмена проведения

**User Story:** Как бригадир, я хочу иметь возможность отменить проведение табеля, чтобы исправить ошибки.

#### Acceptance Criteria

1. WHEN Foreman отменяет проведение Timesheet_Document, THE Timesheet_System SHALL удалить все записи из Payroll_Register, созданные этим документом
2. THE Timesheet_System SHALL установить флаг is_posted в значение FALSE
3. THE Timesheet_System SHALL очистить поле posted_at
4. WHEN отмена проведения выполнена, THE Timesheet_System SHALL разрешить редактирование Timesheet_Document
5. THE Timesheet_System SHALL запретить удаление проведенного Timesheet_Document без предварительной отмены проведения

### Requirement 9: Печатная форма

**User Story:** Как бригадир, я хочу распечатывать табель, чтобы предоставлять отчетность в бумажном виде.

#### Acceptance Criteria

1. WHEN Foreman запрашивает печать Timesheet_Document, THE Timesheet_System SHALL сгенерировать печатную форму в формате Excel
2. THE Timesheet_System SHALL включить в печатную форму: номер, дату, Work_Object, Estimate, таблицу с сотрудниками и отработанными часами
3. THE Timesheet_System SHALL отображать в печатной форме итоговые значения по каждому сотруднику
4. THE Timesheet_System SHALL включить общую итоговую строку с суммой по всем сотрудникам
5. THE Timesheet_System SHALL поддерживать кириллицу в печатной форме

### Requirement 10: Интеграция с существующими данными

**User Story:** Как система, я должна использовать существующие справочники и документы, чтобы обеспечить целостность данных.

#### Acceptance Criteria

1. WHEN Foreman выбирает Work_Object, THE Timesheet_System SHALL отображать список из справочника "Объекты"
2. WHEN Foreman выбирает Estimate, THE Timesheet_System SHALL отображать список смет, связанных с выбранным Work_Object
3. WHEN Foreman выбирает Employee, THE Timesheet_System SHALL отображать список из справочника "Физические лица"
4. THE Timesheet_System SHALL автоматически подставлять Hourly_Rate из справочника "Физические лица", если он там указан
5. THE Timesheet_System SHALL разрешить Foreman изменять Hourly_Rate в табеле независимо от справочника

### Requirement 11: Фильтрация сотрудников по бригаде

**User Story:** Как бригадир, я хочу видеть в списке подбора только сотрудников своей бригады или всех сотрудников, чтобы упростить заполнение табеля.

#### Acceptance Criteria

1. THE Timesheet_System SHALL предоставить Foreman настройку фильтрации сотрудников с двумя режимами: "Только моя бригада" и "Все сотрудники"
2. WHEN настройка установлена в "Только моя бригада", THE Timesheet_System SHALL отображать только Employee, где Foreman указан как руководитель, плюс Employee без руководителя
3. WHEN настройка установлена в "Все сотрудники", THE Timesheet_System SHALL отображать всех Employee из справочника
4. THE Timesheet_System SHALL сохранять выбранную настройку фильтрации для каждого Foreman
5. THE Timesheet_System SHALL применять фильтрацию во всех формах подбора сотрудников

### Requirement 12: Автозаполнение из ежедневных отчетов

**User Story:** Как бригадир, я хочу автоматически заполнить табличную часть табеля сотрудниками из ежедневных отчетов, чтобы не вводить данные вручную.

#### Acceptance Criteria

1. WHEN Foreman выбирает Work_Object и Estimate в Timesheet_Document, THE Timesheet_System SHALL предоставить функцию "Заполнить из ежедневных отчетов"
2. WHEN Foreman активирует функцию заполнения, THE Timesheet_System SHALL найти все Daily_Report_Document по выбранным Work_Object и Estimate за Month_Period
3. THE Timesheet_System SHALL извлечь уникальный список Employee из найденных Daily_Report_Document
4. THE Timesheet_System SHALL добавить каждого Employee в табличную часть Timesheet_Document, если он еще не добавлен
5. THE Timesheet_System SHALL заполнить Working_Hours для каждого Employee на основе данных из Daily_Report_Document (actual_labor)
6. WHEN в Daily_Report_Document указано несколько Employee для одной работы, THE Timesheet_System SHALL распределить actual_labor пропорционально между ними
7. THE Timesheet_System SHALL запросить подтверждение перед заполнением, если табличная часть уже содержит данные
