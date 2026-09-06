/**
 * Creates every tab defined in SHEET_ORDER, writes its header row, freezes it,
 * and applies basic formatting (bold header, filter, column widths).
 * Safe to re-run: it will not wipe existing data rows, only rewrite headers/formatting.
 */
function runSetupSheets() {
  var spreadsheet = ss_();

  SHEET_ORDER.forEach(function (name) {
    var sheet = getOrCreateSheet(name);
    var headers = getHeaders(name);
    if (headers.length > 0) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      sheet.setFrozenRows(1);
      var headerRange = sheet.getRange(1, 1, 1, headers.length);
      headerRange.setFontWeight('bold')
        .setBackground('#1a2b4c')
        .setFontColor('#ffffff')
        .setVerticalAlignment('middle');
      sheet.setRowHeight(1, 32);
      if (sheet.getFilter()) sheet.getFilter().remove();
      if (sheet.getLastRow() >= 1 && sheet.getLastColumn() >= 1) {
        sheet.getRange(1, 1, Math.max(sheet.getLastRow(), 1), headers.length).createFilter();
      }
      for (var c = 1; c <= headers.length; c++) sheet.autoResizeColumn(c);
      sheet.setTabColor(null);
    }
  });

  buildSettingsSheet_();
  buildMasterDataSheet_();
  buildCeoDashboardSheetShell_();
  buildWeeklyCeoSheetShell_();

  // Reorder tabs to match SHEET_ORDER exactly.
  SHEET_ORDER.forEach(function (name, index) {
    var sheet = spreadsheet.getSheetByName(name);
    if (sheet) spreadsheet.setActiveSheet(sheet), spreadsheet.moveActiveSheet(index + 1);
  });
  spreadsheet.setActiveSheet(spreadsheet.getSheetByName(SHEETS.CEO_DASHBOARD));

  SpreadsheetApp.flush();
  return 'Sheet structure created: ' + SHEET_ORDER.length + ' tabs.';
}

function buildSettingsSheet_() {
  var sheet = getOrCreateSheet(SHEETS.SETTINGS);
  sheet.clear();
  var rows = [
    ['Setting', 'Value', 'Notes'],
    ['Company Name', 'Eureka Healthcare Development Experts', ''],
    ['Fiscal Year', FISCAL_YEAR, ''],
    ['Positioning', 'Strategy. Transformation. Operational Excellence.', ''],
    ['Revenue — Minimum', REVENUE_MIN, 'EGP'],
    ['Revenue — Operating Target', REVENUE_TARGET, 'EGP'],
    ['Revenue — Stretch', REVENUE_STRETCH, 'EGP'],
    ['Annual Sales Bookings Target', ANNUAL_BOOKINGS_TARGET, 'EGP'],
    ['Minimum Qualified Pipeline', PIPELINE_MIN, 'EGP'],
    ['Maximum Qualified Pipeline', PIPELINE_MAX, 'EGP'],
    ['Pipeline Coverage Target (x Revenue)', PIPELINE_COVERAGE_TARGET, ''],
    ['Pipeline Coverage Alert Floor (x Revenue)', PIPELINE_COVERAGE_ALERT_FLOOR, 'Below this = RED ALERT'],
    ['Revenue Achievement Alert Floor', ALERT_REVENUE_ACHIEVEMENT_FLOOR, '% of target, below = RED ALERT'],
    ['Receivable Overdue Alert (days)', ALERT_RECEIVABLE_OVERDUE_DAYS, ''],
    ['Inactive Opportunity Alert (days)', ALERT_INACTIVE_OPPORTUNITY_DAYS, ''],
    ['Web App URL', '', 'Paste after first deployment'],
    ['Last Setup Run', new Date(), '']
  ];
  sheet.getRange(1, 1, rows.length, 3).setValues(rows);
  sheet.getRange(1, 1, 1, 3).setFontWeight('bold').setBackground('#1a2b4c').setFontColor('#ffffff');
  sheet.setFrozenRows(1);
  sheet.setColumnWidth(1, 260);
  sheet.setColumnWidth(2, 220);
  sheet.setColumnWidth(3, 320);
}

/** 26_Master_Data holds every dropdown list as its own column, used both by Apps Script and by sheet-native data validation. */
function buildMasterDataSheet_() {
  var sheet = getOrCreateSheet(SHEETS.MASTER_DATA);
  sheet.clear();
  var lists = getMasterLists_();
  var maxLen = 0;
  var keys = Object.keys(lists);
  keys.forEach(function (k) { maxLen = Math.max(maxLen, lists[k].length); });
  var header = keys;
  var grid = [header];
  for (var r = 0; r < maxLen; r++) {
    var row = keys.map(function (k) { return lists[k][r] !== undefined ? lists[k][r] : ''; });
    grid.push(row);
  }
  sheet.getRange(1, 1, grid.length, header.length).setValues(grid);
  sheet.getRange(1, 1, 1, header.length).setFontWeight('bold').setBackground('#1a2b4c').setFontColor('#ffffff');
  sheet.setFrozenRows(1);
  for (var c = 1; c <= header.length; c++) sheet.autoResizeColumn(c);
}

function getMasterLists_() {
  return {
    TASK_STATUS: TASK_STATUS,
    TASK_PRIORITY: TASK_PRIORITY,
    TASK_CATEGORIES: TASK_CATEGORIES,
    EXPENSE_CATEGORIES: EXPENSE_CATEGORIES,
    PAYMENT_STATUS: PAYMENT_STATUS,
    PAYMENT_METHODS: PAYMENT_METHODS,
    COLLECTION_STATUS: COLLECTION_STATUS,
    SALES_STAGES: SALES_STAGES.map(function (s) { return s.name; }),
    CAMPAIGN_TYPES: CAMPAIGN_TYPES,
    EVENT_TYPES: EVENT_TYPES,
    ACCOUNT_TIERS: ACCOUNT_TIERS,
    RISK_CATEGORIES: RISK_CATEGORIES,
    RISK_STATUS: RISK_STATUS,
    DECISION_STATUS: DECISION_STATUS,
    COUNTRIES: COUNTRIES,
    KPI_CATEGORIES: ['Financial', 'Commercial', 'Marketing', 'Delivery', 'Strategic']
  };
}

/** Dashboard sheet is mostly a live-formula "at a glance" surface for anyone opening the raw Sheet directly. */
function buildCeoDashboardSheetShell_() {
  var sheet = getOrCreateSheet(SHEETS.CEO_DASHBOARD);
  sheet.clear();
  sheet.getRange('A1').setValue('EUREKA 2027 — CEO DASHBOARD (open the web app for the full interactive experience)')
    .setFontWeight('bold').setFontSize(14);
  sheet.getRange('A1:F1').merge();
  sheet.setColumnWidths(1, 6, 200);
  sheet.setFrozenRows(3);
  var labels = [
    ['', '', '', '', '', ''],
    ['Metric', 'Value', '', 'Metric', 'Value', ''],
    ['2027 Revenue Target', '', '', 'Total Pipeline', '', ''],
    ['Revenue Actual (Recognized)', '', '', 'Weighted Pipeline', '', ''],
    ['Revenue Achievement %', '', '', 'Pipeline Coverage (x)', '', ''],
    ['Annual Bookings Target', '', '', 'Cash Collected', '', ''],
    ['Bookings Actual', '', '', 'Outstanding Receivables', '', ''],
    ['Growth Budget', '', '', 'Win Rate', '', ''],
    ['Actual Growth Spend', '', '', 'Deals Won (YTD)', '', ''],
    ['Budget Variance', '', '', 'Tasks Completion %', '', '']
  ];
  sheet.getRange(2, 1, labels.length, 6).setValues(labels);
  sheet.getRange(3, 1, 1, 6).setFontWeight('bold'); // header row ("Metric / Value ...", row 3 — row 2 above it is a blank spacer)
  sheet.getRange(4, 1, 8, 1).setFontWeight('bold'); // left-hand metric labels, rows 4-11
  sheet.getRange(4, 4, 8, 1).setFontWeight('bold'); // right-hand metric labels, rows 4-11
  sheet.getRange('A13').setValue('This sheet is refreshed by Eureka 2027 menu → "Refresh dashboard formulas". Live drill-down, charts and weekly review are in the web app.').setFontStyle('italic');
}

function buildWeeklyCeoSheetShell_() {
  var sheet = getOrCreateSheet(SHEETS.WEEKLY_CEO);
  sheet.clear();
  sheet.getRange('A1').setValue('WEEKLY CEO REVIEW (current week, auto-detected from today\'s date)')
    .setFontWeight('bold').setFontSize(14);
  sheet.getRange('A1:D1').merge();
  var labels = [
    ['', '', '', ''],
    ['This Week Metric', 'Value', 'End of Week Metric', 'Value'],
    ['Current Week ID', '', 'Tasks Planned', ''],
    ['Sales Target', '', 'Tasks Completed', ''],
    ['Expected Collections', '', 'Completion %', ''],
    ['Critical Tasks', '', 'Tasks Overdue', ''],
    ['Blocked Tasks', '', 'Spend This Week', ''],
    ['Overdue Tasks', '', 'Revenue Collected', ''],
    ['Budget Planned This Week', '', 'Bookings', '']
  ];
  sheet.getRange(2, 1, labels.length, 4).setValues(labels);
  sheet.getRange(3, 1, 1, 4).setFontWeight('bold'); // header row (row 3 — row 2 above it is a blank spacer)
  sheet.getRange(4, 1, 7, 1).setFontWeight('bold'); // "This Week" labels, rows 4-10
  sheet.getRange(4, 3, 7, 1).setFontWeight('bold'); // "End of Week" labels, rows 4-10
  sheet.setColumnWidths(1, 4, 220);
}
