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

## 3. Timesheet template (v2) — structure

Built as a **clean rebuild** so dropdowns are standard list validations that
survive round-trips (the original's "x14" validations break outside desktop Excel).
Modelled on the real pipeline: **FSTC → FSTC_Split → Data → CF Report**.

**Header (one sheet = one Vendor / Date / Shift):**
- **Vendor (Name - ID)** dropdown at the top — the same sheet serves multiple vendors.
- Single **Date** and **Shift** for the whole sheet (never multiple dates/shifts per sheet).
- Client (CF Industries), Posting Date, Prepared/Approved By, Sheet #, auto Total Hours.
- Official CF logo + brand colours.

**Grid — one row per employee × work order:**
`Employee | Trade (SAP code-name) | PO/Job | WO ID | WO Name (auto) | OP Steps
(comma list) | DT | RT | Total (auto) | Location | Notes`, then a collapsed
**Reconciliation** band (Lenel Hrs, Deviation, Swipe Reason, Hold Up).
- A person charging several WOs gets **one row per WO**; the OP Steps cell lists that
  WO's steps (e.g. `0392, 0395, 0396`). Hours are split to op-steps downstream.
- Hidden **WOOP Export Key** builds `WO<id>OP<step>,OP<step>…` — the exact string the
  FSTC split process reads.

**Data validation & protection (mirrors the Wolverine sheet):**
- List dropdowns via named ranges (Vendor, Employee, Trade, PO, WO ID, Location, Shift).
- Hours validated **decimal ≥ 0**; header dates validated.
- Sheet is **protected with no password** — every cell locked **except the yellow
  entry cells**, so derived/formula cells can't be broken (Review ▸ Unprotect to edit layout).
- **Checks** (conditional formatting): unknown employee/trade/WO → red; hours with no
  PO or no OP steps → amber; non-zero swipe deviation → red.

**Reference / Work Orders tabs** seed real values pulled from the sample files:
21 employees, 14 trades (SAP code-name), 37 POs, 44 work orders + an 85-row OP-step master.

### Open template questions
1. One sheet per day/shift, or a multi-tab workbook per TA week?
2. Confirm the vendor list (Name + ID) — currently placeholder (Wolverine/B&D/Safeway).
3. Should WO ID / OP Steps be **cascading** (OP list filtered by WO, DFR-style)?  Doable next.
4. Employee identifier — name only, or add a per-vendor CF/badge ID for the swipe match?

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
