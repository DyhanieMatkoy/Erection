// Reference types
export interface Counterparty {
  id: number
  name: string
  parent_id: number | null
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface Object {
  id: number
  name: string
  address?: string
  owner_id?: number | null
  parent_id: number | null
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface Work {
  id: number
  name: string
  code?: string
  unit?: string
  unit_id?: number
  price?: number
  labor_rate?: number
  parent_id: number | null
  is_group: boolean
  is_deleted: boolean
  marked_for_deletion?: boolean
  created_at: string
  updated_at: string
  cost_items?: CostItemMaterial[]
  materials?: CostItemMaterial[]
}

export interface CostItem {
  id: number
  parent_id: number | null
  code?: string
  description: string
  is_folder: boolean
  price: number
  unit?: string
  unit_id?: number
  unit_name?: string
  labor_coefficient: number
  marked_for_deletion: boolean
  created_at: string
  modified_at: string
}

export interface Material {
  id: number
  code?: string
  description: string
  price: number
  unit?: string
  unit_id?: number
  unit_name?: string
  marked_for_deletion: boolean
  created_at: string
  modified_at: string
}

export interface Unit {
  id: number
  name: string
  description?: string
  marked_for_deletion: boolean
}

export interface CostItemMaterial {
  id: number
  work_id: number
  cost_item_id: number
  material_id: number | null
  quantity_per_unit: number
  work?: Work
  cost_item?: CostItem
  material?: Material
}

export interface Person {
  id: number
  full_name: string
  position?: string
  parent_id: number | null
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface Organization {
  id: number
  name: string
  parent_id: number | null
  is_deleted: boolean
  created_at: string
  updated_at: string
}

// Document types
export interface EstimateLine {
  id?: number
  estimate_id?: number
  work_id: number | null
  work_name?: string
  quantity: number
  unit?: string
  price: number
  sum: number
  labor: number
  parent_id: number | null
  is_group: boolean
  order_num: number
}

export interface Estimate {
  id?: number
  number: string
  date: string
  customer_id: number
  customer_name?: string
  object_id: number
  object_name?: string
  contractor_id: number
  contractor_name?: string
  responsible_id: number
  responsible_name?: string
  total_sum: number
  total_labor: number
  is_posted: boolean
  posted_at: string | null
  is_deleted: boolean
  created_at?: string
  updated_at?: string
  lines?: EstimateLine[]
}

export interface DailyReportLine {
  id?: number
  daily_report_id?: number
  line_number?: number
  estimate_line_id: number
  work_id?: number
  work_name?: string
  planned_labor: number
  actual_labor: number
  deviation: number
  executors?: number[]
  executor_names?: string[]
}

export interface DailyReport {
  id?: number
  date: string
  estimate_id: number
  estimate_number?: string
  foreman_id: number
  foreman_name?: string
  is_posted: boolean
  posted_at: string | null
  is_deleted: boolean
  created_at?: string
  updated_at?: string
  lines?: DailyReportLine[]
}

// Timesheet types
export interface TimesheetLine {
  id?: number
  timesheet_id?: number
  line_number: number
  employee_id: number
  employee_name?: string
  hourly_rate: number
  days: Record<number, number> // {1: 8.0, 2: 7.5, ...}
  total_hours: number
  total_amount: number
}

export interface Timesheet {
  id?: number
  number: string
  date: string
  object_id: number
  object_name?: string
  estimate_id: number
  estimate_number?: string
  foreman_id: number
  foreman_name?: string
  month_year: string // "YYYY-MM"
  is_posted: boolean
  posted_at: string | null
  marked_for_deletion: boolean
  created_at?: string
  modified_at?: string
  lines?: TimesheetLine[]
}

// Register types
export interface WorkExecutionMovement {
  period: string
  object_id: number
  object_name: string
  estimate_id: number
  estimate_number: string
  work_id: number
  work_name: string
  income_quantity: number
  income_sum: number
  expense_quantity: number
  expense_sum: number
  balance_quantity: number
  balance_sum: number
}


// ============================================================================
// Work Composition Types
// ============================================================================

/**
 * Work composition detail with cost items and materials
 */
export interface WorkComposition {
  work_id: number
  work_name: string
  work_code: string | null
  work_unit: string | null
  work_price: number
  work_labor_rate: number
  cost_items: CostItemMaterial[]
  materials: CostItemMaterial[]
  total_cost_items_price: number
  total_materials_cost: number
  total_cost: number
}
