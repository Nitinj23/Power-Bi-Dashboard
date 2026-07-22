# Power BI — `CF_TA___Shop_Fab.pbix` model notes & rebuild plan

Reverse-engineered from the report definition (the model itself is a compressed
binary and can't be edited outside Power BI Desktop). This documents what the file
does today and gives you paste-ready pieces to add the checks the email calls for.

---

## 1. Current model (as-is)

**Two report pages**
- `CF 2026 TA` — the main dashboard (7 `tableEx`, 4 slicers, gauge, combo/column
  charts, 100%-stacked bars, cards, images).
- `SAP Planning` — pivot tables + slicers over the IW37N / project data.

**Tables (query names kept as `Input - …` / `Reference - …`):**

| Table | Key columns seen in the report | Role |
|-------|--------------------------------|------|
| `Input - Shore` | EmployeeName, `Trade - Abbreviated`, HoursRT, HoursDT, Date, Purchase Order, Approved, Grouping, CostCategory, TotalCost, `colTrade&PO` | **Labor / timecard feed** (Wolverine "Shore") |
| `Input - IW37N Latest` | Order, Description, Activity, `Op. Short Text`, `Oper.WorkCenter`, `Std Text Key`, Revision, Work | SAP work-order operations |
| `Input - Projects` | colCFJobs, Status, colCFEstFilter, `colJobNumber&Desc`, colCFJobsArea, col# | Project/job list |
| `Input - Shop Data` | colFabStatus | Shop-fab status |
| `Reference - CF Location` | Name, Location | Location lookup (used heavily — 100+ refs) |
| `Reference - CF Op Work Centre` | `Work Ctr`, `Short description` | Work-centre lookup |
| `Reference - CF TA Shop Fab POs` | PO#, Budget, colIncurred | PO budget vs incurred |
| `Reference - Dates` | `Week End` | Date table |
| `Reference - Trade Data` | `Suncor Service Master`, DirVsInd | Trade master (direct vs indirect) |
| `tblMeasuresCFTA / Cost / Estimate / Reporting` | — | Measure-holder tables |

**Measures in use (15):** cost (`msrCostCommitted/Incurred/CommRem`), estimate
(`msrEstimateHours/Cost`, `msrIncurredHours/Cost`, `msrRemainingEstimate$/Hrs`,
`msr%ofEstimate(Hrs)`, `msrShopFab%`), reporting (`msrDataDate`,
`msrReportingFTE@40`), and `msrCFCountJobs`.

**Observations for the clean-up (email: "clean up a lot of the existing file"):**
- The labor feed is `Input - Shore` (Wolverine-shaped: RT/DT, PO, Trade-Abbreviated).
  For CF we point this at the new CF timesheet template instead.
- There are **no validation measures today** — nothing checks employee names, trades,
  or hours vs Lenel. That's the gap the new DAX below fills.
- `Reference - Trade Data` uses a "Suncor Service Master"; for CF this becomes the
  trade → **SAP activity type** mapping (CI201/CI203…) on the timesheet Reference tab.

---

## 2. What to add (delivered in this folder)

- `PowerQuery_Ingestion.m` — new/replacement queries: **Input - CF Timesheet**,
  **Input - Lenel**, **Reference - CF Employees**, **Reference - CF Activity Types**.
- `DAX_Checks.dax` — validation measures + row-level flag columns for names, trades,
  activity-type mapping, hours-vs-Lenel, and unmatched work orders.

These are written against the table/column names above. If you rename anything,
update the references (noted inline).

---

## 3. What YOU need to do in Power BI Desktop (Windows)

A `.pbix` can't be assembled off-Windows, so these steps are manual (one-time):

1. **Open** `CF_TA___Shop_Fab.pbix` in Power BI Desktop.
2. **Add the ingestion queries** — Home ▸ Transform data ▸ New Source ▸ Blank Query,
   then Advanced Editor, and paste each query from `PowerQuery_Ingestion.m`. Fix the
   file paths at the top of each (timesheet, Lenel export). Close & Apply.
3. **Relationships** — model view: link `Input - CF Timesheet` to
   `Reference - CF Employees` (Employee Name), to `Reference - CF Activity Types`
   (Trade), to `Input - IW37N Latest` (Work Order = Order), and `Input - Lenel`
   to employees (CF ID) + date.
4. **Add the check measures** — paste each measure from `DAX_Checks.dax` into the
   `tblMeasuresReporting` table (or a new `tblMeasuresChecks` table). Add the
   calculated columns to `Input - CF Timesheet`.
5. **Build a "Data Quality" page** — cards for the 5 check measures (red when > 0),
   plus a table filtered to `flagAnyError = 1` so Hillary sees exactly which rows fail.
6. **Point `Input - Shore` at the CF feed** (or swap visuals to `Input - CF Timesheet`)
   once you're happy the new feed matches.
7. **Set up refresh** — the timesheet, Lenel and IW37N should live in a fixed folder
   (or SharePoint) so a scheduled refresh picks up the daily files.

Tell me the final table/column names you settle on and I'll tighten the DAX/M to match.
