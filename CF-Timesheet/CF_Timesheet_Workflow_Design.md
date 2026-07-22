# CF Turnaround — Timesheet & Time-Entry Workflow

**Purpose:** organize the brain-dump into workstreams, decisions, and a proposed
end-to-end design so we have something concrete to react to.
**Scope:** Safeway & B&D timesheets during the TA. Wolverine office handles
Wolverine info and hands it to us in whatever format/time we specify.
**Status:** draft for discussion — 2026-07-22.

---

## 1. Deliverables in this folder

| File | What it is |
|------|-----------|
| `CF_Timesheet_Template.xlsx` | Clean, CF-branded rebuild of the Wolverine timesheet (see §3). |
| `CF_Timesheet_Workflow_Design.md` | This document. |
| `assets/cf_logo_official.png` | Official CF logo (extracted from the .pbix). |
| `powerbi/PowerBI_Model_Notes.md` | Reverse-engineered model + manual rebuild steps. |
| `powerbi/PowerQuery_Ingestion.m` | Paste-ready M queries (timesheet, Lenel, references). |
| `powerbi/DAX_Checks.dax` | Paste-ready check measures & row-level flags. |

---

## 2. Proposed daily workflow

```
1. Pull IW37N report (SAP)            ── planner / script
2. Pull IW29 work-order list (SAP)    ── refreshes "Work Orders" tab
3. Get Lenel swipe export             ── daily (auto-generated if we re-enable it)
4. Hillary receives timecards
5. Refresh Power BI
6. Work through errors + swipe deviations
7. Allocate hours proportionally to op steps
8. Export to Excel → pivot table for approvals
9. Export from BI → upload to SAP (split by op step)
```

The Excel template covers steps 4–6 at the source (valid names/trades, hours-vs-Lenel
check) so fewer errors reach the BI stage.

---

## 3. Timesheet template — what changed vs. the current Wolverine sheet

Built as a **clean rebuild** (not a modify of the 145-column original) so the
dropdowns are standard list validations that survive round-trips, instead of the
current file's "x14" extension validations that break when the file is edited by
anything other than desktop Excel.

Email ask → how it's handled:

- **Look similar to current** — same header-band + labor-grid + work-description
  layout and yellow "populate these" convention.
- **CF logo** — embedded top-left (placeholder; drop in the official file).
- **Hide columns that don't serve** — dropped Wolverine-only columns (multi-job
  allocation blocks, Meal $$, Daily LOA, "Which Column?"). Helper column A is hidden.
- **Hide the equipment section** — removed entirely.
- **"Work Order" + expanded yellow** — renamed from "Job/Task Number"; a large
  free-text yellow WORK ORDER box sits in the header, plus a per-row Work Order
  column (dropdown from the IW29 list) and a wide Work Order Description column.
- **More employee rows** — 40 rows; trivially extendable.
- **Reference tab** — Employees (Name + CF ID + Work Center + default Trade) and
  Trades → **SAP activity type** mapping (e.g. `Pipefitter – Journeyman → CI203 →
  CRT CIM PF JM ST`). Straight-time vs double-time are separate activity types.
- **FAQ tab** — Work-order formatting, Adding employees, Adding roles/trades, the
  built-in checks, and the daily workflow.
- **Checks** (email: names, trades, hours vs Lenel):
  - Employee name not in Reference → cell turns red, CF ID shows `?`.
  - Trade not mapped → cell turns red, Activity Type shows `?`.
  - `Lenel Hours` column + auto `Deviation` (booked − swipe); non-zero turns red.
  - Total Hours > 16 or < 0 → red; RT + DT ≠ Total → amber.

**Seed data:** Employees + activity types from the CIMS example's `Data` tab;
Work Orders (71) from the IW29 export. All are examples — extend on the Reference /
Work Orders tabs.

### Open template questions
1. One sheet per day, or one workbook covering the TA? (drives how rows/dates scale)
2. Is Work Order per-employee-row (current assumption) or one per sheet?
3. Do we need the RT/DT split, or does SAP derive rate from the activity type?
4. Confirm the full trade → activity-type list beyond CIMS pipefitters (B&D, Safeway crafts).

---

## 4. Other workstreams (not built here — need input/access)

### Lenel export
- Access requested for Nitin + Mark; Hillary already has it.
- Need a **daily export** (reportedly was auto-generated before — worth re-enabling).
- Feeds the `Lenel Hours` column / BI swipe-deviation check. **Decision:** agree the
  export layout (badge ID, name, first-in/last-out, total hours, date).

### SAP — IW37N
- Daily export with an **agreed layout**; scripting it would remove manual steps.
- IW29 already gives us the work-order master (Order, Revision, description, location).
- **Decision:** lock the IW37N column layout so the same script/BI query works daily.

### Power BI (`CF_TA___Shop_Fab.pbix`)
- Set Hillary up with an app that does what we do for Wolverine, but cleaned up.
- Must check employee names, trades, and hours-asked vs Lenel swipe data.
- **Next step:** inspect the existing model (tables/relationships/measures) and list
  what to keep vs. rebuild — call it out if you want me to do that pass next.

### Approvals / signatures
- Undecided: DocuSign vs. hard copies (Mark leaning toward hard copy as familiar).
- Template already supports a pivot-for-approvals export regardless of the choice.

---

## 5. Decisions needed
- [ ] Sheet-per-day vs. single TA workbook.
- [ ] Work Order granularity (per row vs. per sheet).
- [ ] Full trade → activity-type mapping (all crafts, ST/DT).
- [ ] Lenel export layout + cadence (and re-enable auto-generation).
- [ ] IW37N export layout (+ whether to script it).
- [ ] DocuSign vs. hard copy for approvals.
- [ ] Format/time Wolverine office delivers their data to us.
