// ============================================================================
//  CF Timesheet -> Power BI  |  data cleanup queries
//  Paste each block into its own Blank Query (Home > Transform data >
//  New Source > Blank Query > Advanced Editor). Set the folder path first.
//
//  Layout assumed (Timesheet tab of CF_Timesheet_v5):
//    Date=C9  Shift=D9  Vendor=E9 ; entry rows 14..63 ;
//    left cols  C=Employee  D=Position(Trade)  I=Additional Comment  J=LOA  K=Meal ;
//    22 PO blocks; each block's R/DT/SwipeDev/OffsiteType columns start at
//    M,R,W,AB,... (every 5th col); PO# in row 9, "WO<id>OP<ops>" in row 10,
//    "Job Specific: .." remark in row 67.
// ============================================================================

// ---------------------------------------------------------------------------
// QUERY 1:  SAP  (the IW37N / op-step master -> WO Name + work centre)
//   Point at a folder of IW37N exports, or one file. One row per WO+op step.
// ---------------------------------------------------------------------------
let
    SapFile = "C:\CF-TA\SAP\IW37N.xlsx",         // <-- change me (or use Folder.Files)
    Src  = Excel.Workbook(File.Contents(SapFile), null, true),
    Sht  = Src{[Kind="Sheet", Item="Sheet1"]}[Data],     // adjust sheet name
    Prom = Table.PromoteHeaders(Sht, [PromoteAllScalars=true]),
    Keep = Table.SelectColumns(Prom, {"Order","Description","Activity","Op. Short Text","Oper.WorkCenter"}, MissingField.Ignore),
    Typed= Table.TransformColumnTypes(Keep, {{"Order", type text}, {"Activity", type text}}),
    // WO-level name (one row per Order) and a WOOP key for the op-step join
    WOOP = Table.AddColumn(Typed, "WOOP", each "WO" & [Order] & "OP" & [Activity], type text)
in
    WOOP


// ---------------------------------------------------------------------------
// QUERY 2:  Timesheets  (folder -> one row per Employee x Work Order)
//   This is the PRINT / CF-Report grain: hours stay at the WO level, OP steps
//   are kept as the entered list. Join WO Name from the SAP query.
// ---------------------------------------------------------------------------
let
    TimesheetFolder = "C:\CF-TA\Timesheets",      // <-- change me
    Blocks = List.Transform({0..21}, each 13 + _ * 5),   // M,R,W,... first col of each block

    Extract = (content as binary) as table =>
        let
            Wb   = Excel.Workbook(content, null, true),
            TS   = Wb{[Item="Timesheet", Kind="Sheet"]}[Data],
            Cell = (r,c) => Record.FieldOrDefault(TS{r-1}, "Column" & Text.From(c), null),
            Num  = (v) => let n = try Number.From(v) otherwise null in if n=null then 0 else n,
            TheDate = Cell(9,3), Shift = Cell(9,4), Vendor = Cell(9,5),
            Rows = List.Combine(List.Transform({14..63}, (r) =>
                     List.Transform(Blocks, (bc) =>
                        let
                            rt=Num(Cell(r,bc)), dt=Num(Cell(r,bc+1)), sw=Num(Cell(r,bc+2)),
                            woop = Text.From(Cell(10,bc)),
                            wo   = try Text.BetweenDelimiters(woop,"WO","OP") otherwise null,
                            ops  = try Text.Trim(Text.AfterDelimiter(woop,"OP")) otherwise null,
                            rmk  = let t=Cell(67,bc) in if t=null then null else Text.Trim(Text.AfterDelimiter(Text.From(t),":"))
                        in
                            if (rt=0 and dt=0 and sw=0) or Cell(r,3)=null then null
                            else [
                                Date=TheDate, Shift=Shift, Vendor=Vendor,
                                #"Job Description"=Cell(9,bc),        // PO / job number
                                Employee=Cell(r,3), Trade=Cell(r,4),
                                #"WO ID"=wo, #"OP Steps"=ops,
                                #"DT Hrs"=dt, #"RT Hrs"=rt, #"Offsite Hrs"=sw,
                                #"Total Hrs"=rt+dt,
                                #"Offsite Type"=Cell(r,bc+3),
                                #"Additional Comment"=Cell(r,9),
                                #"Timecard Remark"=rmk,
                                LOA = if Cell(r,10)="Y" then 1 else 0,
                                #"OT Meal" = if Cell(r,11)="Y" then 1 else 0 ]
                     ))),
            Clean = List.RemoveNulls(Rows)
        in
            Table.FromRecords(Clean),

    Src   = Folder.Files(TimesheetFolder),
    Files = Table.SelectRows(Src, each Text.EndsWith(Text.Lower([Extension]),".xlsx") and not Text.StartsWith([Name],"~$")),
    AddT  = Table.AddColumn(Files, "Data", each Extract([Content])),
    Comb  = Table.Combine(AddT[Data]),
    // WO Name from SAP (Query1) -> merge on WO ID = Order
    WOName = Table.Distinct(Table.SelectColumns(SAP, {"Order","Description"})),
    Merged = Table.NestedJoin(Comb, {"WO ID"}, WOName, {"Order"}, "wo", JoinKind.LeftOuter),
    Named  = Table.AddColumn(Merged, "WO Name", each try [wo]{0}[Description] otherwise null),
    Out    = Table.RemoveColumns(Named, {"wo"}),
    Typed  = Table.TransformColumnTypes(Out, {
                {"Date", type date}, {"RT Hrs", type number}, {"DT Hrs", type number},
                {"Offsite Hrs", type number}, {"Total Hrs", type number},
                {"WO ID", type text}, {"OP Steps", type text}})
in
    Typed


// ---------------------------------------------------------------------------
// QUERY 3 (optional):  Op-step split for SAP upload
//   Explodes each WO row into one row per op step and splits the hours evenly
//   across the steps (change the allocation rule if you prefer proportional).
// ---------------------------------------------------------------------------
let
    Base   = Timesheets,                                  // Query 2
    AddOps = Table.AddColumn(Base, "OpList", each
                if [OP Steps]=null then {} else List.Transform(Text.Split([OP Steps], ","), each Text.Trim(_))),
    Expand = Table.ExpandListColumn(AddOps, "OpList"),
    Alloc  = Table.AddColumn(Expand, "n", each let l=[OpList] in 1),   // placeholder; per-row count below
    // count op steps per original WO row, then divide hours
    Grp    = Table.Group(Expand, {"Date","Employee","WO ID"}, {{"cnt", each Table.RowCount(_), Int64.Type}}),
    Join   = Table.NestedJoin(Expand, {"Date","Employee","WO ID"}, Grp, {"Date","Employee","WO ID"}, "g", JoinKind.LeftOuter),
    Cnt    = Table.AddColumn(Join, "OpCount", each try [g]{0}[cnt] otherwise 1),
    Split  = Table.AddColumn(Cnt, "RT (split)", each [RT Hrs] / List.Max({[OpCount],1}), type number),
    SplitD = Table.AddColumn(Split, "DT (split)", each [DT Hrs] / List.Max({[OpCount],1}), type number),
    Final  = Table.RenameColumns(Table.RemoveColumns(SplitD,{"g","OP Steps"}), {{"OpList","Op Step"}})
in
    Final
