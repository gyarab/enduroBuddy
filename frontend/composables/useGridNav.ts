import { ref, type Ref } from 'vue'

export const GRID_FIELDS = [
  'type', 'title', 'notes', 'km', 'minutes', 'details', 'avgHr', 'maxHr',
] as const

export type GridField = (typeof GRID_FIELDS)[number]

export interface GridCursor {
  weekIdx: number
  dayIdx: number   // 0 = pondělí, 6 = neděle
  fieldIdx: number // 0–7
}

export function useGridNav() {
  const cursor: Ref<GridCursor | null> = ref(null)
  const editMode = ref(false)
  const pendingReplace: Ref<string | undefined> = ref(undefined)

  function moveCursor(
    dir: 'up' | 'down' | 'left' | 'right',
    weekCount: number,
  ): void {
    if (!cursor.value) {
      cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
      return
    }
    const c = cursor.value

    if (dir === 'left') {
      cursor.value = { ...c, fieldIdx: Math.max(0, c.fieldIdx - 1) }
      return
    }
    if (dir === 'right') {
      cursor.value = { ...c, fieldIdx: Math.min(7, c.fieldIdx + 1) }
      return
    }
    if (dir === 'up') {
      if (c.dayIdx > 0) {
        cursor.value = { ...c, dayIdx: c.dayIdx - 1 }
      } else if (c.weekIdx > 0) {
        cursor.value = { ...c, weekIdx: c.weekIdx - 1, dayIdx: 6 }
      }
      return
    }
    if (dir === 'down') {
      if (c.dayIdx < 6) {
        cursor.value = { ...c, dayIdx: c.dayIdx + 1 }
      } else if (c.weekIdx < weekCount - 1) {
        cursor.value = { ...c, weekIdx: c.weekIdx + 1, dayIdx: 0 }
      }
    }
  }

  function enterEdit(replaceContent?: string): void {
    editMode.value = true
    pendingReplace.value = replaceContent
  }

  function exitEdit(): void {
    editMode.value = false
    pendingReplace.value = undefined
  }

  function initCursor(weeks: Array<{ week_start: string; week_end: string }>): void {
    if (!weeks.length) return
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
  }

  return { cursor, editMode, pendingReplace, moveCursor, enterEdit, exitEdit, initCursor }
}
