# Resource Loading Template — Sept 2026 to year end

`Resource_Loading_Template.xlsx` — issue to PMs for completion.

Built in response to Ken Barrett's request for a resource-loaded schedule,
week by week, September to year end.

No instructions tab — guidance is a one-line legend on row 2 of each PM tab,
and the covering email carries the rest.

## Structure

- **Summary - Trade** — FTE by Trade x Week Ending. 100% formula driven
- **Summary - Client** — FTE by Client x Week Ending. 100% formula driven
- **11 PM tabs** — one per PM, pre-loaded with their active jobs
- **Lists** — trades, clients, PMs (drives the dropdowns and summary rows)
- **Input - Project List** — 205 active jobs, source data

18 weeks, week-ending Saturday, 05-Sep-2026 to 02-Jan-2027, carried over
from the original file.

## Both entry methods supported

PMs can enter FTE either way, and both roll into the same summary totals:

- **By Job** — pre-listed job rows; pick a Trade, enter FTE by week
- **By Client** — blank rows at the bottom; leave Job # empty, pick Client
  and Trade, enter FTE by week

## Verified

`recalc.py`: 1,468 formulas, 0 errors. Beyond that, a live data test wrote
FTE into three PM tabs (including one client-level row with Job # blank)
and confirmed both summaries picked up the right figures and reconciled to
the same grand total.

## Open items before issue

1. **The trade list is not agreed.** 17 categories are a first pass by me,
   not from any existing standard. Ken and the PMs should confirm before
   this goes out — the Trade summary rows follow this list.
2. **Two PMs had jobs but no tab in the original file** — Pendlebury, Jay
   (3 jobs) and Kennedy, Vince (1 job). Tabs added, so those 4 jobs are no
   longer invisible. Confirm both should be in scope.
3. Job descriptions carried mojibake in the source (en-dashes read as
   "a€“"); repaired on import.
