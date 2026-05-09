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
