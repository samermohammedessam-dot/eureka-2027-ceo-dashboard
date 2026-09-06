/**
 * Writes native Google Sheets formulas (SUMIFS/COUNTIFS/QUERY) into 01_CEO_Dashboard and
 * 02_Weekly_CEO so the raw spreadsheet is still useful to anyone who opens it directly,
 * without needing the web app. Column letters are derived from SHEET_SCHEMA so this never
 * breaks if a column is reordered.
 */
function colLetter_(sheetName, key) {
  var schema = getSchema(sheetName);
  var idx = schema.map(function (c) { return c.key; }).indexOf(key);
  if (idx === -1) throw new Error('Unknown column ' + key + ' on ' + sheetName);
  return columnToLetter_(idx + 1);
}

function columnToLetter_(column) {
  var letter = '';
  while (column > 0) {
    var rem = (column - 1) % 26;
    letter = String.fromCharCode(65 + rem) + letter;
    column = Math.floor((column - 1) / 26);
  }
  return letter;
}

function rangeRef_(sheetName, key) {
  var letter = colLetter_(sheetName, key);
  return "'" + sheetName + "'!" + letter + '2:' + letter;
}

function refreshDashboardSheet() {
  var sheet = ss_().getSheetByName(SHEETS.CEO_DASHBOARD);
  if (!sheet) return;

  var revRecognized = rangeRef_(SHEETS.REVENUE, 'revenueRecognized');
  var revCollected = rangeRef_(SHEETS.REVENUE, 'amountCollected');
  var revOutstanding = rangeRef_(SHEETS.REVENUE, 'outstanding');
  var revContractValue = rangeRef_(SHEETS.REVENUE, 'contractValue');
  var revSignDate = rangeRef_(SHEETS.REVENUE, 'contractSigningDate');
  var expBudget = rangeRef_(SHEETS.EXPENSES, 'budgetedAmount');
  var expActual = rangeRef_(SHEETS.EXPENSES, 'actualAmount');
  var pipeValue = rangeRef_(SHEETS.PIPELINE, 'estimatedOpportunityValue');
  var pipeWeighted = rangeRef_(SHEETS.PIPELINE, 'weightedValue');
  var pipeStage = rangeRef_(SHEETS.PIPELINE, 'stage');
  var taskStatus = rangeRef_(SHEETS.TASKS, 'status');

  // Row 3 is the "Metric / Value" header (see buildCeoDashboardSheetShell_ in SetupSheets.gs)
  // — data starts at row 4. Re-assert the header text every time this runs (not just when
  // the shell is first built): this menu item is meant to be run on its own, repeatedly,
  // without rebuilding the sheet first, so it must never depend on row 3 already being
  // correct from some earlier run. setValue() replaces any stale formula/value left over
  // from a previous version of this function, and '@' forces plain-text display regardless
  // of whatever number format that stale content carried.
  sheet.getRange('A3').setValue('Metric').setNumberFormat('@');
  sheet.getRange('B3').setValue('Value').setNumberFormat('@');
  sheet.getRange('D3').setValue('Metric').setNumberFormat('@');
  sheet.getRange('E3').setValue('Value').setNumberFormat('@');

  // Every cell reference below is deliberately one row below the metric's row number would
  // suggest at first glance; double-check against the shell's `labels` array (row 4 = 2027
  // Revenue Target ... row 11 = Budget Variance / Tasks Completion %) before changing any of
  // these addresses.
  sheet.getRange('B4').setFormula('=' + REVENUE_TARGET); // 2027 Revenue Target
  sheet.getRange('B5').setFormula('=SUM(' + revRecognized + ')'); // Revenue Actual (Recognized)
  sheet.getRange('B6').setFormula('=IFERROR(B5/B4,0)').setNumberFormat('0%'); // Revenue Achievement %
  sheet.getRange('B7').setFormula('=' + ANNUAL_BOOKINGS_TARGET); // Annual Bookings Target
  sheet.getRange('B8').setFormula('=SUMPRODUCT((YEAR(' + revSignDate + ')=' + FISCAL_YEAR + ')*' + revContractValue + ')'); // Bookings Actual
  sheet.getRange('B9').setFormula('=' + TOTAL_GROWTH_BUDGET_2027); // Growth Budget (Section 7)
  sheet.getRange('B10').setFormula('=SUM(' + expActual + ')'); // Actual Growth Spend
  sheet.getRange('B11').setFormula('=B9-B10'); // Budget Variance

  sheet.getRange('E4').setFormula('=SUMIF(' + pipeStage + ',"<>Won",' + pipeValue + ')-SUMIF(' + pipeStage + ',"Lost",' + pipeValue + ')'); // Total Pipeline
  sheet.getRange('E5').setFormula('=SUMIF(' + pipeStage + ',"<>Won",' + pipeWeighted + ')-SUMIF(' + pipeStage + ',"Lost",' + pipeWeighted + ')'); // Weighted Pipeline
  sheet.getRange('E6').setFormula('=IFERROR(E4/' + REVENUE_TARGET + ',0)').setNumberFormat('0.0"x"'); // Pipeline Coverage (x)
  sheet.getRange('E7').setFormula('=SUM(' + revCollected + ')'); // Cash Collected
  sheet.getRange('E8').setFormula('=SUM(' + revOutstanding + ')'); // Outstanding Receivables
  sheet.getRange('E9').setFormula('=IFERROR(COUNTIF(' + pipeStage + ',"Won")/(COUNTIF(' + pipeStage + ',"Won")+COUNTIF(' + pipeStage + ',"Lost")),0)').setNumberFormat('0%'); // Win Rate
  sheet.getRange('E10').setFormula('=COUNTIF(' + pipeStage + ',"Won")'); // Deals Won (YTD) — a count, not currency, deliberately left out of the EGP formatting loop below
  sheet.getRange('E11').setFormula('=IFERROR(COUNTIF(' + taskStatus + ',"Completed")/COUNTA(' + taskStatus + '),0)').setNumberFormat('0%'); // Tasks Completion %

  Object.keys({ B4: 1, B5: 1, B7: 1, B8: 1, B9: 1, B10: 1, B11: 1, E4: 1, E5: 1, E7: 1, E8: 1 }).forEach(function (a) {
    sheet.getRange(a).setNumberFormat('#,##0 "EGP"');
  });

  refreshWeeklyCeoSheet_();
  SpreadsheetApp.flush();
  return 'Dashboard sheet formulas refreshed.';
}

function refreshWeeklyCeoSheet_() {
  var sheet = ss_().getSheetByName(SHEETS.WEEKLY_CEO);
  if (!sheet) return;
  var weekStart = rangeRef_(SHEETS.WEEKLY_EXECUTION, 'startDate');
  var weekEnd = rangeRef_(SHEETS.WEEKLY_EXECUTION, 'endDate');
  var weekIdCol = rangeRef_(SHEETS.WEEKLY_EXECUTION, 'weekId');
  var weekSales = rangeRef_(SHEETS.WEEKLY_EXECUTION, 'salesTargetWeek');
  var weekBudget = rangeRef_(SHEETS.WEEKLY_EXECUTION, 'budgetPlannedWeek');
  var taskWeekId = rangeRef_(SHEETS.TASKS, 'weekId');
  var taskStatus = rangeRef_(SHEETS.TASKS, 'status');
  var taskDue = rangeRef_(SHEETS.TASKS, 'dueDate');
  var taskPriority = rangeRef_(SHEETS.TASKS, 'priority');
  var taskLight = rangeRef_(SHEETS.TASKS, 'trafficLight');
  var expDate = rangeRef_(SHEETS.EXPENSES, 'date');
  var expActual = rangeRef_(SHEETS.EXPENSES, 'actualAmount');
  var revDueDate = rangeRef_(SHEETS.REVENUE, 'dueDate');
  var revOutstanding = rangeRef_(SHEETS.REVENUE, 'outstanding');
  var revCollDate = rangeRef_(SHEETS.REVENUE, 'collectionDate');
  var revCollAmt = rangeRef_(SHEETS.REVENUE, 'amountCollected');
  var revSignDate = rangeRef_(SHEETS.REVENUE, 'contractSigningDate');
  var revContractValue = rangeRef_(SHEETS.REVENUE, 'contractValue');

  // Row 3 is the "This Week Metric / Value / End of Week Metric / Value" header (see
  // buildWeeklyCeoSheetShell_ in SetupSheets.gs) — data starts at row 4, so $B$4 (not $B$3)
  // is the cell every other formula below looks up the current week's ID from. Re-assert the
  // header text every time this runs, the same way refreshDashboardSheet() does above, so it
  // self-heals regardless of what an earlier version of this function may have left behind.
  sheet.getRange('A3').setValue('This Week Metric').setNumberFormat('@');
  sheet.getRange('B3').setValue('Value').setNumberFormat('@');
  sheet.getRange('C3').setValue('End of Week Metric').setNumberFormat('@');
  sheet.getRange('D3').setValue('Value').setNumberFormat('@');

  var currentWeekId = '=INDEX(' + weekIdCol + ',MATCH(1,(TODAY()>=' + weekStart + ')*(TODAY()<=' + weekEnd + '),0))';
  sheet.getRange('B4').setFormula(currentWeekId); // Current Week ID
  sheet.getRange('B5').setFormula('=IFERROR(INDEX(' + weekSales + ',MATCH($B$4,' + weekIdCol + ',0)),0)').setNumberFormat('#,##0 "EGP"'); // Sales Target
  // Expected Collections = receivables DUE this week (outstanding amounts whose due date
  // falls in the current week) — matches the web app's WeeklyApi.gs definition. The
  // previous version summed amountCollected by collectionDate instead, which is what was
  // actually COLLECTED, not what's expected — that number now correctly lives in "Revenue
  // Collected" below instead.
  sheet.getRange('B6').setFormula('=SUMIFS(' + revOutstanding + ',' + revDueDate + ',">="&INDEX(' + weekStart + ',MATCH($B$4,' + weekIdCol + ',0)),' + revDueDate + ',"<="&INDEX(' + weekEnd + ',MATCH($B$4,' + weekIdCol + ',0)))').setNumberFormat('#,##0 "EGP"'); // Expected Collections
  sheet.getRange('B7').setFormula('=COUNTIFS(' + taskWeekId + ',$B$4,' + taskPriority + ',"Critical")'); // Critical Tasks
  sheet.getRange('B8').setFormula('=COUNTIFS(' + taskWeekId + ',$B$4,' + taskStatus + ',"Blocked")'); // Blocked Tasks
  sheet.getRange('B9').setFormula('=COUNTIFS(' + taskWeekId + ',$B$4,' + taskLight + ',"RED")'); // Overdue Tasks
  sheet.getRange('B10').setFormula('=IFERROR(INDEX(' + weekBudget + ',MATCH($B$4,' + weekIdCol + ',0)),0)').setNumberFormat('#,##0 "EGP"'); // Budget Planned This Week

  sheet.getRange('D4').setFormula('=COUNTIFS(' + taskWeekId + ',$B$4)'); // Tasks Planned
  sheet.getRange('D5').setFormula('=COUNTIFS(' + taskWeekId + ',$B$4,' + taskStatus + ',"Completed")'); // Tasks Completed
  sheet.getRange('D6').setFormula('=IFERROR(D5/D4,0)').setNumberFormat('0%'); // Completion %
  sheet.getRange('D7').setFormula('=COUNTIFS(' + taskWeekId + ',$B$4,' + taskStatus + ',"<>Completed",' + taskDue + ',"<"&TODAY())'); // Tasks Overdue
  sheet.getRange('D8').setFormula('=SUMIFS(' + expActual + ',' + expDate + ',">="&INDEX(' + weekStart + ',MATCH($B$4,' + weekIdCol + ',0)),' + expDate + ',"<="&INDEX(' + weekEnd + ',MATCH($B$4,' + weekIdCol + ',0)))').setNumberFormat('#,##0 "EGP"'); // Spend This Week
  // Revenue Collected = actually collected this week (amountCollected by collectionDate) —
  // previously this cell just pointed at "=B5" (the mislabeled Expected Collections cell)
  // instead of having its own formula.
  sheet.getRange('D9').setFormula('=SUMIFS(' + revCollAmt + ',' + revCollDate + ',">="&INDEX(' + weekStart + ',MATCH($B$4,' + weekIdCol + ',0)),' + revCollDate + ',"<="&INDEX(' + weekEnd + ',MATCH($B$4,' + weekIdCol + ',0)))').setNumberFormat('#,##0 "EGP"'); // Revenue Collected
  sheet.getRange('D10').setFormula('=SUMIFS(' + revContractValue + ',' + revSignDate + ',">="&INDEX(' + weekStart + ',MATCH($B$4,' + weekIdCol + ',0)),' + revSignDate + ',"<="&INDEX(' + weekEnd + ',MATCH($B$4,' + weekIdCol + ',0)))').setNumberFormat('#,##0 "EGP"'); // Bookings
}
