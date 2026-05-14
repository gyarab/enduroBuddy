import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

import type { DashboardWeek } from "~/utils/api/training";
import WeekCard from "./WeekCard.vue";
import { useAuthStore } from "~/stores/auth";
import { useTrainingStore } from "~/stores/training";

const DATE = "2026-05-01";

function buildWeek(overrides: Partial<DashboardWeek> = {}): DashboardWeek {
  return {
    id: 1,
    week_index: 1,
    week_start: DATE,
    week_end: "2026-05-07",
    has_started: true,
    planned_total_km_text: "38 km",
    completed_total: { km: "0", time: "0", avg_hr: null, max_hr: null },
    planned_rows: [
      {
        id: 10,
        kind: "planned",
        status: "planned",
        date: DATE,
        day_label: "Po",
        title: "Tempo run",
        notes: "Keep pace",
        session_type: "RUN",
        planned_metrics: null,
        completed_metrics: null,
        editable: true,
        is_second_phase: false,
        can_add_second_phase: false,
        can_remove_second_phase: false,
        has_linked_activity: false,
      },
    ],
    completed_rows: [],
    ...overrides,
  };
}

function mountWeekCard(week: DashboardWeek = buildWeek()) {
  // Set up stores BEFORE mounting
  const authStore = useAuthStore();
  authStore.user = {
    capabilities: { has_garmin_connection: false, garmin_sync_enabled: false },
  } as any;

  const trainingStore = useTrainingStore();
  trainingStore.dashboard = {
    flags: { can_edit_completed: true, can_edit_planned: true, is_coach: false },
  } as any;

  return mount(WeekCard, {
    props: { week, editorContext: "athlete" },
  });
}

function buildWeekWithCompleted(): DashboardWeek {
  return buildWeek({
    completed_rows: [
      {
        id: 10,
        kind: "completed",
        status: "done",
        date: DATE,
        day_label: "Po",
        title: "",
        notes: "",
        session_type: "RUN",
        planned_metrics: null,
        completed_metrics: {
          km: "8.00",
          minutes: "45",
          details: "",
          avg_hr: 145,
          max_hr: 170,
        },
        editable: true,
        has_linked_activity: false,
      },
    ],
  });
}

describe("WeekCard — zone editing mutual exclusion", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("clicking planned cell shows title input, hides km input", async () => {
    const wrapper = mountWeekCard();
    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true);
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(false);
  });

  it("clicking completed cell shows km input, hides title input", async () => {
    const wrapper = mountWeekCard();
    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(true);
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(false);
  });

  it("switching from planned to completed zone hides planned inputs", async () => {
    const wrapper = mountWeekCard();

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true);

    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(false);
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(true);
  });

  it("switching from completed to planned zone hides completed inputs", async () => {
    const wrapper = mountWeekCard();

    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(true);

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(false);
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true);
  });
});

describe("WeekCard — summary row", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("shows planned_total_km_text in summary row", () => {
    const wrapper = mountWeekCard();
    expect(wrapper.text()).toContain("38 km");
  });
});

describe("WeekCard — inline save", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("saves planned title edits through the training store", async () => {
    const wrapper = mountWeekCard();
    const trainingStore = useTrainingStore();
    trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined);

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("12 km steady");
    await wrapper.find(".wt__row").trigger("focusout", { relatedTarget: document.body });

    expect(trainingStore.savePlannedDraft).toHaveBeenCalledWith(10, [
      { field: "title", value: "12 km steady" },
    ]);
  });

  it("saves completed km edits through the training store", async () => {
    const wrapper = mountWeekCard(buildWeekWithCompleted());
    const trainingStore = useTrainingStore();
    trainingStore.saveCompletedDraft = vi.fn().mockResolvedValue(undefined);

    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    await wrapper.find(`[data-testid="input-km-${DATE}"]`).setValue("9.25");
    await wrapper.find(".wt__row").trigger("focusout", { relatedTarget: document.body });

    expect(trainingStore.saveCompletedDraft).toHaveBeenCalledWith(10, [
      { field: "km", value: "9.25" },
    ]);
  });
});

describe("WeekCard — auto-save keeps edit open", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("edit input is still visible after 1-second debounce save", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await vi.advanceTimersByTimeAsync(1100)
    await nextTick()

    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true)
  })

  it("focusout still closes the edit", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await wrapper.find(".wt__row").trigger("focusout", { relatedTarget: document.body })
    await nextTick()

    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(false)
  })

  it("failed auto-save adds wt__row--flash-err class", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockRejectedValue(new Error("Network error"))

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await vi.advanceTimersByTimeAsync(1100)
    await nextTick()

    expect(wrapper.find(".wt__row").classes()).toContain("wt__row--flash-err")
  })
})

describe("WeekCard — keyboard navigation", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it("Tab in title emits exit-edit (navigation delegated to grid)", async () => {
    const wrapper = mountWeekCard()
    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find('[data-field="title"]').trigger("keydown", { key: "Tab", shiftKey: false })
    await nextTick()

    expect(wrapper.emitted("exit-edit")).toBeTruthy()
  })

  it("Enter in notes emits exit-edit-move with 'down'", async () => {
    const wrapper = mountWeekCard()
    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await nextTick()
    await wrapper.find('[data-field="notes"]').trigger("keydown", { key: "Enter", shiftKey: false })
    await nextTick()

    expect(wrapper.emitted("exit-edit-move")).toBeTruthy()
    expect(wrapper.emitted("exit-edit-move")![0]).toEqual(["down"])
  })

  it("Shift+Enter in notes emits exit-edit-move with 'up'", async () => {
    const wrapper = mountWeekCard()
    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await nextTick()
    await wrapper.find('[data-field="notes"]').trigger("keydown", { key: "Enter", shiftKey: true })
    await nextTick()

    expect(wrapper.emitted("exit-edit-move")).toBeTruthy()
    expect(wrapper.emitted("exit-edit-move")![0]).toEqual(["up"])
  })

  it("Ctrl+Enter in notes does not emit exit-edit-move (allows newline)", async () => {
    const wrapper = mountWeekCard()
    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await nextTick()
    await wrapper.find('[data-field="notes"]').trigger("keydown", { key: "Enter", ctrlKey: true })
    await nextTick()

    expect(wrapper.emitted("exit-edit-move")).toBeFalsy()
  })

  it("Tab emits exit-edit (grid handles cross-week and cross-field navigation)", async () => {
    const singleDayWeek = buildWeek({ week_start: DATE, week_end: DATE })
    const wrapper = mountWeekCard(singleDayWeek)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find('[data-field="title"]').trigger("keydown", { key: "Tab", shiftKey: false })
    await nextTick()

    expect(wrapper.emitted("exit-edit")).toBeTruthy()
  })

  it("Shift+Tab emits exit-edit", async () => {
    const singleDayWeek = buildWeek({ week_start: DATE, week_end: DATE })
    const wrapper = mountWeekCard(singleDayWeek)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find('[data-field="title"]').trigger("keydown", { key: "Tab", shiftKey: true })
    await nextTick()

    expect(wrapper.emitted("exit-edit")).toBeTruthy()
  })
})

describe("WeekCard — activeCursor nav highlight", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it("applies nav-selected class to type cell when activeCursor.fieldIdx=0", async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    await wrapper.setProps({ activeCursor: { dayIdx: 0, fieldIdx: 0 } })
    await nextTick()
    const typeCell = wrapper.find('[data-testid="nav-cell-type-' + DATE + '"]')
    expect(typeCell.exists()).toBe(true)
    expect(typeCell.classes()).toContain('wt__cell--nav-selected-p')
  })

  it("applies nav-selected class to title cell when activeCursor.fieldIdx=1", async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    await wrapper.setProps({ activeCursor: { dayIdx: 0, fieldIdx: 1 } })
    await nextTick()
    const titleCell = wrapper.find('[data-testid="cell-title-' + DATE + '"]')
    expect(titleCell.classes()).toContain('wt__cell--nav-selected-p')
  })

  it("no nav-selected class when activeCursor is null", async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    await wrapper.setProps({ activeCursor: null })
    await nextTick()
    const selectedP = wrapper.findAll('.wt__cell--nav-selected-p')
    const selectedC = wrapper.findAll('.wt__cell--nav-selected-c')
    expect(selectedP.length + selectedC.length).toBe(0)
  })
})


describe('WeekCard — focusCellByIdx', () => {
  it('opens edit for title (fieldIdx=1) on dayIdx=0', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    ;(wrapper.vm as any).focusCellByIdx(0, 1)
    await nextTick()
    const input = wrapper.find('[data-testid="input-title-' + DATE + '"]')
    expect(input.exists()).toBe(true)
  })

  it('replaces content when replaceContent is provided', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    ;(wrapper.vm as any).focusCellByIdx(0, 1, 'x')
    await nextTick()
    const input = wrapper.find<HTMLTextAreaElement>('[data-testid="input-title-' + DATE + '"]')
    expect((input.element as HTMLTextAreaElement).value).toBe('x')
  })
})

describe('WeekCard — exit-edit event on ESC', () => {
  it('emits exit-edit when ESC is pressed in title input', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    ;(wrapper.vm as any).focusCellByIdx(0, 1)
    await nextTick()
    const input = wrapper.find('[data-testid="input-title-' + DATE + '"]')
    await input.trigger('keydown', { key: 'Escape' })
    expect(wrapper.emitted('exit-edit')).toBeTruthy()
  })
})

describe('WeekCard — cursor-set emit', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('emits cursor-set with dayIdx and fieldIdx when a planned cell is clicked', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    const titleCell = wrapper.find('[data-testid="cell-title-' + DATE + '"]')
    await titleCell.trigger('click')
    const emitted = wrapper.emitted('cursor-set')
    expect(emitted).toBeTruthy()
    expect(emitted![0][0]).toEqual({ dayIdx: 0, fieldIdx: 1 })
  })

  it('renders notes as textarea when planned zone is open', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    const titleCell = wrapper.find('[data-testid="cell-title-' + DATE + '"]')
    await titleCell.trigger('click')
    await nextTick()
    const notesTextarea = wrapper.find('[data-field="notes"][data-date="' + DATE + '"]')
    expect(notesTextarea.element.tagName).toBe('TEXTAREA')
  })
})
