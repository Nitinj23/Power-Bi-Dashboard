// ============================================================================
//  CF TA Shop/Fab — Power Query (M) ingestion queries
//  Paste each block into a separate Blank Query (Advanced Editor) in Power BI.
//  Update the file paths in the two Parameters at the top first.
//  Written to match the existing model's "Input - " / "Reference - " naming.
// ============================================================================

// ---------------------------------------------------------------------------
// PARAMETERS  (Home > Manage Parameters > New — or just hardcode the paths)
// ---------------------------------------------------------------------------
// pTimesheetFolder : folder holding the daily CF timesheet workbooks
// pLenelFile       : the daily Lenel swipe export (xlsx or csv)
//
// Example values:
//   pTimesheetFolder = "C:\CF-TA\Timesheets"
//   pLenelFile       = "C:\CF-TA\Lenel\lenel_export.xlsx"


// ===========================================================================
// QUERY 1:  Input - CF Timesheet
//   Reads every "Timesheet" sheet in the timesheet folder, keeps real rows,
//   and shapes it like the labor feed the report expects.
// ===========================================================================
let
    Source        = Folder.Files(pTimesheetFolder),
    OnlyXlsx      = Table.SelectRows(Source, each Text.EndsWith([Extension], ".xlsx") and not Text.StartsWith([Name], "~$")),
    AddWorkbook   = Table.AddColumn(OnlyXlsx, "Data", each Excel.Workbook([Content], false)),
    Expand1       = Table.ExpandTableColumn(AddWorkbook, "Data", {"Name","Kind","Data"}, {"SheetName","Kind","SheetData"}),
    OnlyTimesheet = Table.SelectRows(Expand1, each [SheetName] = "Timesheet" and [Kind] = "Sheet"),
    // the data grid starts at row 11 (header) / row 12 (data) in the template
    Grid          = Table.AddColumn(OnlyTimesheet, "Rows", each
                        Table.Skip([SheetData], 10)),   // drop the logo/header band
    Combined      = Table.Combine(Table.Column(Grid, "Rows")),
    Promoted      = Table.PromoteHeaders(Combined, [PromoteAllScalars=true]),
    // keep the columns we care about (rename to match the model)
    Renamed       = Table.RenameColumns(Promoted, {
                        {"Employee Name", "EmployeeName"},
                        {"CF ID", "CF ID"},
                        {"Trade / Position", "Trade"},
                        {"Activity" & Character.FromNumber(10) & "Type", "Activity Type"},
                        {"Work Order", "Work Order"},
                        {"Total" & Character.FromNumber(10) & "Hours", "HoursTotal"},
                        {"RT" & Character.FromNumber(10) & "Hrs", "HoursRT"},
                        {"DT" & Character.FromNumber(10) & "Hrs", "HoursDT"},
                        {"Work Location", "Work Location"}
                    }, MissingField.Ignore),
    KeepReal      = Table.SelectRows(Renamed, each [EmployeeName] <> null and Text.Trim(Text.From([EmployeeName])) <> "" and [EmployeeName] <> "TOTAL"),
    Typed         = Table.TransformColumnTypes(KeepReal, {
                        {"EmployeeName", type text}, {"Trade", type text},
                        {"Work Order", type text}, {"HoursTotal", type number},
                        {"HoursRT", type number}, {"HoursDT", type number}
                    })
in
    Typed


// ===========================================================================
// QUERY 2:  Input - Lenel
//   Lenel swipe export -> hours on site per employee per day.
//   Adjust the column names to match your actual Lenel layout.
// ===========================================================================
let
    Source     = Excel.Workbook(File.Contents(pLenelFile), null, true),
    Sheet      = Source{[Item="Sheet1", Kind="Sheet"]}[Data],
    Promoted   = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    // EXPECTED Lenel columns (rename to your export): Badge/CF ID, Name, Date, Time In, Time Out
    Renamed    = Table.RenameColumns(Promoted, {
                    {"Badge ID", "CF ID"}, {"Cardholder", "EmployeeName"},
                    {"Event Date", "Date"}, {"First In", "TimeIn"}, {"Last Out", "TimeOut"}
                 }, MissingField.Ignore),
    Typed      = Table.TransformColumnTypes(Renamed, {
                    {"CF ID", type text}, {"Date", type date},
                    {"TimeIn", type datetime}, {"TimeOut", type datetime}}, MissingField.Ignore),
    LenelHours = Table.AddColumn(Typed, "LenelHours",
                    each try Duration.TotalHours([TimeOut] - [TimeIn]) otherwise null, type number)
in
    LenelHours


// ===========================================================================
// QUERY 3:  Reference - CF Employees   (from the timesheet template Reference tab)
// ===========================================================================
let
    Source   = Excel.Workbook(File.Contents(pTimesheetFolder & "\CF_Timesheet_Template.xlsx"), null, true),
    Ref      = Source{[Item="Reference", Kind="Sheet"]}[Data],
    // EMPLOYEES block is columns A:D starting row 2 (header) / row 3 (data)
    EmpCols  = Table.SelectColumns(Ref, {"Column1","Column2","Column3","Column4"}),
    Skip     = Table.Skip(EmpCols, 2),
    Named    = Table.RenameColumns(Skip, {
                  {"Column1","Employee Name"}, {"Column2","CF ID"},
                  {"Column3","Work Center"}, {"Column4","Default Trade"}}),
    Clean    = Table.SelectRows(Named, each [Employee Name] <> null and [Employee Name] <> "EMPLOYEES"),
    Typed    = Table.TransformColumnTypes(Clean, {{"Employee Name", type text}, {"CF ID", type text}})
in
    Typed


// ===========================================================================
// QUERY 4:  Reference - CF Activity Types  (trade -> SAP activity type)
// ===========================================================================
let
    Source   = Excel.Workbook(File.Contents(pTimesheetFolder & "\CF_Timesheet_Template.xlsx"), null, true),
    Ref      = Source{[Item="Reference", Kind="Sheet"]}[Data],
    // TRADES block is columns F:I starting row 2 (header) / row 3 (data)
    TrdCols  = Table.SelectColumns(Ref, {"Column6","Column7","Column8","Column9"}),
    Skip     = Table.Skip(TrdCols, 2),
    Named    = Table.RenameColumns(Skip, {
                  {"Column6","Trade"}, {"Column7","Activity Type"},
                  {"Column8","Activity Type Description"}, {"Column9","Work Center"}}),
    Clean    = Table.SelectRows(Named, each [Trade] <> null and [Trade] <> "TRADES  ->  SAP ACTIVITY TYPE"),
    Typed    = Table.TransformColumnTypes(Clean, {{"Trade", type text}, {"Activity Type", type text}})
in
    Typed
