/**
 * Tests for Table Part Command Manager Integration.
 * 
 * This module tests the integration between the row control panel and
 * the command manager, including form command discovery, registration,
 * and execution.
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { 
  TablePartCommandManager,
  CommandAvailability,
  tableCommand,
  createCommandContext,
  createCommandManager,
  type FormCommand,
  type CommandContext,
  type CommandResult
} from '../tablePartCommandManager'

describe('TablePartCommandManager', () => {
  let commandManager: TablePartCommandManager

  beforeEach(() => {
    commandManager = createCommandManager()
  })

  describe('Command Discovery', () => {
    class MockFormWithCommands {
      addRowCalled = false
      deleteRowCalled = false
      selectedRowsParam: number[] = []

      @tableCommand({ 
        id: 'add_row', 
        name: 'Add Row',
        availability: CommandAvailability.ALWAYS 
      })
      addTableRow(context: CommandContext): CommandResult {
        this.addRowCalled = true
        return {
          success: true,
          message: 'Row added',
          affectedRows: [],
          refreshRequired: false
        }
      }

      @tableCommand({ 
        id: 'delete_row', 
        name: 'Delete Rows',
        availability: CommandAvailability.REQUIRES_SELECTION 
      })
      deleteSelectedRows(context: CommandContext): CommandResult {
        this.deleteRowCalled = true
        this.selectedRowsParam = context.selectedRows
        return {
          success: true,
          message: `Deleted ${context.selectedRows.length} rows`,
          affectedRows: context.selectedRows,
          refreshRequired: true
        }
      }

      // Method without decorator (should be discovered by naming convention)
      moveUp(): boolean {
        return true
      }

      moveDown(): boolean {
        return true
      }
    }

    it('should discover commands from form instance (Requirements 2.1, 2.2)', () => {
      const form = new MockFormWithCommands()
      
      const discovered = commandManager.discoverAndRegisterCommands(form)
      
      // Should discover decorated commands
      const commandIds = discovered.map(cmd => cmd.id)
      expect(commandIds).toContain('add_row')
      expect(commandIds).toContain('delete_row')
      
      // Should also discover naming convention commands
      expect(commandIds).toContain('move_up')
      expect(commandIds).toContain('move_down')
    })

    it('should register commands with correct availability', () => {
      const form = new MockFormWithCommands()
      commandManager.discoverAndRegisterCommands(form)
      
      const commands = commandManager.getRegisteredCommands()
      
      // Check availability settings
      const addCommand = commands['add_row']
      expect(addCommand).toBeDefined()
      expect(addCommand.availability).toBe(CommandAvailability.ALWAYS)
      
      const deleteCommand = commands['delete_row']
      expect(deleteCommand).toBeDefined()
      expect(deleteCommand.availability).toBe(CommandAvailability.REQUIRES_SELECTION)
    })
  })

  describe('Command Execution', () => {
    class MockFormWithCommands {
      addRowCalled = false
      deleteRowCalled = false
      selectedRowsParam: number[] = []

      @tableCommand({ id: 'add_row', name: 'Add Row' })
      addTableRow(context: CommandContext): CommandResult {
        this.addRowCalled = true
        return {
          success: true,
          message: 'Row added',
          affectedRows: [],
          refreshRequired: false
        }
      }

      @tableCommand({ 
        id: 'delete_row', 
        name: 'Delete Rows',
        availability: CommandAvailability.REQUIRES_SELECTION 
      })
      deleteSelectedRows(context: CommandContext): CommandResult {
        this.deleteRowCalled = true
        this.selectedRowsParam = context.selectedRows
        return {
          success: true,
          message: `Deleted ${context.selectedRows.length} rows`,
          affectedRows: context.selectedRows,
          refreshRequired: true
        }
      }
    }

    it('should execute form command through manager (Requirements 2.3, 2.4)', async () => {
      const form = new MockFormWithCommands()
      commandManager.discoverAndRegisterCommands(form)
      
      const context = createCommandContext([], [])
      const result = await commandManager.executeCommand('add_row', context)
      
      expect(result.success).toBe(true)
      expect(form.addRowCalled).toBe(true)
    })

    it('should respect command availability requirements', async () => {
      const form = new MockFormWithCommands()
      commandManager.discoverAndRegisterCommands(form)
      
      // Try to execute delete without selection
      let context = createCommandContext([], [])
      let result = await commandManager.executeCommand('delete_row', context)
      
      expect(result.success).toBe(false)
      expect(form.deleteRowCalled).toBe(false)
      
      // Execute with selection
      context = createCommandContext([0, 1], [{}, {}])
      result = await commandManager.executeCommand('delete_row', context)
      
      expect(result.success).toBe(true)
      expect(form.deleteRowCalled).toBe(true)
      expect(form.selectedRowsParam).toEqual([0, 1])
    })

    it('should handle command execution errors gracefully', async () => {
      class FaultyForm {
        @tableCommand({ id: 'faulty_command' })
        faultyMethod(context: CommandContext): never {
          throw new Error('Something went wrong')
        }
      }

      const form = new FaultyForm()
      commandManager.discoverAndRegisterCommands(form)
      
      const context = createCommandContext()
      const result = await commandManager.executeCommand('faulty_command', context)
      
      expect(result.success).toBe(false)
      expect(result.message).toContain('Something went wrong')
    })

    it('should return error for unknown commands', async () => {
      const context = createCommandContext()
      const result = await commandManager.executeCommand('unknown_command', context)
      
      expect(result.success).toBe(false)
      expect(result.message).toContain('not found')
    })
  })

  describe('Command State Management', () => {
    class MockFormWithCommands {
      @tableCommand({ id: 'add_row', availability: CommandAvailability.ALWAYS })
      addRow(): boolean { return true }

      @tableCommand({ id: 'delete_row', availability: CommandAvailability.REQUIRES_SELECTION })
      deleteRow(): boolean { return true }

      @tableCommand({ id: 'export_data', availability: CommandAvailability.REQUIRES_ROWS })
      exportData(): boolean { return true }
    }

    it('should update command states based on context (Requirements 2.5)', () => {
      const form = new MockFormWithCommands()
      commandManager.discoverAndRegisterCommands(form)
      
      // Update states with no selection, no rows
      let context = createCommandContext([], [])
      let states = commandManager.updateCommandStates(context)
      
      expect(states['add_row']).toBe(true)
      expect(states['delete_row']).toBe(false)
      expect(states['export_data']).toBe(false)
      
      // Update states with selection and rows
      context = createCommandContext([0], [{}])
      states = commandManager.updateCommandStates(context)
      
      expect(states['add_row']).toBe(true)
      expect(states['delete_row']).toBe(true)
      expect(states['export_data']).toBe(true)
    })

    it('should cache command states properly', () => {
      const form = new MockFormWithCommands()
      commandManager.discoverAndRegisterCommands(form)
      
      // Update states
      const context = createCommandContext([0], [{}])
      commandManager.updateCommandStates(context)
      
      // Check cached states
      expect(commandManager.getCommandState('add_row')).toBe(true)
      expect(commandManager.getCommandState('delete_row')).toBe(true)
      expect(commandManager.getCommandState('export_data')).toBe(true)
    })

    it('should get available commands based on context', () => {
      const form = new MockFormWithCommands()
      commandManager.discoverAndRegisterCommands(form)
      
      // No selection, no rows
      let context = createCommandContext([], [])
      let available = commandManager.getAvailableCommands(context)
      
      const availableIds = available.map(cmd => cmd.id)
      expect(availableIds).toContain('add_row')
      expect(availableIds).not.toContain('delete_row')
      expect(availableIds).not.toContain('export_data')
      
      // With selection and rows
      context = createCommandContext([0], [{}])
      available = commandManager.getAvailableCommands(context)
      
      const availableIds2 = available.map(cmd => cmd.id)
      expect(availableIds2).toContain('add_row')
      expect(availableIds2).toContain('delete_row')
      expect(availableIds2).toContain('export_data')
    })
  })

  describe('Command Manager Utilities', () => {
    it('should clear all commands', () => {
      class MockForm {
        @tableCommand({ id: 'test_command' })
        testMethod(): boolean { return true }
      }

      const form = new MockForm()
      commandManager.discoverAndRegisterCommands(form)
      
      expect(Object.keys(commandManager.getRegisteredCommands())).toHaveLength(1)
      
      commandManager.clearCommands()
      
      expect(Object.keys(commandManager.getRegisteredCommands())).toHaveLength(0)
      expect(commandManager.getCommandState('test_command')).toBe(false)
    })

    it('should register and unregister individual commands', () => {
      const command: FormCommand = {
        id: 'test_command',
        name: 'Test Command',
        methodName: 'testMethod',
        formInstance: { testMethod: () => true },
        availability: CommandAvailability.ALWAYS,
        parameters: [],
        enabled: true
      }

      commandManager.registerCommand(command)
      expect(commandManager.getRegisteredCommands()['test_command']).toBeDefined()

      commandManager.unregisterCommand('test_command')
      expect(commandManager.getRegisteredCommands()['test_command']).toBeUndefined()
    })
  })

  describe('Decorator Functionality', () => {
    it('should properly configure commands with decorator', () => {
      class DecoratedForm {
        @tableCommand({
          id: 'custom_command',
          name: 'Custom Command',
          availability: CommandAvailability.REQUIRES_SELECTION,
          parameters: ['param1', 'param2'],
          enabled: true
        })
        customMethod(): boolean {
          return true
        }
      }

      const form = new DecoratedForm()
      const discovered = commandManager.discoverAndRegisterCommands(form)
      
      expect(discovered).toHaveLength(1)
      
      const command = discovered[0]
      expect(command.id).toBe('custom_command')
      expect(command.name).toBe('Custom Command')
      expect(command.availability).toBe(CommandAvailability.REQUIRES_SELECTION)
      expect(command.parameters).toEqual(['param1', 'param2'])
      expect(command.enabled).toBe(true)
    })

    it('should use default values when decorator options are not provided', () => {
      class SimpleForm {
        @tableCommand()
        simpleMethod(): boolean {
          return true
        }
      }

      const form = new SimpleForm()
      const discovered = commandManager.discoverAndRegisterCommands(form)
      
      expect(discovered).toHaveLength(1)
      
      const command = discovered[0]
      expect(command.id).toBe('simpleMethod')
      expect(command.name).toBe('Simple Method')
      expect(command.availability).toBe(CommandAvailability.ALWAYS)
      expect(command.parameters).toEqual([])
      expect(command.enabled).toBe(true)
    })
  })
})