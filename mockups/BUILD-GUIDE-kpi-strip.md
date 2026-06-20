# Build Guide — "Current Month Overview" KPI Strip (Power BI Desktop)

This rebuilds the yellow KPI banner into the cleaner strip shown in
`kpi-strip-redesign.html`, using only native Power BI features.

There are two routes. **Route A (Card "new" visual)** is the fastest and most
maintainable. **Route B (individual cards + shapes)** matches the mockup
pixel-for-pixel (icons + colored pills). Most people want A. Use B only if you
need the icon/pill styling exactly.

---

## 0. Apply the theme first (1 minute, do this regardless of route)

This sets the brand colors, fonts, rounded corners and shadows globally so you
stop styling every visual by hand.

1. **View** ribbon → **Themes** → dropdown arrow → **Browse for themes**.
2. Select `mockups/wolverine-theme.json` from this repo.
3. Every new card now inherits white background, 12px rounded corners and a soft
   shadow automatically.

---

## 1. Create the measures

Open **Modeling → New measure** and add these (adjust table/column names to your
model). Names match the mockup.

```DAX
Labour Hours =
SUM ( Timesheet[Hours] )                     -- field + indirect

Labour Spend =
SUM ( Timesheet[Cost] )

Billable Workforce FTE =
DISTINCTCOUNT ( Timesheet[EmployeeID] )       -- swap for your FTE logic

Apprentice Ratio =
DIVIDE (
    CALCULATE ( [Labour Hours], Employee[Class] = "Apprentice" ),
    [Labour Hours]
)

Workforce Average =
AVERAGEX ( VALUES ( 'Date'[WeekEnding] ), [Billable Workforce FTE] )

DT RT Ratio =
DIVIDE (
    CALCULATE ( [Labour Hours], Timesheet[RateType] = "DT" ),
    CALCULATE ( [Labour Hours], Timesheet[RateType] = "RT" )
)

Truck Hours Billed =
CALCULATE ( SUM ( Equipment[Hours] ), Equipment[Type] = "Truck" )
```

For the big-number formatting (4.61K, $4.8K): select the measure → **Measure
tools** → **Format** = Currency or Whole number, and set **Display units** on
the card visual itself (see step 3).

---

## 2. Build the section header (replaces the yellow banner)

Power BI has no "section" container, so compose it from shapes:

1. **Insert → Shapes → Rectangle**. Make it ~5px wide × 26px tall, fill brand
   orange `#E8731A`, corner radius 4. This is the accent bar.
2. **Insert → Text box**: type `Current Month Overview`, Segoe UI Semibold 18.
   Place it right of the accent bar.
3. **Insert → Text box** (smaller, gray `#6B7280`, 12px): `June 2026 · Field + Indirect`.
   - Optional dynamic version: drop a **Card** visual bound to a measure
     `Period Label = "Selected: " & SELECTEDVALUE('Date'[MonthName])`.
4. Select the three items → right-click → **Group**. Now they move together.
5. **Delete the yellow rectangle** entirely — the header replaces it.

---

## Route A — Card (new) visual  ⭐ recommended

The modern **Card** visual holds multiple KPIs in one tidy, auto-aligned visual.

1. **Visualizations** pane → the **Card (new)** icon (single rounded rectangle,
   *not* the legacy "123" card).
2. Drag all seven measures into the **Data** well. They lay out as a row of
   cards automatically.
3. Format the visual (Format pane):
   - **Layout** → set **Category count per row** so all 7 sit on one line; set
     **Spacing / Padding** ~14px for even gutters.
   - **Callout values** → font 24, Semibold, color `#1F2430`.
   - **Reference labels** → turn ON, use them for the descriptor line
     ("Field + indirect", "Indirect", etc.). Set a measure or static text per card.
   - **Cards → Shape**: rounded corners 12, **Accent bar** ON, position Left,
     and color it per category for the colored-edge look.
   - **Effects → Shadow** ON (already on via theme).
4. Done. This single visual is the whole strip, fully responsive.

> Tip: the **Accent bar** per card is the closest native equivalent to the
> colored icons in the mockup. Set each card's accent to a different theme color.

---

## Route B — Individual cards + shapes (pixel-match the mockup)

Use this only if you want the **icon tile + colored pill** look exactly.

For **each** of the 7 KPIs:

1. **Insert → Shapes → Rectangle**, ~165 × 120px, white fill, corner radius 12,
   shadow on (theme handles this). This is the card body.
2. Drop a legacy **Card** visual on top, bound to the measure. Format:
   - **Callout value** 24 Semibold; **Category label** OFF (you'll label manually).
   - **Background** → OFF (so the card body shape shows through).
   - Set **Display units** = Thousands (K) for hours/spend.
3. **Icon tile**: Insert → Shapes → Rectangle ~34×34px, radius 9, fill a light
   tint (e.g. `#FDEEE2`). Place top-right. Then **Insert → Image** with a small
   PNG icon (clock, people, $, etc.) on top — or use a Unicode glyph in a text box.
   - Free icon source: download mono PNGs and recolor to the category color.
4. **Label**: Insert → Text box, 10.5px, gray, uppercase, e.g. `LABOUR HOURS`.
5. **Pill**: Insert → Shapes → Rectangle, radius 20 (full pill), fill light tint,
   add a Text box with the descriptor (`Field + indirect`) in the matching color.
6. **Group** all elements of the card together, then **copy-paste** the group 6×
   and re-bind each card + edit labels. Faster than building each from scratch.

**Alignment for all 7:** select every card group → **Format** ribbon →
**Align → Align Top**, then **Distribute Horizontally** for perfectly even gaps.
Turn on **View → Snap to grid** while placing.

---

## 3. Restyle the filter + Reset button

- **Slicer** (Month/Week Ending): Format → **Slicer settings → Style = Dropdown**;
  Header font Segoe UI 12; turn on **Border** radius 8; shadow on.
- **Reset Filters**: Insert → **Buttons → Blank**. Fill brand orange `#E8731A`,
  text white "↺ Reset Filters", radius 8. **Action → Type = Bookmark** pointing
  to a "Default View" bookmark you record with all filters cleared.

---

## 4. Final alignment pass

1. **View → Gridlines** ON, **Snap to grid** ON.
2. Header group at top; 16px gap; KPI row below.
3. Select the KPI row + header, use **Format → Distribute** so gutters are equal.
4. Save. Compare against `kpi-strip-redesign.html`.

---

### Effort estimate
- Route A: ~20–30 min including measures.
- Route B: ~60–90 min (the icon/pill work is the time sink).

Recommendation: **start with Route A + the theme.** It gets you 90% of the
polish for 25% of the effort. Add Route B touches only if leadership wants the
icons.
