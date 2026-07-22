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

## 3. Timesheet template (v4) — side-by-side PO tables

Clean rebuild (standard list validations that survive round-trips). Modelled on the
real pipeline **FSTC → FSTC_Split → Data → CF Report** and on the Wolverine layout.

**Header (one sheet = one Vendor / Date / Shift):** Vendor (Name - ID), Date, Shift,
Client, CF logo. Header + Summary are **frozen** on top.

**Summary:** self-updating **hours by PO** (RT / DT / Total / entries) + Grand Total —
always visible, so you glance at it and submit.

**PO tables run LEFT-TO-RIGHT** (each holds ~30 lines, so a busy PO doesn't push the
others down). Each table is a **collapsible column-group** (hide the table, the Summary
still shows its totals):
- **Pick the PO once** on the table header (`PO ▸`); the header carries the table's
  RT / DT / Total subtotal.
- Row fields: `Employee | Trade | WO ID | OP1..OP5 | RT | DT | Total (auto) |
  Work Location | Offsite Hrs | Offsite Category | OT Meal? | LOA? | Notes`.
- **Multiple OP steps per row** via OP1–OP5, each a **cascading** dropdown showing only
  the op-steps valid for that row's WO (`INDIRECT("WO_"&<WO cell>)`).
- **Offsite Category** dropdown (from Reference); **OT Meal? / LOA?** Y-N eligibility flags.
- **WO Name is reference only** — faint, to the right, outside the table.
- Hidden **WOOP key** joins the chosen op steps: `WO<id>OP<s1>,OP<s2>…` for the pipeline.
- Currently 4 PO tables × 30 rows × 5 OP columns (all adjustable).

**Validation & protection (mirrors the Wolverine sheet):** named-range dropdowns
(Vendor, Employee, Trade, PO, WO ID, Location, Offsite Category, Y/N) + cascading OP;
hours **decimal ≥ 0**; entry cells unlocked / rest locked (protection ready, left off so
the collapse groups work). Checks: unknown employee / trade / WO → red.

**Reference / Work Orders / _OP tabs** seed real values: 21 employees, 14 trades, 37 POs,
44 work orders, per-WO op-step lists (85 steps), plus Offsite-Category and Y/N lists.

### Open template questions
1. How many PO tables side-by-side / rows each / OP columns? (now 4 × 30 × 5)
2. Confirm the vendor list (Name + ID) — currently placeholder (Wolverine/B&D/Safeway).
3. OT Meal? / LOA? — per row (current) or per employee? Should they auto-flag from rules?
4. Employee identifier — name only, or a per-vendor badge/CF ID for the swipe match?

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
