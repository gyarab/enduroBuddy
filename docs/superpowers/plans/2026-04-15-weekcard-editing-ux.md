# WeekCard Inline Editing UX — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two WeekCard UX issues — row height stability on edit, and table expanding to show full training text instead of truncating it.

**Architecture:** Pure CSS + template change in a single component (`WeekCard.vue`). No logic, no API, no store changes. Both changes are independent and can be committed separately.

**Tech Stack:** Vue 3 SFC, CSS Grid, `<style scoped>`

---

## File Map

| File | Change |
|------|--------|
| `frontend/src/components/training/WeekCard.vue` | Template: `rows="2"` → `rows="1"` on title textarea. CSS: 7 rule changes + 1 new rule (`.wt__table`). Add `.wt__table` wrapper element. |

---

### Task 1: Fix row height during editing

Eliminates the vertical jump when a user clicks into a row. The title textarea becomes single-line height; the editing row keeps `align-items: center` and no extra padding.

**Files:**
- Modify: `frontend/src/components/training/WeekCard.vue`

- [ ] **Step 1: Change textarea from rows=2 to rows=1**

  In the template, find the title textarea (around line 368). Change `rows="2"` to `rows="1"`:

  ```html
  <textarea
    v-model="getEdit(slot.date)!.title"
    v-autofocus="getEdit(slot.date)!.focusField === 'title'"
    class="wt__textarea"
    :disabled="getEdit(slot.date)!.isSaving"
    :placeholder="t('weekCard.titlePlaceholder')"
    rows="1"
    @click.stop
    @input="onFieldInput(slot.date, slot)"
  />
  ```

- [ ] **Step 2: Fix `.wt__row--editing` CSS**

  Remove `align-items: start`, `padding-top`, `padding-bottom` so the editing row matches the idle row layout:

  ```css
  .wt__row--editing {
    background: rgba(200,255,0,.04);
    cursor: default;
  }
  ```

  (Replace the entire existing `.wt__row--editing` rule — current rule has `align-items: start; padding-top: 0.5rem; padding-bottom: 0.25rem;` which we're removing.)

- [ ] **Step 3: Fix `.wt__textarea` CSS**

  Add fixed height + horizontal scroll so the textarea stays one line tall:

  ```css
  .wt__textarea {
    resize: none;
    font-family: var(--eb-font-mono);
    line-height: 1.45;
    height: 1.75rem;
    overflow-x: auto;
    white-space: nowrap;
  }
  ```

- [ ] **Step 4: Run tests to verify no regressions**

  ```bash
  cd frontend && npm test -- --run
  ```

  Expected: all tests pass (green). The change is template/CSS only — no logic touched.

- [ ] **Step 5: Commit**

  ```bash
  git add frontend/src/components/training/WeekCard.vue
  git commit -m "fix: keep WeekCard row height stable during inline editing"
  ```

---

### Task 2: Table expands to fit longest row content

Removes text truncation (`ellipsis`) from title/notes/intervals cells. The table grid uses `max-content` for text columns so it naturally grows to the widest row. The card scrolls horizontally when the content exceeds viewport width.

**Files:**
- Modify: `frontend/src/components/training/WeekCard.vue`

- [ ] **Step 1: Wrap table content in `.wt__table`**

  In the template, wrap the column-header row, all day rows, and the summary row in a single `<div class="wt__table">`. The week-card header stays outside the wrapper.

  Before:
  ```html
  <EbCard class="week-card">
    <div class="week-card__header">
      ...
    </div>

    <!-- ── Column headers ── -->
    <div class="wt__cols wt__head-row">
      ...
    </div>

    <!-- ── Day rows ── -->
    <template v-for="slot in daySlots" :key="slot.date">
      ...
    </template>

    <!-- ── Summary row ── -->
    <div class="wt__cols wt__summary-row">
      ...
    </div>
  </EbCard>
  ```

  After:
  ```html
  <EbCard class="week-card">
    <div class="week-card__header">
      ...
    </div>

    <div class="wt__table">
      <!-- ── Column headers ── -->
      <div class="wt__cols wt__head-row">
        ...
      </div>

      <!-- ── Day rows ── -->
      <template v-for="slot in daySlots" :key="slot.date">
        ...
      </template>

      <!-- ── Summary row ── -->
      <div class="wt__cols wt__summary-row">
        ...
      </div>
    </div>
  </EbCard>
  ```

- [ ] **Step 2: Update `.week-card` CSS — enable horizontal scroll**

  ```css
  .week-card {
    overflow-x: auto;
    padding: 0;
  }
  ```

  (Replace `overflow: hidden` with `overflow-x: auto`.)

- [ ] **Step 3: Add `.wt__table` CSS rule**

  Add after the `.week-card` rule:

  ```css
  .wt__table {
    min-width: 100%;
    width: max-content;
  }
  ```

- [ ] **Step 4: Update `.wt__cols` grid template — text columns to `max-content`**

  Replace the entire `.wt__cols` rule:

  ```css
  .wt__cols {
    display: grid;
    grid-template-columns: 52px 40px 44px max-content max-content 2px 64px 56px max-content 52px 52px;
    align-items: start;
    min-height: 2.5rem;
  }
  ```

  (Columns 4, 5, 9 changed from `minmax(0, 2fr)`, `minmax(0, 1fr)`, `minmax(0, 1fr)` to `max-content`.)

- [ ] **Step 5: Remove truncation from text cell classes**

  Replace `.wt__title-text`:
  ```css
  .wt__title-text {
    display: block;
    white-space: nowrap;
    color: var(--eb-text);
    font-size: 0.875rem;
  }
  ```

  Replace `.wt__notes-text`:
  ```css
  .wt__notes-text {
    display: block;
    white-space: nowrap;
    color: var(--eb-text-muted);
    font-size: 0.75rem;
  }
  ```

  Replace `.wt__intervals-text`:
  ```css
  .wt__intervals-text {
    display: block;
    white-space: nowrap;
    color: var(--eb-text-soft);
    font-size: 0.75rem;
    font-family: var(--eb-font-mono);
  }
  ```

  (Removed `overflow: hidden; text-overflow: ellipsis` from all three.)

- [ ] **Step 6: Update responsive breakpoints**

  Replace the 1023px breakpoint rule:
  ```css
  @media (max-width: 1023px) {
    .wt__cols {
      grid-template-columns: 48px 36px 40px max-content 80px 2px 54px 48px 0 44px 44px;
    }
    .wt__cell--intervals { display: none; }
  }
  ```

  Replace the 767px breakpoint rule:
  ```css
  @media (max-width: 767px) {
    .wt__cols {
      grid-template-columns: 44px 32px 38px max-content 2px 52px 46px 42px 42px;
    }
    .wt__h--type,
    .wt__cell--type,
    .wt__cell--notes,
    .wt__h:nth-child(5) { display: none; }
  }
  ```

- [ ] **Step 7: Run tests to verify no regressions**

  ```bash
  cd frontend && npm test -- --run
  ```

  Expected: all tests pass.

- [ ] **Step 8: Commit**

  ```bash
  git add frontend/src/components/training/WeekCard.vue
  git commit -m "fix: expand WeekCard table to fit long training text instead of truncating"
  ```

---

## Self-Review

**Spec coverage:**
- ✅ Row height fixed: Task 1 (textarea rows, CSS `.wt__row--editing`, `.wt__textarea`)
- ✅ Table expands: Task 2 (`.wt__table` wrapper, `.week-card` scroll, `max-content` columns, truncation removed)
- ✅ Responsive breakpoints updated: Task 2 Step 6
- ✅ `PlannedRow.vue` explicitly out of scope — not touched

**Placeholders:** None.

**Type consistency:** No types involved — CSS/template only.
