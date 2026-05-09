import { describe, it, expect } from 'vitest'
import { useGridNav, GRID_FIELDS } from '~/composables/useGridNav'

describe('useGridNav — GRID_FIELDS', () => {
  it('exports 8 fields starting with type', () => {
    expect(GRID_FIELDS[0]).toBe('type')
    expect(GRID_FIELDS).toHaveLength(8)
  })
})

describe('useGridNav — moveCursor', () => {
  it('right increments fieldIdx', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 0 }
    moveCursor('right', 2)
    expect(cursor.value?.fieldIdx).toBe(1)
  })

  it('left at fieldIdx 0 stays', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 0 }
    moveCursor('left', 2)
    expect(cursor.value?.fieldIdx).toBe(0)
  })

  it('right at fieldIdx 7 stays', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 7 }
    moveCursor('right', 2)
    expect(cursor.value?.fieldIdx).toBe(7)
  })

  it('down increments dayIdx', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 3, fieldIdx: 1 }
    moveCursor('down', 2)
    expect(cursor.value?.dayIdx).toBe(4)
  })

  it('down from Sunday (dayIdx 6) goes to next week Monday', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 6, fieldIdx: 2 }
    moveCursor('down', 2)
    expect(cursor.value).toEqual({ weekIdx: 1, dayIdx: 0, fieldIdx: 2 })
  })

  it('down from last week Sunday stays', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 1, dayIdx: 6, fieldIdx: 1 }
    moveCursor('down', 2)
    expect(cursor.value).toEqual({ weekIdx: 1, dayIdx: 6, fieldIdx: 1 })
  })

  it('up from Monday (dayIdx 0) goes to prev week Sunday', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 1, dayIdx: 0, fieldIdx: 3 }
    moveCursor('up', 2)
    expect(cursor.value).toEqual({ weekIdx: 0, dayIdx: 6, fieldIdx: 3 })
  })

  it('up from first week Monday stays', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    moveCursor('up', 2)
    expect(cursor.value).toEqual({ weekIdx: 0, dayIdx: 0, fieldIdx: 1 })
  })

  it('does nothing when cursor is null', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = null
    moveCursor('right', 2)
    expect(cursor.value).toBeNull()
  })
})

describe('useGridNav — enterEdit / exitEdit', () => {
  it('enterEdit sets editMode true and stores replace content', () => {
    const { cursor, editMode, enterEdit, pendingReplace } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    enterEdit('x')
    expect(editMode.value).toBe(true)
    expect(pendingReplace.value).toBe('x')
  })

  it('enterEdit without arg stores undefined replace', () => {
    const { cursor, editMode, enterEdit, pendingReplace } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    enterEdit()
    expect(editMode.value).toBe(true)
    expect(pendingReplace.value).toBeUndefined()
  })

  it('exitEdit clears editMode and pendingReplace', () => {
    const { cursor, editMode, pendingReplace, enterEdit, exitEdit } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    enterEdit('a')
    exitEdit()
    expect(editMode.value).toBe(false)
    expect(pendingReplace.value).toBeUndefined()
  })
})

describe('useGridNav — initCursor', () => {
  it('sets cursor to week containing today', () => {
    const { cursor, initCursor } = useGridNav()
    const today = new Date().toISOString().slice(0, 10)
    const weeks = [
      { week_start: '2020-01-01', week_end: '2020-01-07' },
      { week_start: today, week_end: today },
    ]
    initCursor(weeks)
    expect(cursor.value?.weekIdx).toBe(1)
    expect(cursor.value?.dayIdx).toBe(0)
    expect(cursor.value?.fieldIdx).toBe(0)
  })

  it('falls back to week 0 when today not found', () => {
    const { cursor, initCursor } = useGridNav()
    const weeks = [
      { week_start: '2020-01-01', week_end: '2020-01-07' },
    ]
    initCursor(weeks)
    expect(cursor.value?.weekIdx).toBe(0)
  })

  it('does nothing for empty weeks array', () => {
    const { cursor, initCursor } = useGridNav()
    initCursor([])
    expect(cursor.value).toBeNull()
  })
})
