# Wolverine / Shell Maintenance — KPI Report

A self-contained, **no-JavaScript** HTML report (two pages) built directly from the
client data and the client's own *2026 KPI template* (which supplies the targets).

Designed for weekly director / project-controls reviews, and to drop into Power BI.

## Files
| File | Purpose |
|---|---|
| `generate_kpi_report.py` | Reads the workbooks and regenerates the HTML. **Re-run after every data refresh.** |
| `Wolverine_Shell_KPI_Report.html` | The report. Open in any browser; print to PDF for the meeting pack. |
| `data/Data.xlsx` | Fact table (`Data`) + `Projects` lookup. |
| `data/KPI_Template_2026.xlsm` | Client scorecard — source of the **targets**. |
| `data/Safety_Learning_Cards.xlsx` | Safety observation cards (HSSE page). |

## Regenerate
```bash
pip install openpyxl
python3 generate_kpi_report.py
```
Nothing else changes — non-tech users only replace the files in `data/` and re-run (or
hit Refresh once it's wired into Power BI). No layout edits required.

## The two pages
**1 · Performance & Cost** — KPI scorecard vs targets (RAG status) · exposure-hours trend ·
DFL vs Foreman-&-above by trade · crew-mix ratio bullets (target 1:8) · RT/DT charge mix ·
spend by category & Shell group · portfolio summary.

**2 · HSSE & Safety** — lagging-indicator tiles (First Aids, MTC, LWD, Near Miss, Recordable,
TRIF) · Safety Observations vs 20/month target (gauge + trend) · training compliance · cards
by category / department / location.

## Putting it in Power BI
The page is static markup, so it works two ways:

1. **HTML Content custom visual** (e.g. *HTML Content (lite)* by Daniel Marsh-Patrick) — paste
   the markup into a measure and point the visual at it. Good for an exact-look embed.
2. **As a build spec for native visuals** (recommended for full interactivity / slicers). Field
   map per tile:

| Tile | Native visual | Fields / measure |
|---|---|---|
| Exposure hours trend | Clustered column | `Date`→month on axis, `Σ Split Hours` |
| Hours by trade DFL/FM | Stacked bar | Trade group, tier (DFL/FM), `Σ Split Hours` |
| Crew mix ratio | KPI / bullet | `Σ FM Hrs` ÷ `Σ DFL Hrs` vs 8 |
| Charge mix RT/DT | Donut | `Attribute` (HoursRT/DT), `Σ Split Hours` |
| Spend by category | 100% stacked bar | `Grouping`, `Σ Split $$` |
| Spend by Shell group | Bar | `Pro_Grouping`, `Σ Split $$` |
| Safety obs trend | Column + target line | card `Date`→month, count, target 20 |

### Role classification (mirrors `classify()` in the script)
- **Trade** from `colRELShoreTrade` name (Pipefitter / Boilermaker / Labourer / Operating Eng / Vehicle).
- **Tier**: code `111*` or PM/Superintendent → *Site Indirect*; code `131*` or Planner/Time Keeper/QC/Manager → *Site Indirect*; name contains *Foreman* → *FM & above*; otherwise *DFL*.
- **Apprentice** = name contains "Apprentice".

## Tiles awaiting client data (currently shown as targets/placeholders)
These exist in the client template but aren't in the data feed yet — wire them when the feed adds them:
- HSSE lagging counts (First Aids, MTC, LWD, Recordable, TRIF) — currently 0 / on-target.
- Training compliance % — shown at 100%.
- Quality / welds (Butt, Socket, X-Ray, MT/PT, rework rate).
- Standard-time vs Overtime split (feed has Regular + Double only; no separate OT yet).
