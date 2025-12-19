/**
 * Standard icons for list form buttons
 * Provides consistent SVG icons across the application
 */

export interface IconProps {
  class?: string
  size?: string
}

export const icons = {
  // Standard CRUD operations
  create: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  `,
  
  copy: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  `,
  
  edit: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  `,
  
  delete: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
    </svg>
  `,
  
  // Document lifecycle operations
  post: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
    </svg>
  `,
  
  unpost: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
    </svg>
  `,
  
  // Other common operations
  refresh: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  `,
  
  print: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
    </svg>
  `,
  
  search: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  `,
  
  filter: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
    </svg>
  `,
  
  export: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  `,
  
  import: (props: IconProps = {}) => `
    <svg class="${props.class || 'h-5 w-5'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v6m0 0l-3-3m3 3l3-3M7 19a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V17a2 2 0 01-2 2H7z" />
    </svg>
  `
}

/**
 * Get icon HTML string for a specific action
 */
export function getIcon(name: keyof typeof icons, props?: IconProps): string {
  return icons[name](props)
}

/**
 * Icon names for standard list form actions
 */
export const ICON_NAMES = {
  CREATE: 'create' as const,
  COPY: 'copy' as const,
  EDIT: 'edit' as const,
  DELETE: 'delete' as const,
  POST: 'post' as const,
  UNPOST: 'unpost' as const,
  REFRESH: 'refresh' as const,
  PRINT: 'print' as const,
  SEARCH: 'search' as const,
  FILTER: 'filter' as const,
  EXPORT: 'export' as const,
  IMPORT: 'import' as const,
} as const