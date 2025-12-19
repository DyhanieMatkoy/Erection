/**
 * Composable for table part printing functionality
 * 
 * Provides methods for generating print previews and handling
 * print operations for table parts in the web client.
 */

import { ref } from 'vue'

interface TableRow {
  [key: string]: any
}

interface PrintConfiguration {
  orientation: 'portrait' | 'landscape'
  scale: number
  topMargin: number
  bottomMargin: number
  leftMargin: number
  rightMargin: number
  repeatHeaders: boolean
  showGrid: boolean
  fitToWidth: boolean
  format: 'print' | 'pdf'
  maxRowsPerPage: number
  tableName?: string
}

interface PrintService {
  generatePreview: (data: TableRow[], config: PrintConfiguration) => Promise<string>
  printToPrinter: (data: TableRow[], config: PrintConfiguration) => Promise<void>
  printToPdf: (data: TableRow[], config: PrintConfiguration) => Promise<void>
  validatePrintData: (data: TableRow[]) => { isValid: boolean; error?: string }
  getPageCount: (data: TableRow[], config: PrintConfiguration) => number
}

export function useTablePartPrint(): PrintService {
  const isGenerating = ref(false)
  const isPrinting = ref(false)

  /**
   * Generate HTML preview for table printing
   */
  const generatePreview = async (
    data: TableRow[], 
    config: PrintConfiguration
  ): Promise<string> => {
    isGenerating.value = true
    
    try {
      // Validate data
      const validation = validatePrintData(data)
      if (!validation.isValid) {
        throw new Error(validation.error || 'Invalid data')
      }

      // Generate HTML content
      const html = await generateHtmlContent(data, config)
      return html
    } finally {
      isGenerating.value = false
    }
  }

  /**
   * Print to physical printer
   */
  const printToPrinter = async (
    data: TableRow[], 
    config: PrintConfiguration
  ): Promise<void> => {
    isPrinting.value = true
    
    try {
      const html = await generateHtmlContent(data, config)
      
      // Create a new window for printing
      const printWindow = window.open('', '_blank')
      if (!printWindow) {
        throw new Error('Не удалось открыть окно печати')
      }

      // Write HTML content to print window
      printWindow.document.write(html)
      printWindow.document.close()

      // Wait for content to load, then print
      printWindow.onload = () => {
        printWindow.print()
        printWindow.close()
      }
    } finally {
      isPrinting.value = false
    }
  }

  /**
   * Print to PDF file
   */
  const printToPdf = async (
    data: TableRow[], 
    config: PrintConfiguration
  ): Promise<void> => {
    isPrinting.value = true
    
    try {
      const html = await generateHtmlContent(data, config)
      
      // Create a temporary window for PDF generation
      const pdfWindow = window.open('', '_blank')
      if (!pdfWindow) {
        throw new Error('Не удалось открыть окно для создания PDF')
      }

      // Write HTML content
      pdfWindow.document.write(html)
      pdfWindow.document.close()

      // Trigger browser's print to PDF functionality
      pdfWindow.onload = () => {
        pdfWindow.print()
      }
    } finally {
      isPrinting.value = false
    }
  }

  /**
   * Validate table data for printing
   */
  const validatePrintData = (data: TableRow[]): { isValid: boolean; error?: string } => {
    if (!data || !Array.isArray(data)) {
      return { isValid: false, error: 'Данные должны быть массивом' }
    }

    if (data.length === 0) {
      return { isValid: false, error: 'Нет данных для печати' }
    }

    // Check if all rows have consistent structure
    const firstRowKeys = Object.keys(data[0])
    for (let i = 1; i < data.length; i++) {
      const currentRowKeys = Object.keys(data[i])
      if (currentRowKeys.length !== firstRowKeys.length ||
          !currentRowKeys.every(key => firstRowKeys.includes(key))) {
        return { 
          isValid: false, 
          error: `Строка ${i + 1} имеет отличающуюся структуру` 
        }
      }
    }

    return { isValid: true }
  }

  /**
   * Calculate number of pages needed
   */
  const getPageCount = (data: TableRow[], config: PrintConfiguration): number => {
    if (!data || data.length === 0) return 0
    
    const rowsPerPage = config.maxRowsPerPage || 50
    return Math.ceil(data.length / rowsPerPage)
  }

  /**
   * Generate HTML content for printing
   */
  const generateHtmlContent = async (
    data: TableRow[], 
    config: PrintConfiguration
  ): Promise<string> => {
    const columns = data.length > 0 ? Object.keys(data[0]) : []
    const pages = splitDataIntoPages(data, config.maxRowsPerPage || 50)
    
    const css = generateCssStyles(config)
    const tableHtml = generateTableHtml(pages, columns, config)
    
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>${escapeHtml(config.tableName || 'Табличная часть')}</title>
        <style>${css}</style>
      </head>
      <body>
        <div class="page-container">
          ${tableHtml}
        </div>
      </body>
      </html>
    `
  }

  /**
   * Split data into pages
   */
  const splitDataIntoPages = (data: TableRow[], maxRowsPerPage: number): TableRow[][] => {
    if (data.length <= maxRowsPerPage) {
      return [data]
    }

    const pages: TableRow[][] = []
    for (let i = 0; i < data.length; i += maxRowsPerPage) {
      pages.push(data.slice(i, i + maxRowsPerPage))
    }

    return pages
  }

  /**
   * Generate CSS styles for printing
   */
  const generateCssStyles = (config: PrintConfiguration): string => {
    const gridStyle = config.showGrid ? 'border-collapse: collapse;' : 'border-collapse: separate;'
    const borderStyle = config.showGrid ? '1px solid #000;' : 'none;'
    
    const pageWidth = config.orientation === 'landscape' ? '297mm' : '210mm'
    const pageHeight = config.orientation === 'landscape' ? '210mm' : '297mm'
    
    const contentWidth = `calc(${pageWidth} - ${config.leftMargin}mm - ${config.rightMargin}mm)`

    return `
      @page {
        size: A4 ${config.orientation};
        margin: ${config.topMargin}mm ${config.rightMargin}mm ${config.bottomMargin}mm ${config.leftMargin}mm;
      }
      
      body {
        font-family: Arial, sans-serif;
        font-size: 10pt;
        margin: 0;
        padding: 0;
        line-height: 1.2;
      }
      
      .page-container {
        width: ${contentWidth};
        max-width: 100%;
      }
      
      .table-title {
        font-size: 14pt;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10mm;
        page-break-inside: avoid;
      }
      
      .table-section {
        margin-bottom: 5mm;
      }
      
      table {
        width: 100%;
        ${gridStyle}
        font-size: 9pt;
      }
      
      th, td {
        border: ${borderStyle}
        padding: 2mm;
        text-align: left;
        vertical-align: top;
        word-wrap: break-word;
        page-break-inside: avoid;
      }
      
      th {
        background-color: #f0f0f0;
        font-weight: bold;
        page-break-inside: avoid;
        page-break-after: avoid;
      }
      
      .header-row {
        page-break-inside: avoid;
        page-break-after: avoid;
      }
      
      .page-break {
        page-break-before: always;
      }
      
      .no-break {
        page-break-inside: avoid;
      }
      
      .table-continued {
        font-style: italic;
        font-size: 8pt;
        text-align: right;
        margin-bottom: 2mm;
        color: #666;
      }
      
      @media print {
        .page-container {
          width: 100%;
        }
        
        table {
          font-size: 8pt;
        }
        
        th, td {
          padding: 1mm;
        }
      }
      
      ${config.fitToWidth ? `
        table {
          table-layout: fixed;
        }
        
        th, td {
          overflow: hidden;
          text-overflow: ellipsis;
        }
      ` : ''}
    `
  }

  /**
   * Generate HTML for table content
   */
  const generateTableHtml = (
    pages: TableRow[][], 
    columns: string[], 
    config: PrintConfiguration
  ): string => {
    const parts: string[] = []
    
    // Add title
    parts.push(`<div class="table-title">${escapeHtml(config.tableName || 'Табличная часть')}</div>`)
    
    // Generate each page
    pages.forEach((pageData, pageIndex) => {
      if (pageIndex > 0) {
        parts.push('<div class="page-break"></div>')
        parts.push(`<div class="table-continued">${escapeHtml(config.tableName || 'Табличная часть')} (продолжение)</div>`)
      }
      
      parts.push('<div class="table-section">')
      parts.push('<table>')
      
      // Add header (on each page if configured)
      if (pageIndex === 0 || config.repeatHeaders) {
        parts.push('<thead>')
        parts.push(generateHeaderHtml(columns))
        parts.push('</thead>')
      }
      
      // Add table body
      parts.push('<tbody>')
      pageData.forEach(row => {
        parts.push(generateRowHtml(row, columns))
      })
      parts.push('</tbody>')
      
      parts.push('</table>')
      parts.push('</div>')
    })
    
    return parts.join('\n')
  }

  /**
   * Generate HTML for table header
   */
  const generateHeaderHtml = (columns: string[]): string => {
    const headerCells = columns.map(column => 
      `<th>${escapeHtml(column)}</th>`
    ).join('')
    
    return `<tr class="header-row">${headerCells}</tr>`
  }

  /**
   * Generate HTML for table row
   */
  const generateRowHtml = (row: TableRow, columns: string[]): string => {
    const rowCells = columns.map(column => {
      const value = row[column]
      const displayValue = value !== null && value !== undefined ? String(value) : ''
      return `<td>${escapeHtml(displayValue)}</td>`
    }).join('')
    
    return `<tr class="no-break">${rowCells}</tr>`
  }

  /**
   * Escape HTML characters
   */
  const escapeHtml = (text: string): string => {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
  }

  return {
    generatePreview,
    printToPrinter,
    printToPdf,
    validatePrintData,
    getPageCount
  }
}