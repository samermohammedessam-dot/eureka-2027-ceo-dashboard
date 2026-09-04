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

  sheet.getRange('B3').setFormula('=' + REVENUE_TARGET);
  sheet.getRange('B4').setFormula('=SUM(' + revRecognized + ')');
  sheet.getRange('B5').setFormula('=IFERROR(B4/B3,0)').setNumberFormat('0%');
  sheet.getRange('B6').setFormula('=' + ANNUAL_BOOKINGS_TARGET);
  sheet.getRange('B7').setFormula('=SUMPRODUCT((YEAR(' + revSignDate + ')=' + FISCAL_YEAR + ')*' + revContractValue + ')');
  sheet.getRange('B8').setFormula('=' + TOTAL_GROWTH_BUDGET_2027); // Growth Budget total (Section 7)
  sheet.getRange('B9').setFormula('=SUM(' + expActual + ')');
  sheet.getRange('B10').setFormula('=B8-B9');

  sheet.getRange('E3').setFormula('=SUMIF(' + pipeStage + ',"<>Won",' + pipeValue + ')-SUMIF(' + pipeStage + ',"Lost",' + pipeValue + ')');
  sheet.getRange('E4').setFormula('=SUMIF(' + pipeStage + ',"<>Won",' + pipeWeighted + ')-SUMIF(' + pipeStage + ',"Lost",' + pipeWeighted + ')');
  sheet.getRange('E5').setFormula('=IFERROR(E3/' + REVENUE_TARGET + ',0)').setNumberFormat('0.0"x"');
  sheet.getRange('E6').setFormula('=SUM(' + revCollected + ')');
  sheet.getRange('E7').setFormula('=SUM(' + revOutstanding + ')');
  sheet.getRange('E8').setFormula('=IFERROR(COUNTIF(' + pipeStage + ',"Won")/(COUNTIF(' + pipeStage + ',"Won")+COUNTIF(' + pipeStage + ',"Lost")),0)').setNumberFormat('0%');
  sheet.getRange('E9').setFormula('=COUNTIF(' + pipeStage + ',"Won")');
  sheet.getRange('E10').setFormula('=IFERROR(COUNTIF(' + taskStatus + ',"Completed")/COUNTA(' + taskStatus + '),0)').setNumberFormat('0%');

  Object.keys({ B3: 1, B4: 1, B6: 1, B7: 1, B8: 1, B9: 1, B10: 1, E3: 1, E4: 1, E6: 1, E7: 1, E9: 1 }).forEach(function (a) {
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
  var revCollDate = rangeRef_(SHEETS.REVENUE, 'collectionDate');
  var revCollAmt = rangeRef_(SHEETS.REVENUE, 'amountCollected');
  var revSignDate = rangeRef_(SHEETS.REVENUE, 'contractSigningDate');
  var revContractValue = rangeRef_(SHEETS.REVENUE, 'contractValue');

  var currentWeekId = '=INDEX(' + weekIdCol + ',MATCH(1,(TODAY()>=' + weekStart + ')*(TODAY()<=' + weekEnd + '),0))';
  sheet.getRange('B3').setFormula(currentWeekId);
  sheet.getRange('B4').setFormula('=IFERROR(INDEX(' + weekSales + ',MATCH($B$3,' + weekIdCol + ',0)),0)').setNumberFormat('#,##0 "EGP"');
  sheet.getRange('B5').setFormula('=SUMIFS(' + revCollAmt + ',' + revCollDate + ',">="&INDEX(' + weekStart + ',MATCH($B$3,' + weekIdCol + ',0)),' + revCollDate + ',"<="&INDEX(' + weekEnd + ',MATCH($B$3,' + weekIdCol + ',0)))').setNumberFormat('#,##0 "EGP"');
  sheet.getRange('B6').setFormula('=COUNTIFS(' + taskWeekId + ',$B$3,' + taskPriority + ',"Critical")');
  sheet.getRange('B7').setFormula('=COUNTIFS(' + taskWeekId + ',$B$3,' + taskStatus + ',"Blocked")');
  sheet.getRange('B8').setFormula('=COUNTIFS(' + taskWeekId + ',$B$3,' + taskLight + ',"RED")');
  sheet.getRange('B9').setFormula('=IFERROR(INDEX(' + weekBudget + ',MATCH($B$3,' + weekIdCol + ',0)),0)').setNumberFormat('#,##0 "EGP"');

  sheet.getRange('D3').setFormula('=COUNTIFS(' + taskWeekId + ',$B$3)');
  sheet.getRange('D4').setFormula('=COUNTIFS(' + taskWeekId + ',$B$3,' + taskStatus + ',"Completed")');
  sheet.getRange('D5').setFormula('=IFERROR(D4/D3,0)').setNumberFormat('0%');
  sheet.getRange('D6').setFormula('=COUNTIFS(' + taskWeekId + ',$B$3,' + taskStatus + ',"<>Completed",' + taskDue + ',"<"&TODAY())');
  sheet.getRange('D7').setFormula('=SUMIFS(' + expActual + ',' + expDate + ',">="&INDEX(' + weekStart + ',MATCH($B$3,' + weekIdCol + ',0)),' + expDate + ',"<="&INDEX(' + weekEnd + ',MATCH($B$3,' + weekIdCol + ',0)))').setNumberFormat('#,##0 "EGP"');
  sheet.getRange('D8').setFormula('=B5');
  sheet.getRange('D9').setFormula('=SUMIFS(' + revContractValue + ',' + revSignDate + ',">="&INDEX(' + weekStart + ',MATCH($B$3,' + weekIdCol + ',0)),' + revSignDate + ',"<="&INDEX(' + weekEnd + ',MATCH($B$3,' + weekIdCol + ',0)))').setNumberFormat('#,##0 "EGP"');
}
