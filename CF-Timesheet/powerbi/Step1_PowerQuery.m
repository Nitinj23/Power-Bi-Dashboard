// ============================================================================
//  Step 1 — Timesheets folder  ->  flat "Step1" table (for Power BI)
//  Reads every CF timesheet .xlsx in a folder, unpivots the employee x PO-block
//  matrix, and EXPLODES each block's "WO<id>OP<op1>,<op2>,..." into one row per
//  op step (block hours repeated on each op-step row, exactly like your Step1.xlsx).
//
//  HOW TO USE (Power BI Desktop):
//   1. Home > Transform data > New Source > Blank Query > Advanced Editor.
//   2. Paste this whole query. Set TimesheetFolder to your drop folder.
//   3. Close & Apply. Drop new timesheets in the folder and hit Refresh.
//
//  Assumes the timesheet layout you have now (Timesheet tab):
//   Date=C9  Shift=D9  Vendor=E9 ; entry rows 14..33 ;
//   left cols  C=Employee D=Position I=OffsiteComment J=LOA L=Meal ;
//   22 PO blocks whose R/DT/Offsite/OffsiteType columns start at O,T,Y,... (step 5),
//   PO# in row 9, "WO..OP.." in row 10, timecard remark in row 37 ("Job Specific: ..").
// ============================================================================
let
    TimesheetFolder = "C:\CF-TA\Timesheets",          // <-- change me

    Blocks = List.Transform({0..21}, each 15 + _ * 5), // O,T,Y,... = first col of each block

    ExtractOne = (content as binary) as table =>
        let
            Wb   = Excel.Workbook(content, null, true),
            TS   = Wb{[Item="Timesheet", Kind="Sheet"]}[Data],
            Cell = (r as number, c as number) =>
                     Record.FieldOrDefault(TS{r-1}, "Column" & Text.From(c), null),
            Num  = (v) => let n = try Number.From(v) otherwise null in if n = null then 0 else n,
            Shift= Cell(9,4), Vendor = Cell(9,5), TheDate = Cell(9,3),

            Rows = List.Combine(List.Transform({14..33}, (r) =>
                     List.Combine(List.Transform(Blocks, (bc) =>
                        let
                            rt   = Num(Cell(r,bc)),  dt = Num(Cell(r,bc+1)),  off = Num(Cell(r,bc+2)),
                            has  = (rt<>0 or dt<>0 or off<>0) and Cell(r,3) <> null,
                            woop = Text.From(Cell(10,bc)),
                            wo   = try Text.BetweenDelimiters(woop,"WO","OP") otherwise null,
                            ops  = List.Transform(
                                       Text.Split(try Text.AfterDelimiter(woop,"OP") otherwise "", ","),
                                       each Text.Trim(_)),
                            rmk  = let t = Cell(37,bc) in
                                   if t = null then null else Text.Trim(Text.AfterDelimiter(Text.From(t), ":")),
                            base = [
                                Date              = TheDate,
                                Shift             = Shift,
                                Vendor            = Vendor,
                                Employee          = Cell(r,3),
                                Position          = Cell(r,4),
                                #"RT Hours"       = rt,
                                #"DT Hours"       = dt,
                                #"Offsite Hours"  = off,
                                #"Offsite Remarks"= Cell(r,9),        // I = Offsite Comment
                                #"Timecard remark"= rmk,              // row 37 "Job Specific: .."
                                #"PO Number"      = Cell(9,bc),
                                #"Work Order"     = wo,
                                #"Offsite Category"= Cell(r,bc+3),    // block offsite type
                                LOA               = if Cell(r,10)="Y" then 1 else 0,   // J
                                #"OT Meal"        = if Cell(r,12)="Y" then 1 else 0 ]  // L
                        in
                            if not has then {}
                            else List.Transform(ops, (op) => Record.AddField(base, "Op Step", op))
                     ))
                   )),
            T = Table.FromRecords(Rows)
        in
            T,

    Source = Folder.Files(TimesheetFolder),
    Files  = Table.SelectRows(Source, each Text.EndsWith(Text.Lower([Extension]),".xlsx")
                                        and not Text.StartsWith([Name],"~$")),
    AddRows = Table.AddColumn(Files, "Data", each ExtractOne([Content])),
    Combined = Table.Combine(AddRows[Data]),
    Result = Table.SelectColumns(Combined,
        {"Date","Shift","Vendor","Employee","Position","RT Hours","DT Hours","Offsite Hours",
         "Offsite Remarks","Timecard remark","PO Number","Work Order","Op Step",
         "Offsite Category","LOA","OT Meal"}),
    Typed = Table.TransformColumnTypes(Result, {
        {"Date", type date}, {"RT Hours", type number}, {"DT Hours", type number},
        {"Offsite Hours", type number}, {"LOA", Int64.Type}, {"OT Meal", Int64.Type},
        {"Work Order", type text}, {"Op Step", type text}, {"PO Number", type text}})
in
    Typed

// ----------------------------------------------------------------------------
// NEXT STAGE (the CF Illustration report):
//   - Join this table to the SAP op-step master (IW-type "Data" export) on
//     Work Order + Op Step to get WO Name / work centre.
//   - Allocate the block hours across its op steps (proportional or per your rule).
//   - Pivot by employee / PO / WO / Op Step for the approval printout, then export
//     each vendor/day to PDF.
// ----------------------------------------------------------------------------
