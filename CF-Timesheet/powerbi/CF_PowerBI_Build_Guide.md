# CF Timesheet → Power BI — build guide

Goal: drop vendor timesheets into a folder, hit **Refresh**, and print/export the
approval timesheet (the `CF_Timesheet_20260808.pdf` layout).

> **Why a guide, not a .pbix:** a Power BI file is a Windows/Power-BI-Desktop
> binary; a hand-built one from outside the app almost always fails to open. This
> kit (the two `.m`/`.dax` files + these steps) builds it reliably in ~20–30 min.

---

## The data flow

```
 Timesheets folder ─┐
                    ├─► Query "Timesheets"  (Employee × Work Order, clean)  ─► PRINT report
 IW37N (SAP) file ──┘         │  join WO Name / work centre
                              └─► Query "TimesheetsSplit" (one row per op step) ─► SAP upload
```

This mirrors your Illustration report: **FSTC → FSTC_Split → Data → CF Report**.
Query 2 = the CF-Report grain (one line per employee per WO, op steps listed) —
that's what prints. Query 3 = the FSTC_Split grain (per op step) for SAP.

---

## Step 1 — Load the queries
1. Power BI Desktop → **Home ▸ Transform data** (Power Query).
2. **New Source ▸ Blank Query ▸ Advanced Editor**; paste **Query 1 (SAP)** from
   `PowerQuery_TimesheetClean.m`; set the SAP file path; rename the query **SAP**.
3. New Blank Query; paste **Query 2 (Timesheets)**; set `TimesheetFolder`; rename
   **Timesheets**. (It references `SAP`, so create SAP first.)
4. *(optional, for SAP upload)* New Blank Query; paste **Query 3**; rename
   **TimesheetsSplit**.
5. **Close & Apply.**

Fix the two paths at the top of each query. Drop new timesheets in the folder and
**Refresh** to reload.

## Step 2 — Model + measures
1. **Model view:** relationship `Timesheets[WO ID]` → `SAP[Order]` is optional
   (the WO Name is already merged in Query 2).
2. Paste each measure from `DAX_Measures_Report.dax` (New measure).

## Step 3 — The printable report (matches the PDF)
1. New report page, **Landscape**.
2. Add a **Table** visual (or **Matrix** for date subtotals). Columns in order:
   **Date, Shift, Job Description, Employee, Trade, WO ID, WO Name, OP Steps**,
   then measures **[DT Hours], [RT Hours], [Total Hours]**.
   - For a **Matrix**: put **Date** (and Shift) in Rows, the rest in Rows below
     it, measures in Values → you get the **daily subtotals** like the PDF.
3. Add a **Text/Card** at the top: `CF Industries` + the **[Report Title]** measure.
4. Add **slicers** for **Vendor** and **Date** so you can print one vendor/day.
5. Format: turn on **Totals** (matrix), set the header fill to CF green (#015846),
   white bold text; enable **word-wrap** on OP Steps.

## Step 4 — Print / export
- **File ▸ Export to PDF** prints the current page (apply the Vendor/Date slicer
  first to get one vendor's day per PDF).
- For many vendors/days automatically: publish to the Power BI Service and use a
  **paginated report (Report Builder)** with the same fields + a Date/Vendor
  parameter, then **Subscribe** or **Export to PDF** per group. (Paginated is the
  proper tool for pixel-perfect, multi-page printing.)

## Step 5 — SAP upload export (optional)
- Use the **TimesheetsSplit** query (one row per op step, hours split evenly per
  step). Change the split rule in Query 3 if you allocate proportionally.
- Export that table to Excel/CSV in your SAP upload layout.

---

## Notes / things to confirm
- **Hours grain:** the print report shows **WO-level totals** with op steps listed
  (as your CF Report does). The per-op-step split is only for SAP.
- **One WO per block** is assumed (matches the timesheet). If a block ever holds
  multiple `WO..OP..` segments, the WO parsing needs a small tweak — tell me.
- **"Timecard Remark"** comes from the block's row-67 "Job Specific: …" cell.
- If WO Name is blank in the report, that WO ID isn't in the SAP export — refresh
  IW37N or check the number.

Give me a real IW37N export and 2–3 filled timesheets and I'll tighten the M to
your exact column names and (if useful) mock the report layout for sign-off.
