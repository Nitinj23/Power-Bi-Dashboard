# Build Guide — Wolverine / Shell KPI Dashboard in Power BI

Two routes. **Route A** embeds the HTML as-is (fast, looks identical, not interactive).
**Route B** rebuilds it as native Power BI visuals (the production, refresh-and-go version
your non-tech users will run weekly). Do A for a quick proof; do B for the real thing.

---

## Route A — Embed the HTML (≈10 min)

1. Install **Power BI Desktop** (free, Microsoft Store).
2. **Get Data → Blank Query → Advanced Editor**, paste:
   ```
   let Source = #table({"html"}, {{ "PASTE_HTML_HERE" }}) in Source
   ```
   Replace `PASTE_HTML_HERE` with the contents of `Wolverine_Shell_KPI_Report.html`
   (open it in Notepad, copy all, escape any `"` as `""`). Name the query `ReportHTML`.
3. **Visualizations → … → Get more visuals → import "HTML Content"** (by Daniel Marsh-Patrick).
4. Drop the **HTML Content** visual on the canvas, drag `ReportHTML[html]` into its **Values**.
5. The report renders. ⚠️ It's static — filters won't change it. That's the limitation; use
   Route B when you want interactivity.

---

## Route B — Native Power BI build (the real one)

### Phase 1 · Load the data
1. **Get Data → Excel** → `data/Data.xlsx` → tick **`Data`** and **`Projects`** → **Transform Data**.
2. **Get Data → Excel** → `data/Safety_Learning_Cards.xlsx` → tick **`2026`** → load as table `Safety`.

### Phase 2 · Shape in Power Query (this replaces the script's `classify()` logic)
Select the **Data** query. Add these via **Add Column → Custom Column**:

**Trade**
```m
if [colRELShoreTrade] = null then "Other"
else if Text.Contains([colRELShoreTrade],"Pipefitter") then "Pipefitter"
else if Text.Contains([colRELShoreTrade],"Boilermaker") then "Boilermaker"
else if Text.Contains([colRELShoreTrade],"Labourer") or Text.Contains([colRELShoreTrade],"Laborer") then "Labourer"
else if Text.Contains([colRELShoreTrade],"Operating Engineer") then "Operating Eng"
else if Text.Contains([colRELShoreTrade],"Truck") or Text.Contains([colRELShoreTrade],"Van") then "Vehicle"
else "Other"
```

**Tier** (DFL vs Foreman-&-above vs Indirect)
```m
let s = [colRELShoreTrade], code = if s = null then "" else Text.BeforeDelimiter(s,"-") in
if s = null then "Other"
else if Text.StartsWith(code,"111") or Text.Contains(s,"Superintendent") or Text.Contains(s,"PM/") then "Indirect"
else if Text.StartsWith(code,"131") or Text.Contains(s,"Planner") or Text.Contains(s,"Time Keeper") or Text.Contains(s,"Quality Control") or Text.Contains(s,"Manager") then "Indirect"
else if Text.Contains(s,"Foreman") then "FM"
else if [Trade] = "Vehicle" then "Vehicle"
else "DFL"
```

**IsApprentice**
```m
if [colRELShoreTrade] <> null and Text.Contains([colRELShoreTrade],"Apprentice") then "Apprentice" else "Other"
```

**WeekDate** (the `Date` column is text like `"Friday, April 10, 2026"`)
```m
Date.FromText(Text.AfterDelimiter([Date], ", "), [Culture="en-US"])
```
Then **Add Column → Date → Month → Start of Month** on `WeekDate` → name it `Month`.

Do the same `Month` step on the **Safety** query using its `Date:` column. **Close & Apply.**

### Phase 3 · Model
- **Model view** → drag `Projects[JobNumber]` onto `Data[JobNumber]` (1-to-many).
- Optional but recommended: **Modeling → New Table** for a calendar:
  `Calendar = CALENDARAUTO()`, then relate `Calendar[Date]` to `Data[WeekDate]`.

### Phase 4 · Measures (New Measure for each)
```DAX
Total Hours   = CALCULATE(SUM(Data[Split Hours]), Data[Attribute] IN {"HoursRT","HoursDT"})
RT Hours      = CALCULATE([Total Hours], Data[Attribute] = "HoursRT")
DT Hours      = CALCULATE([Total Hours], Data[Attribute] = "HoursDT")
DFL Hours     = CALCULATE([Total Hours], Data[Tier] = "DFL")
FM Hours      = CALCULATE([Total Hours], Data[Tier] = "FM")
Indirect Hours= CALCULATE([Total Hours], Data[Tier] = "Indirect")
Vehicle Hours = CALCULATE([Total Hours], Data[Trade] = "Vehicle")
Apprentice Hrs= CALCULATE([Total Hours], Data[IsApprentice] = "Apprentice")
Apprentice %  = DIVIDE([Apprentice Hrs], [Total Hours])

Total Cost    = SUM(Data[Split $$])
Labour Spend  = CALCULATE([Total Cost], Data[Grouping] = "Labour")
Equip Spend   = CALCULATE([Total Cost], Data[Grouping] = "Equip")
ThirdParty Sp = CALCULATE([Total Cost], Data[Grouping] = "3rd Party")

Headcount     = DISTINCTCOUNT(Data[EmployeeName])
Crew Mix Base = DIVIDE([DFL Hours], [FM Hours])          -- show as "1 : [value]"
Crew Mix Txt  = "1 : " & FORMAT([Crew Mix Base], "0.0")
RT to DT      = DIVIDE([RT Hours], [DT Hours])

-- Safety (target lines)
Safety Cards     = COUNTROWS(Safety)
Safety Target    = 20
Crew Mix Target  = 8
```

### Phase 5 · Build the visuals (tile → visual → fields)

**Page 1 — Performance & Cost**
| Tile | Visual | Setup |
|---|---|---|
| KPI strip | 6 × **Card** (or KPI) | `Total Hours`, `Headcount`, `Labour Spend`, `Apprentice %`, `RT to DT`, `Vehicle Hours` |
| Exposure-hours trend | **Clustered column** | Axis `Month` · Value `Total Hours` |
| Hours by trade DFL/FM | **Stacked bar** | Axis `Trade` · Legend `Tier` (filter to DFL, FM) · Value `Total Hours` |
| Crew mix ratio | **Card** per trade or **KPI** | `Crew Mix Txt`, target `Crew Mix Target` |
| Charge mix RT/DT | **Donut** | Legend `Attribute` (HoursRT/DT) · Value `Total Hours` |
| Spend by category | **100% stacked bar** | Legend `Grouping` · Value `Total Cost` |
| Spend by Shell group | **Bar** | Axis `Projects[Pro_Grouping]` · Value `Total Cost` |
| Portfolio | **Cards** | active jobs = `COUNTROWS(FILTER(Projects, Projects[Status]="Active"))`, `SUM(Projects[PO Value])` |

**Page 2 — HSSE & Safety**
| Tile | Visual | Setup |
|---|---|---|
| Lagging tiles | **Cards** | First Aids/MTC/LWD/Recordable/TRIF (0 until feed adds them) |
| Safety obs vs target | **Gauge** | Value `Safety Cards` · Target `Safety Target` |
| Safety obs trend | **Column + analytics line** | Axis `Month` · Value `Safety Cards` · add constant line at 20 |
| By category / dept / location | **Bar** ×3 | Axis `Learner Mindset Category:` / `Functional Department?` / `Location:` · Value `Safety Cards` |
| Training compliance | **Gauge** | placeholder 100% until data arrives |

Add a **Slicer** for `Month` (and `Projects[ProjectManager]`) on each page — that's the
interactivity the HTML can't give you.

### Phase 6 · Make it look like the mockup
**View → Themes → Browse for themes** and load a JSON with the brand palette:
```json
{ "name": "Wolverine-Shell",
  "dataColors": ["#2E7BB5","#E8651E","#1AA191","#6F5AA8","#D6122A","#F6C700"],
  "background": "#FFFFFF", "foreground": "#1B2B3A", "tableAccent": "#E8651E" }
```
Use the preview PNG as your layout reference for placement and titles.

### Phase 7 · Hand-off to non-tech users (the whole point)
1. **Publish** to the Power BI Service (or save the `.pbix` to SharePoint/OneDrive).
2. Point the queries at a **fixed file path** the team controls (the `data/` folder).
3. Weekly routine for them = **drop the refreshed Excel in `data/` → open report → Home → Refresh.**
   No layout edits, ever. (Or set Scheduled Refresh in the Service so it's automatic.)

---

### When the data feed grows
The Python generator (`generate_kpi_report.py`) stays useful for fast HTML previews/PDF packs —
re-run it anytime. The native Power BI model auto-picks-up new rows on Refresh. The placeholder
tiles (HSSE lagging, training, welds, separate Overtime) only need their fields mapped once the
client feed includes them.
