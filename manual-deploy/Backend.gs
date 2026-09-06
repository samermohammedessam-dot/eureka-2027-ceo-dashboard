
// ============================================================
// SOURCE: data/SheetService.gs
// ============================================================

/**
 * Generic data-access layer. Every other module reads/writes sheets exclusively through
 * these functions so batching, caching, and header-mapping logic lives in one place.
 */

function ss_() {
  return SpreadsheetApp.getActiveSpreadsheet();
}

function getOrCreateSheet(name) {
  var sheet = ss_().getSheetByName(name);
  if (!sheet) sheet = ss_().insertSheet(name);
  return sheet;
}

/**
 * Reads all data rows of a sheet as an array of plain objects keyed by schema `key`.
 * Empty trailing rows are skipped. Adds `_row` (1-based sheet row number) to every object
 * so callers can write updates back without re-scanning.
 */
function readAllRecords(sheetName) {
  var sheet = ss_().getSheetByName(sheetName);
  if (!sheet || sheet.getLastRow() < 2) return [];
  var schema = getSchema(sheetName);
  var numCols = schema.length;
  var values = sheet.getRange(2, 1, sheet.getLastRow() - 1, numCols).getValues();
  var records = [];
  for (var r = 0; r < values.length; r++) {
    var row = values[r];
    if (row.join('') === '') continue; // fully blank row
    var obj = { _row: r + 2 };
    for (var c = 0; c < schema.length; c++) {
      obj[schema[c].key] = row[c];
    }
    records.push(obj);
  }
  return records;
}

/** Cached read for dashboard-style aggregations. TTL defined in Constants.gs. */
function readAllRecordsCached(sheetName) {
  var cache = CacheService.getScriptCache();
  var cacheKey = 'records_' + sheetName;
  var cached = cache.get(cacheKey);
  if (cached) {
    try { return JSON.parse(cached); } catch (e) { /* fall through to fresh read */ }
  }
  var records = readAllRecords(sheetName);
  try {
    cache.put(cacheKey, JSON.stringify(records), CACHE_TTL_SECONDS);
  } catch (e) {
    // Payload too large for cache (>100KB) — silently skip caching, still return fresh data.
  }
  return records;
}

function invalidateCache(sheetName) {
  CacheService.getScriptCache().remove('records_' + sheetName);
}

/** Appends one record (plain object keyed by schema `key`). Returns the generated ID if the schema has an idPrefix column. */
function appendRecord(sheetName, record) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheet = getOrCreateSheet(sheetName);
    var schema = getSchema(sheetName);
    var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
    if (idCol && !record[idCol.key]) {
      record[idCol.key] = generateId(sheetName, idCol.idPrefix);
    }
    var row = schema.map(function (c) {
      return (record[c.key] === undefined || record[c.key] === null) ? '' : record[c.key];
    });
    sheet.appendRow(row);
    invalidateCache(sheetName);
    return record[idCol ? idCol.key : null] || sheet.getLastRow();
  } finally {
    lock.releaseLock();
  }
}

/** Updates a record identified by its ID column value. Only keys present in `patch` are overwritten. */
function updateRecordById(sheetName, idValue, patch) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheet = ss_().getSheetByName(sheetName);
    if (!sheet) return false;
    var schema = getSchema(sheetName);
    var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
    if (!idCol) return false;
    var idColIndex = schema.indexOf(idCol);
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return false;
    var ids = sheet.getRange(2, idColIndex + 1, lastRow - 1, 1).getValues();
    for (var r = 0; r < ids.length; r++) {
      if (String(ids[r][0]) === String(idValue)) {
        var rowNum = r + 2;
        var existing = {};
        var rowValues = sheet.getRange(rowNum, 1, 1, schema.length).getValues()[0];
        schema.forEach(function (c, i) { existing[c.key] = rowValues[i]; });
        var merged = existing;
        for (var k in patch) merged[k] = patch[k];
        var newRow = schema.map(function (c) {
          return (merged[c.key] === undefined || merged[c.key] === null) ? '' : merged[c.key];
        });
        sheet.getRange(rowNum, 1, 1, schema.length).setValues([newRow]);
        invalidateCache(sheetName);
        return true;
      }
    }
    return false;
  } finally {
    lock.releaseLock();
  }
}

/** Deletes a record identified by its ID column value. */
function deleteRecordById(sheetName, idValue) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheet = ss_().getSheetByName(sheetName);
    if (!sheet) return false;
    var schema = getSchema(sheetName);
    var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
    if (!idCol) return false;
    var idColIndex = schema.indexOf(idCol);
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return false;
    var ids = sheet.getRange(2, idColIndex + 1, lastRow - 1, 1).getValues();
    for (var r = 0; r < ids.length; r++) {
      if (String(ids[r][0]) === String(idValue)) {
        sheet.deleteRow(r + 2);
        invalidateCache(sheetName);
        return true;
      }
    }
    return false;
  } finally {
    lock.releaseLock();
  }
}

/**
 * Bulk-appends many records in a single write (used by seeders — far fewer API calls than
 * looping appendRecord). IDs for records that don't already have one are assigned
 * sequentially in memory, starting from one scan of the sheet's current max ID — calling
 * generateId() once per record here would have every record in the batch see the same
 * (not-yet-updated) sheet and come back with the same "next" ID.
 */
function bulkAppendRecords(sheetName, records) {
  if (!records || records.length === 0) return;
  var sheet = getOrCreateSheet(sheetName);
  var schema = getSchema(sheetName);
  var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
  var nextIdNum = idCol ? nextIdSequenceStart_(sheetName, idCol.idPrefix) : null;
  var rows = records.map(function (record) {
    if (idCol && !record[idCol.key]) {
      record[idCol.key] = idCol.idPrefix + '-' + padId_(nextIdNum);
      nextIdNum++;
    }
    return schema.map(function (c) {
      return (record[c.key] === undefined || record[c.key] === null) ? '' : record[c.key];
    });
  });
  sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, schema.length).setValues(rows);
  invalidateCache(sheetName);
}

function sumBy(records, valueKey, predicate) {
  var total = 0;
  for (var i = 0; i < records.length; i++) {
    if (!predicate || predicate(records[i])) {
      var v = Number(records[i][valueKey]);
      if (!isNaN(v)) total += v;
    }
  }
  return total;
}

function countBy(records, predicate) {
  var n = 0;
  for (var i = 0; i < records.length; i++) if (!predicate || predicate(records[i])) n++;
  return n;
}

// ============================================================
// SOURCE: data/IdGenerator.gs
// ============================================================

/**
 * Sequential, human-readable ID generation (e.g. TSK-0001, REV-0037).
 * Scans the existing ID column once per call — fine at this data volume (hundreds to a few
 * thousand rows per sheet) and keeps IDs short and sortable, unlike UUIDs.
 *
 * IMPORTANT: this scans the SHEET as it currently stands. A caller that needs several new
 * IDs in a row (see bulkAppendRecords in SheetService.gs) must NOT call this once per record
 * before anything has been written — every call would see the same unchanged sheet and
 * return the same "next" ID. Use nextIdSequenceStart_() once, then increment in memory,
 * for that case instead.
 */
function generateId(sheetName, prefix) {
  return prefix + '-' + padId_(nextIdSequenceStart_(sheetName, prefix));
}

/** Returns the next free sequence number (not yet formatted/prefixed) for a sheet's ID column. */
function nextIdSequenceStart_(sheetName, prefix) {
  var sheet = ss_().getSheetByName(sheetName);
  var schema = getSchema(sheetName);
  var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
  var max = 0;
  if (sheet && idCol) {
    var idColIndex = schema.indexOf(idCol);
    var lastRow = sheet.getLastRow();
    if (lastRow >= 2) {
      var ids = sheet.getRange(2, idColIndex + 1, lastRow - 1, 1).getValues();
      for (var i = 0; i < ids.length; i++) {
        var m = String(ids[i][0]).match(new RegExp('^' + prefix + '-(\\d+)$'));
        if (m) max = Math.max(max, parseInt(m[1], 10));
      }
    }
  }
  return max + 1;
}

function padId_(n) {
  return ('0000' + n).slice(-4);
}

// ============================================================
// SOURCE: api/Compute.gs
// ============================================================

/**
 * Calculated-field engine. Every "computed:true" column in SHEET_SCHEMA is written here,
 * never typed by a user. Run via the menu ("Recompute calculated fields") or automatically
 * after any CRUD write from the web app (see ApiHelpers.gs).
 */
function recomputeAllCalculatedFields() {
  recomputeTasks_();
  recomputeRevenue_();
  recomputeExpenses_();
  recomputePipeline_();
  recomputeCampaigns_();
  recomputeEvents_();
  recomputeAcademy_();
  recomputeRisks_();
  SpreadsheetApp.flush();
  return 'Calculated fields refreshed.';
}

function writeColumnValues_(sheetName, key, valuesByRow) {
  var schema = getSchema(sheetName);
  var colIndex = schema.map(function (c) { return c.key; }).indexOf(key);
  if (colIndex === -1) return;
  var sheet = ss_().getSheetByName(sheetName);
  var rows = Object.keys(valuesByRow);
  rows.forEach(function (rowNum) {
    sheet.getRange(Number(rowNum), colIndex + 1).setValue(valuesByRow[rowNum]);
  });
}

function todayMidnight_() {
  var d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}

function daysBetween_(a, b) {
  if (!a || !b) return '';
  var da = new Date(a), db = new Date(b);
  return Math.round((db - da) / 86400000);
}

var MONTH_NAMES_ = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

/**
 * Derives a calendar month name straight from the Date object's own local fields
 * (getMonth()) rather than Utilities.formatDate(date, 'GMT', 'MMMM'). The old GMT-based
 * version reinterpreted a date built in the script's timeZone (Africa/Cairo, UTC+2) as if
 * it were UTC, which shifts local midnight back onto the previous calendar day — silently
 * correct for most dates, but wrong for any date that falls on the 1st of a month, which
 * gets misread as the last day of the PREVIOUS month (e.g. Jan 1 read as "December").
 */
function monthNameOf_(date) {
  if (!date) return '';
  return MONTH_NAMES_[new Date(date).getMonth()];
}
var MONTH_TO_QUARTER_ = { January: 'Q1', February: 'Q1', March: 'Q1', April: 'Q2', May: 'Q2', June: 'Q2', July: 'Q3', August: 'Q3', September: 'Q3', October: 'Q4', November: 'Q4', December: 'Q4' };

function recomputeTasks_() {
  var records = readAllRecords(SHEETS.TASKS);
  var today = todayMidnight_();
  var patch = {};
  records.forEach(function (t) {
    var light;
    if (t.status === 'Completed') {
      light = TRAFFIC_LIGHT.GREEN;
    } else if (t.status === 'Cancelled') {
      light = TRAFFIC_LIGHT.GREEN;
    } else if (t.status === 'Blocked' || (t.dueDate && new Date(t.dueDate) < today)) {
      light = TRAFFIC_LIGHT.RED;
    } else if (t.dueDate && daysBetween_(today, t.dueDate) <= 3) {
      light = TRAFFIC_LIGHT.YELLOW;
    } else {
      light = TRAFFIC_LIGHT.GREEN;
    }
    patch[t._row] = light;
  });
  writeColumnValues_(SHEETS.TASKS, 'trafficLight', patch);
}

function recomputeRevenue_() {
  var records = readAllRecords(SHEETS.REVENUE);
  var outstanding = {}, days = {}, month = {}, quarter = {};
  var today = todayMidnight_();
  records.forEach(function (r) {
    var invoice = Number(r.invoiceAmount) || 0;
    var collected = Number(r.amountCollected) || 0;
    outstanding[r._row] = Math.max(invoice - collected, 0);
    days[r._row] = (outstanding[r._row] > 0 && r.dueDate) ? Math.max(daysBetween_(r.dueDate, today), 0) : 0;
    var mn = monthNameOf_(r.invoiceDate || r.contractSigningDate);
    month[r._row] = mn;
    quarter[r._row] = MONTH_TO_QUARTER_[mn] || '';
  });
  writeColumnValues_(SHEETS.REVENUE, 'outstanding', outstanding);
  writeColumnValues_(SHEETS.REVENUE, 'daysOutstanding', days);
  writeColumnValues_(SHEETS.REVENUE, 'month', month);
  writeColumnValues_(SHEETS.REVENUE, 'quarter', quarter);
}

function recomputeExpenses_() {
  var records = readAllRecords(SHEETS.EXPENSES);
  var variance = {}, week = {}, month = {}, quarter = {};
  var weeks = readAllRecords(SHEETS.WEEKLY_EXECUTION);
  records.forEach(function (e) {
    variance[e._row] = (Number(e.budgetedAmount) || 0) - (Number(e.actualAmount) || 0);
    var mn = monthNameOf_(e.date);
    month[e._row] = mn;
    quarter[e._row] = MONTH_TO_QUARTER_[mn] || '';
    week[e._row] = findWeekIdForDate_(e.date, weeks);
  });
  writeColumnValues_(SHEETS.EXPENSES, 'variance', variance);
  writeColumnValues_(SHEETS.EXPENSES, 'week', week);
  writeColumnValues_(SHEETS.EXPENSES, 'month', month);
  writeColumnValues_(SHEETS.EXPENSES, 'quarter', quarter);
}

function findWeekIdForDate_(date, weeks) {
  if (!date) return '';
  var d = new Date(date).getTime();
  for (var i = 0; i < weeks.length; i++) {
    if (d >= new Date(weeks[i].startDate).getTime() && d <= new Date(weeks[i].endDate).getTime()) return weeks[i].weekId;
  }
  return '';
}

function stageProbability_(stageName) {
  var s = SALES_STAGES.filter(function (x) { return x.name === stageName; })[0];
  return s ? s.probability : 0;
}

function recomputePipeline_() {
  var records = readAllRecords(SHEETS.PIPELINE);
  var prob = {}, weighted = {};
  records.forEach(function (o) {
    var p = stageProbability_(o.stage);
    prob[o._row] = p;
    weighted[o._row] = Math.round((Number(o.estimatedOpportunityValue) || 0) * p);
  });
  writeColumnValues_(SHEETS.PIPELINE, 'probabilityPct', prob);
  writeColumnValues_(SHEETS.PIPELINE, 'weightedValue', weighted);
}

function recomputeCampaigns_() {
  var records = readAllRecords(SHEETS.CAMPAIGNS);
  var cpl = {}, cpql = {}, roi = {};
  records.forEach(function (c) {
    var spend = Number(c.actualSpend) || 0;
    cpl[c._row] = c.leads ? Math.round(spend / Number(c.leads)) : 0;
    cpql[c._row] = c.qualifiedLeads ? Math.round(spend / Number(c.qualifiedLeads)) : 0;
    roi[c._row] = spend > 0 ? Math.round(((Number(c.revenueInfluenced) || 0) - spend) / spend * 100) / 100 : 0;
  });
  writeColumnValues_(SHEETS.CAMPAIGNS, 'costPerLead', cpl);
  writeColumnValues_(SHEETS.CAMPAIGNS, 'costPerQualifiedLead', cpql);
  writeColumnValues_(SHEETS.CAMPAIGNS, 'roi', roi);
}

function recomputeEvents_() {
  var records = readAllRecords(SHEETS.EVENTS);
  var roi = {};
  records.forEach(function (ev) {
    var cost = Number(ev.actualCost) || 0;
    roi[ev._row] = cost > 0 ? Math.round(((Number(ev.revenueGenerated) || 0) - cost) / cost * 100) / 100 : 0;
  });
  writeColumnValues_(SHEETS.EVENTS, 'eventROI', roi);
}

function recomputeAcademy_() {
  var records = readAllRecords(SHEETS.ACADEMY);
  var margin = {};
  records.forEach(function (a) {
    margin[a._row] = (Number(a.revenue) || 0) - (Number(a.cost) || 0);
  });
  writeColumnValues_(SHEETS.ACADEMY, 'margin', margin);
}

function recomputeRisks_() {
  var records = readAllRecords(SHEETS.RISKS);
  var score = {};
  records.forEach(function (r) {
    score[r._row] = (Number(r.probability) || 0) * (Number(r.impact) || 0);
  });
  writeColumnValues_(SHEETS.RISKS, 'riskScore', score);
}

// ============================================================
// SOURCE: api/RefreshDashboardSheet.gs
// ============================================================

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

// ============================================================
// SOURCE: api/ApiHelpers.gs
// ============================================================

/**
 * Shared helpers for the client-facing API layer (functions called via google.script.run).
 * Every function the frontend can call is prefixed `api_` by convention so it's obvious
 * from the file which functions form the public contract with the frontend (src/ui/*.html,
 * or JavaScript.html in the manual-deploy copy).
 */

// Sheets the generic CRUD API is allowed to touch. Whitelisted deliberately — the frontend
// passes a sheet name as a string, so this stops any arbitrary sheet from being written to.
// Built lazily (not a top-level array literal) so it never depends on file load order —
// safe even if this file's code is pasted/merged ahead of the file that defines SHEETS.
function genericCrudSheets_() {
  return [
    SHEETS.TARGET_ACCOUNTS, SHEETS.PARTNERSHIPS, SHEETS.ACADEMY, SHEETS.CASE_STUDIES,
    SHEETS.DIGITAL_ROADMAP, SHEETS.DECISIONS, SHEETS.RISKS, SHEETS.PROJECTS, SHEETS.CLIENTS,
    SHEETS.TEAM, SHEETS.MARKETS, SHEETS.BUSINESS_UNITS
  ];
}

function assertGenericSheetAllowed_(sheetName) {
  if (genericCrudSheets_().indexOf(sheetName) === -1) {
    throw new Error('Sheet not permitted for generic CRUD: ' + sheetName);
  }
}

function stripRowMeta_(record) {
  var clean = {};
  for (var k in record) if (k !== '_row') clean[k] = record[k];
  return clean;
}

function applyFilters_(records, filters) {
  if (!filters) return records;
  return records.filter(function (r) {
    for (var key in filters) {
      var val = filters[key];
      if (val === undefined || val === null || val === '') continue;
      if (key === '_search') continue;
      if (String(r[key]) !== String(val)) return false;
    }
    if (filters._search) {
      var needle = String(filters._search).toLowerCase();
      var hay = JSON.stringify(r).toLowerCase();
      if (hay.indexOf(needle) === -1) return false;
    }
    return true;
  });
}

function safeCall_(fn) {
  try {
    return { ok: true, data: fn() };
  } catch (err) {
    Logger.log('API error: ' + err + '\n' + (err && err.stack));
    return { ok: false, error: String(err && err.message || err) };
  }
}

// ============================================================
// SOURCE: api/GenericCrudApi.gs
// ============================================================

/**
 * Generic CRUD endpoints for the "reference/tracker" sheets that don't need bespoke
 * calculated fields: Target Accounts, Partnerships, Academy, Case Studies, Digital Roadmap,
 * Decisions, Risks, Projects, Clients, Team, Markets, Business Units.
 */
function api_getGenericRecords(sheetName, filters) {
  return safeCall_(function () {
    assertGenericSheetAllowed_(sheetName);
    var records = readAllRecords(sheetName).map(stripRowMeta_);
    return applyFilters_(records, filters);
  });
}

function api_saveGenericRecord(sheetName, record) {
  return safeCall_(function () {
    assertGenericSheetAllowed_(sheetName);
    var schema = getSchema(sheetName);
    var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
    var idKey = idCol ? idCol.key : null;
    if (idKey && record[idKey]) {
      updateRecordById(sheetName, record[idKey], record);
      recomputeAllCalculatedFields();
      return record[idKey];
    }
    var newId = appendRecord(sheetName, record);
    recomputeAllCalculatedFields();
    return newId;
  });
}

function api_deleteGenericRecord(sheetName, idValue) {
  return safeCall_(function () {
    assertGenericSheetAllowed_(sheetName);
    return deleteRecordById(sheetName, idValue);
  });
}

// ============================================================
// SOURCE: api/TasksApi.gs
// ============================================================

function api_getTasks(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.TASKS).map(stripRowMeta_), filters);
  });
}

function api_saveTask(task) {
  return safeCall_(function () {
    if (task.taskId) {
      updateRecordById(SHEETS.TASKS, task.taskId, task);
    } else {
      task.status = task.status || 'Not Started';
      task.percentCompletion = task.percentCompletion || 0;
      appendRecord(SHEETS.TASKS, task);
    }
    recomputeTasks_();
    return task.taskId || true;
  });
}

function api_deleteTask(taskId) {
  return safeCall_(function () { return deleteRecordById(SHEETS.TASKS, taskId); });
}

// ============================================================
// SOURCE: api/RevenueApi.gs
// ============================================================

function api_getRevenue(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.REVENUE).map(stripRowMeta_), filters);
  });
}

function api_saveRevenue(rec) {
  return safeCall_(function () {
    if (rec.revenueId) {
      updateRecordById(SHEETS.REVENUE, rec.revenueId, rec);
    } else {
      appendRecord(SHEETS.REVENUE, rec);
    }
    recomputeRevenue_();
    return rec.revenueId || true;
  });
}

function api_deleteRevenue(id) {
  return safeCall_(function () { return deleteRecordById(SHEETS.REVENUE, id); });
}

/** Section 10: outstanding, collection %, DSO, revenue vs targets — computed on demand for the Revenue view. */
function api_getRevenueSummary() {
  return safeCall_(function () {
    var records = readAllRecords(SHEETS.REVENUE);
    var invoiced = sumBy(records, 'invoiceAmount');
    var collected = sumBy(records, 'amountCollected');
    var outstanding = sumBy(records, 'outstanding');
    var recognized = sumBy(records, 'revenueRecognized');
    var bookings = sumBy(records, 'contractValue');
    var dso = computeDSO_(records);
    return {
      invoiced: invoiced, collected: collected, outstanding: outstanding, recognized: recognized,
      bookings: bookings, collectionPct: invoiced ? collected / invoiced : 0, dso: dso,
      revenueTarget: REVENUE_TARGET, bookingsTarget: ANNUAL_BOOKINGS_TARGET
    };
  });
}

function computeDSO_(records) {
  var withDays = records.filter(function (r) { return r.amountCollected > 0 && r.collectionDate && r.invoiceDate; });
  if (!withDays.length) return null;
  var totalDays = withDays.reduce(function (sum, r) { return sum + daysBetween_(r.invoiceDate, r.collectionDate); }, 0);
  return Math.round(totalDays / withDays.length);
}

// ============================================================
// SOURCE: api/ExpensesApi.gs
// ============================================================

function api_getExpenses(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.EXPENSES).map(stripRowMeta_), filters);
  });
}

function api_saveExpense(rec) {
  return safeCall_(function () {
    if (rec.expenseId) {
      updateRecordById(SHEETS.EXPENSES, rec.expenseId, rec);
    } else {
      appendRecord(SHEETS.EXPENSES, rec);
    }
    recomputeExpenses_();
    return rec.expenseId || true;
  });
}

function api_deleteExpense(id) {
  return safeCall_(function () { return deleteRecordById(SHEETS.EXPENSES, id); });
}

function api_getExpenseSummary() {
  return safeCall_(function () {
    var records = readAllRecords(SHEETS.EXPENSES);
    var budgeted = sumBy(records, 'budgetedAmount');
    var actual = sumBy(records, 'actualAmount');
    var byMarket = groupSum_(records, 'market', 'actualAmount');
    var byMonth = groupSum_(records, 'month', 'actualAmount');
    var byCampaign = groupSum_(records, 'campaign', 'actualAmount');
    var byEvent = groupSum_(records, 'event', 'actualAmount');
    var byCategory = groupSum_(records, 'expenseCategory', 'actualAmount');
    return {
      budgeted: budgeted, actual: actual, variance: budgeted - actual,
      utilizationPct: budgeted ? actual / budgeted : 0,
      byMarket: byMarket, byMonth: byMonth, byCampaign: byCampaign, byEvent: byEvent, byCategory: byCategory,
      annualBudget: TOTAL_GROWTH_BUDGET_2027
    };
  });
}

function groupSum_(records, groupKey, valueKey) {
  var out = {};
  records.forEach(function (r) {
    var g = r[groupKey] || 'Unassigned';
    out[g] = (out[g] || 0) + (Number(r[valueKey]) || 0);
  });
  return out;
}

// ============================================================
// SOURCE: api/PipelineApi.gs
// ============================================================

function api_getPipeline(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.PIPELINE).map(stripRowMeta_), filters);
  });
}

function api_savePipeline(rec) {
  return safeCall_(function () {
    if (rec.opportunityId) {
      updateRecordById(SHEETS.PIPELINE, rec.opportunityId, rec);
    } else {
      rec.stage = rec.stage || 'Target Account';
      appendRecord(SHEETS.PIPELINE, rec);
    }
    recomputePipeline_();
    return rec.opportunityId || true;
  });
}

function api_deletePipeline(id) {
  return safeCall_(function () { return deleteRecordById(SHEETS.PIPELINE, id); });
}

/** Section 11: pipeline value, weighted pipeline, win rate, cycle, average deal, coverage, breakdowns. */
function api_getPipelineSummary() {
  return safeCall_(function () {
    var records = readAllRecords(SHEETS.PIPELINE);
    var open = records.filter(function (r) { return r.stage !== 'Won' && r.stage !== 'Lost'; });
    var won = records.filter(function (r) { return r.stage === 'Won'; });
    var lost = records.filter(function (r) { return r.stage === 'Lost'; });
    var totalPipeline = sumBy(open, 'estimatedOpportunityValue');
    var weightedPipeline = sumBy(open, 'weightedValue');
    var winRate = (won.length + lost.length) ? won.length / (won.length + lost.length) : 0;
    var avgDeal = won.length ? sumBy(won, 'estimatedOpportunityValue') / won.length : 0;
    var cycles = won.filter(function (r) { return r.firstContactDate; })
      .map(function (r) { return daysBetween_(r.firstContactDate, r.expectedCloseDate || r.lastContactDate); });
    var avgCycle = cycles.length ? Math.round(cycles.reduce(function (a, b) { return a + b; }, 0) / cycles.length) : null;
    return {
      totalPipeline: totalPipeline, weightedPipeline: weightedPipeline,
      coverage: REVENUE_TARGET ? totalPipeline / REVENUE_TARGET : 0,
      coverageTarget: PIPELINE_COVERAGE_TARGET, coverageAlertFloor: PIPELINE_COVERAGE_ALERT_FLOOR,
      winRate: winRate, avgDealSize: avgDeal, avgSalesCycleDays: avgCycle,
      byMarket: groupSum_(open, 'market', 'estimatedOpportunityValue'),
      byBusinessUnit: groupSum_(open, 'businessUnit', 'estimatedOpportunityValue'),
      byBdOwner: groupSum_(open, 'bdOwner', 'estimatedOpportunityValue'),
      byStage: groupSum_(open, 'stage', 'estimatedOpportunityValue'),
      wonCount: won.length, lostCount: lost.length
    };
  });
}

// ============================================================
// SOURCE: api/CampaignsApi.gs
// ============================================================

function api_getCampaigns(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.CAMPAIGNS).map(stripRowMeta_), filters);
  });
}

function api_saveCampaign(rec) {
  return safeCall_(function () {
    if (rec.campaignId) {
      updateRecordById(SHEETS.CAMPAIGNS, rec.campaignId, rec);
    } else {
      appendRecord(SHEETS.CAMPAIGNS, rec);
    }
    recomputeCampaigns_();
    return rec.campaignId || true;
  });
}

function api_deleteCampaign(id) {
  return safeCall_(function () { return deleteRecordById(SHEETS.CAMPAIGNS, id); });
}

// ============================================================
// SOURCE: api/EventsApi.gs
// ============================================================

function api_getEvents(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.EVENTS).map(stripRowMeta_), filters);
  });
}

function api_saveEvent(rec) {
  return safeCall_(function () {
    if (rec.eventId) {
      updateRecordById(SHEETS.EVENTS, rec.eventId, rec);
    } else {
      appendRecord(SHEETS.EVENTS, rec);
    }
    recomputeEvents_();
    return rec.eventId || true;
  });
}

function api_deleteEvent(id) {
  return safeCall_(function () { return deleteRecordById(SHEETS.EVENTS, id); });
}

// ============================================================
// SOURCE: api/MarketsApi.gs
// ============================================================

/** Market performance: target vs actual revenue, pipeline, spend — powers Markets view + heatmap. */
function api_getMarketsPerformance() {
  return safeCall_(function () {
    var markets = readAllRecords(SHEETS.MARKETS).map(stripRowMeta_);
    var revenue = readAllRecords(SHEETS.REVENUE);
    var pipeline = readAllRecords(SHEETS.PIPELINE).filter(function (r) { return r.stage !== 'Won' && r.stage !== 'Lost'; });
    var expenses = readAllRecords(SHEETS.EXPENSES);

    return markets.map(function (m) {
      var revenueActual = sumBy(revenue, 'revenueRecognized', function (r) { return r.market === m.market; });
      var bookings = sumBy(revenue, 'contractValue', function (r) { return r.market === m.market; });
      var pipelineValue = sumBy(pipeline, 'estimatedOpportunityValue', function (r) { return r.market === m.market; });
      var spend = sumBy(expenses, 'actualAmount', function (r) { return r.market === m.market; });
      var achievementPct = m.revenueTarget2027 ? revenueActual / m.revenueTarget2027 : null;
      return {
        market: m.market, country: m.country, revenueTarget: m.revenueTarget2027, revenueActual: revenueActual,
        achievementPct: achievementPct, bookings: bookings, pipelineValue: pipelineValue, spend: spend,
        owner: m.owner, status: m.status,
        health: achievementPct === null ? 'N/A' : (achievementPct >= ALERT_REVENUE_ACHIEVEMENT_FLOOR ? 'GREEN' : (achievementPct >= 0.5 ? 'YELLOW' : 'RED'))
      };
    });
  });
}

// ============================================================
// SOURCE: api/KpiApi.gs
// ============================================================

/** Joins the 12_KPIs master list with live-computed actuals where a computation is known. */
function api_getKpis() {
  return safeCall_(function () {
    var kpis = readAllRecords(SHEETS.KPIS).map(stripRowMeta_);
    var actuals = computeKpiActuals_();
    return kpis.map(function (k) {
      var actual = actuals[k.kpiName];
      return Object.assign({}, k, { actual: actual !== undefined ? actual : k.actual });
    });
  });
}

function computeKpiActuals_() {
  var revenue = readAllRecords(SHEETS.REVENUE);
  var expenses = readAllRecords(SHEETS.EXPENSES);
  var pipelineAll = readAllRecords(SHEETS.PIPELINE);
  var pipelineOpen = pipelineAll.filter(function (r) { return r.stage !== 'Won' && r.stage !== 'Lost'; });
  var won = pipelineAll.filter(function (r) { return r.stage === 'Won'; });
  var lost = pipelineAll.filter(function (r) { return r.stage === 'Lost'; });
  var tasks = readAllRecords(SHEETS.TASKS);
  var projects = readAllRecords(SHEETS.PROJECTS);
  var campaigns = readAllRecords(SHEETS.CAMPAIGNS);

  var revenueActual = sumBy(revenue, 'revenueRecognized');
  var bookings = sumBy(revenue, 'contractValue');
  var collected = sumBy(revenue, 'amountCollected');
  var outstanding = sumBy(revenue, 'outstanding');
  var spend = sumBy(expenses, 'actualAmount');
  var budgeted = sumBy(expenses, 'budgetedAmount');
  var totalPipeline = sumBy(pipelineOpen, 'estimatedOpportunityValue');
  var weightedPipeline = sumBy(pipelineOpen, 'weightedValue');

  var out = {};
  out['Revenue Target'] = REVENUE_TARGET;
  out['Revenue Actual'] = revenueActual;
  out['Sales Bookings'] = bookings;
  out['Cash Collected'] = collected;
  out['Outstanding Receivables'] = outstanding;
  out['Growth Spend'] = spend;
  out['Budget Variance'] = budgeted - spend;
  out['Total Pipeline'] = totalPipeline;
  out['Weighted Pipeline'] = weightedPipeline;
  out['Pipeline Coverage'] = REVENUE_TARGET ? round2_(totalPipeline / REVENUE_TARGET) + 'x' : '0x';
  out['New Leads'] = pipelineAll.length;
  out['Qualified Leads'] = countBy(pipelineAll, function (r) { return stageProbability_(r.stage) >= 0.30; });
  out['Meetings'] = countBy(pipelineAll, function (r) { return stageProbability_(r.stage) >= 0.20; });
  out['Diagnostics'] = countBy(pipelineAll, function (r) { return r.stage === 'Diagnostic / Assessment'; });
  out['Proposals'] = countBy(pipelineAll, function (r) { return stageProbability_(r.stage) >= 0.60; });
  out['Wins'] = won.length;
  out['Win Rate'] = (won.length + lost.length) ? round2_(won.length / (won.length + lost.length) * 100) + '%' : '0%';
  out['Average Contract Value'] = revenue.length ? Math.round(bookings / revenue.length) : 0;
  out['Campaign Qualified Leads'] = sumBy(campaigns, 'qualifiedLeads');
  out['Pipeline Influenced'] = sumBy(campaigns, 'pipelineInfluenced');
  out['Marketing Revenue Influenced'] = sumBy(campaigns, 'revenueInfluenced');
  out['Project Completion %'] = projects.length ? round2_(avgBy_(projects, 'percentComplete') * 100) + '%' : 'N/A';
  out['Client NPS'] = projects.length ? round2_(avgBy_(projects, 'nps')) : 'N/A';
  out['Consultant Utilization'] = projects.length ? round2_(avgBy_(projects, 'consultantUtilization') * 100) + '%' : 'N/A';
  out['Red Projects'] = countBy(projects, function (p) { return p.status === 'Red'; });
  out['Scope Creep Cases'] = countBy(projects, function (p) { return p.scopeCreep === true; });
  out['Revenue from Outside Alexandria'] = sumBy(revenue, 'revenueRecognized', function (r) { return r.market !== 'Alexandria (Existing Base)'; });
  out['International Revenue'] = sumBy(revenue, 'revenueRecognized', function (r) { return r.country !== 'Egypt'; });
  out['Markets Entered'] = countBy(readAllRecords(SHEETS.MARKETS), function (m) { return String(m.status).indexOf('Active') === 0; });
  out['Strategic Partnerships Signed'] = countBy(readAllRecords(SHEETS.PARTNERSHIPS), function (p) { return p.status === 'Active'; });
  out['Tasks Completion %'] = tasks.length ? round2_(countBy(tasks, function (t) { return t.status === 'Completed'; }) / tasks.length * 100) + '%' : '0%';
  return out;
}

function avgBy_(records, key) {
  var vals = records.map(function (r) { return Number(r[key]); }).filter(function (v) { return !isNaN(v); });
  if (!vals.length) return 0;
  return vals.reduce(function (a, b) { return a + b; }, 0) / vals.length;
}

function round2_(n) { return Math.round(n * 100) / 100; }

// ============================================================
// SOURCE: api/DashboardApi.gs
// ============================================================

/**
 * Section 15: the CEO homepage. One call returns every number and chart series the
 * dashboard needs so the client makes a single round trip.
 */
function api_getDashboard() {
  return safeCall_(function () {
    var revenue = readAllRecordsCached(SHEETS.REVENUE);
    var expenses = readAllRecordsCached(SHEETS.EXPENSES);
    var pipelineAll = readAllRecordsCached(SHEETS.PIPELINE);
    var pipelineOpen = pipelineAll.filter(function (r) { return r.stage !== 'Won' && r.stage !== 'Lost'; });
    var won = pipelineAll.filter(function (r) { return r.stage === 'Won'; });
    var lost = pipelineAll.filter(function (r) { return r.stage === 'Lost'; });
    var tasks = readAllRecordsCached(SHEETS.TASKS);
    var plan = readAllRecordsCached(SHEETS.MASTER_PLAN);
    var markets = readAllRecordsCached(SHEETS.MARKETS);
    var businessUnits = readAllRecordsCached(SHEETS.BUSINESS_UNITS);

    var revenueActual = sumBy(revenue, 'revenueRecognized');
    var bookingsActual = sumBy(revenue, 'contractValue');
    var collected = sumBy(revenue, 'amountCollected');
    var outstanding = sumBy(revenue, 'outstanding');
    var spend = sumBy(expenses, 'actualAmount');
    var budgeted = sumBy(expenses, 'budgetedAmount');
    var totalPipeline = sumBy(pipelineOpen, 'estimatedOpportunityValue');
    var weightedPipeline = sumBy(pipelineOpen, 'weightedValue');

    var monthOrder = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    var revenueByMonth = monthOrder.map(function (mn) {
      var planRow = plan.filter(function (p) { return p.month === mn; })[0];
      return {
        month: mn,
        revenueTarget: planRow ? planRow.revenueTarget : 0,
        revenueActual: sumBy(revenue, 'revenueRecognized', function (r) { return r.month === mn; }),
        bookingsTarget: planRow ? planRow.salesBookingsTarget : 0,
        bookingsActual: sumBy(revenue, 'contractValue', function (r) { return monthNameOf_(r.contractSigningDate) === mn; }),
        budget: planRow ? planRow.growthBudget : 0,
        actualSpend: sumBy(expenses, 'actualAmount', function (e) { return e.month === mn; })
      };
    });

    var uniqueMarkets = distinct_(revenue.map(function (r) { return r.market; }).filter(Boolean));
    var revenueByMarket = markets.map(function (m) {
      return { market: m.market, target: m.revenueTarget2027, actual: sumBy(revenue, 'revenueRecognized', function (r) { return r.market === m.market; }) };
    });

    var buNames = distinct_(businessUnits.map(function (b) { return b.businessUnit; }));
    var revenueByBusinessUnit = buNames.map(function (bu) {
      return { businessUnit: bu, actual: sumBy(revenue, 'revenueRecognized', function (r) { return r.businessUnit === bu; }) };
    });

    var pipelineByMarket = groupSum_(pipelineOpen, 'market', 'estimatedOpportunityValue');
    var pipelineByStage = SALES_STAGES.filter(function (s) { return s.name !== 'Won' && s.name !== 'Lost'; }).map(function (s) {
      return { stage: s.name, value: sumBy(pipelineOpen, 'estimatedOpportunityValue', function (r) { return r.stage === s.name; }) };
    });

    var collectionsByMonth = monthOrder.map(function (mn) {
      return { month: mn, collected: sumBy(revenue, 'amountCollected', function (r) { return monthNameOf_(r.collectionDate) === mn; }) };
    });

    return {
      targets: { min: REVENUE_MIN, target: REVENUE_TARGET, stretch: REVENUE_STRETCH },
      headline: {
        revenueTarget: REVENUE_TARGET, revenueActual: revenueActual,
        revenueAchievementPct: REVENUE_TARGET ? revenueActual / REVENUE_TARGET : 0,
        bookingsTarget: ANNUAL_BOOKINGS_TARGET, bookingsActual: bookingsActual,
        cashCollected: collected, outstandingReceivables: outstanding,
        growthBudget: TOTAL_GROWTH_BUDGET_2027, actualGrowthSpend: spend, budgetVariance: TOTAL_GROWTH_BUDGET_2027 - spend,
        totalPipeline: totalPipeline, weightedPipeline: weightedPipeline,
        pipelineCoverage: REVENUE_TARGET ? totalPipeline / REVENUE_TARGET : 0,
        winRate: (won.length + lost.length) ? won.length / (won.length + lost.length) : 0,
        dealsWon: won.length,
        tasksCompletionPct: tasks.length ? countBy(tasks, function (t) { return t.status === 'Completed'; }) / tasks.length : 0
      },
      charts: {
        revenueByMonth: revenueByMonth,
        revenueByMarket: revenueByMarket,
        revenueByBusinessUnit: revenueByBusinessUnit,
        pipelineByMarket: pipelineByMarket,
        pipelineByStage: pipelineByStage,
        collectionsByMonth: collectionsByMonth
      },
      alerts: computeAlerts_()
    };
  });
}

function distinct_(arr) {
  var seen = {};
  var out = [];
  arr.forEach(function (v) { if (!seen[v]) { seen[v] = true; out.push(v); } });
  return out;
}

// ============================================================
// SOURCE: api/AlertsApi.gs
// ============================================================

/**
 * Section 28: rule-based management alerts. Pure functions over the sheets — no ML, no
 * external AI — so alerts are deterministic, explainable, and free to run as often as needed.
 */
function api_getAlerts() {
  return safeCall_(computeAlerts_);
}

function computeAlerts_() {
  var alerts = [];
  var revenue = readAllRecords(SHEETS.REVENUE);
  var expenses = readAllRecords(SHEETS.EXPENSES);
  var pipelineAll = readAllRecords(SHEETS.PIPELINE);
  var pipelineOpen = pipelineAll.filter(function (r) { return r.stage !== 'Won' && r.stage !== 'Lost'; });
  var tasks = readAllRecords(SHEETS.TASKS);
  var projects = readAllRecords(SHEETS.PROJECTS);
  var campaigns = readAllRecords(SHEETS.CAMPAIGNS);
  var markets = readAllRecords(SHEETS.MARKETS);
  var quarters = readAllRecords(SHEETS.QUARTERLY_REVIEW);
  var today = todayMidnight_();

  var revenueActual = sumBy(revenue, 'revenueRecognized');
  if (REVENUE_TARGET && revenueActual / REVENUE_TARGET < ALERT_REVENUE_ACHIEVEMENT_FLOOR) {
    alerts.push(mkAlert_('RED', 'Revenue', 'Revenue achievement is ' + pct_(revenueActual / REVENUE_TARGET) + ', below the ' + pct_(ALERT_REVENUE_ACHIEVEMENT_FLOOR) + ' floor.'));
  }

  var totalPipeline = sumBy(pipelineOpen, 'estimatedOpportunityValue');
  var coverage = REVENUE_TARGET ? totalPipeline / REVENUE_TARGET : 0;
  if (coverage < PIPELINE_COVERAGE_ALERT_FLOOR) {
    alerts.push(mkAlert_('RED', 'Pipeline', 'Pipeline coverage is ' + coverage.toFixed(1) + 'x revenue target, below the ' + PIPELINE_COVERAGE_ALERT_FLOOR + 'x floor.'));
  }

  tasks.forEach(function (t) {
    if (t.priority === 'Critical' && t.status !== 'Completed' && t.status !== 'Cancelled' && t.dueDate && new Date(t.dueDate) < today) {
      alerts.push(mkAlert_('RED', 'Tasks', 'Critical task overdue: "' + t.task + '" (owner: ' + t.taskOwner + ', due ' + fmtDate_(t.dueDate) + ').'));
    }
  });

  revenue.forEach(function (r) {
    if (r.outstanding > 0 && r.daysOutstanding > ALERT_RECEIVABLE_OVERDUE_DAYS) {
      alerts.push(mkAlert_('RED', 'Receivables', 'Receivable overdue ' + r.daysOutstanding + ' days: ' + r.client + ' (' + numFmt_(r.outstanding) + ' EGP outstanding).'));
    }
  });

  projects.forEach(function (p) {
    if (p.status === 'Red') alerts.push(mkAlert_('RED', 'Delivery', 'Project "' + p.projectName + '" is status RED (owner: ' + p.pmoOwner + ').'));
  });

  campaigns.forEach(function (c) {
    if (c.budget && c.actualSpend > c.budget) {
      alerts.push(mkAlert_('YELLOW', 'Campaigns', 'Campaign "' + c.campaign + '" exceeds budget: spent ' + numFmt_(c.actualSpend) + ' vs ' + numFmt_(c.budget) + '.'));
    }
  });

  var internationalMarkets = markets.filter(function (m) { return m.country !== 'Egypt'; });
  internationalMarkets.forEach(function (m) {
    var hasPipeline = pipelineOpen.some(function (r) { return r.market === m.market; });
    if (!hasPipeline && m.revenueTarget2027 > 0) {
      alerts.push(mkAlert_('YELLOW', 'International', 'International market "' + m.market + '" has a revenue target but no open pipeline.'));
    }
  });

  pipelineOpen.forEach(function (r) {
    if ((r.stage === 'Proposal Submitted' || r.stage === 'Negotiation') && !r.nextAction) {
      alerts.push(mkAlert_('YELLOW', 'Pipeline', 'Proposal/negotiation with no next action: ' + r.organization + ' (' + r.stage + ').'));
    }
    var lastTouch = r.lastContactDate || r.firstContactDate;
    if (lastTouch && daysBetween_(lastTouch, today) > ALERT_INACTIVE_OPPORTUNITY_DAYS) {
      alerts.push(mkAlert_('YELLOW', 'Pipeline', 'Opportunity inactive ' + daysBetween_(lastTouch, today) + ' days: ' + r.organization + '.'));
    }
  });

  quarters.forEach(function (q) {
    var quarterEndPassed = quarterHasEnded_(q.quarter, today);
    if (quarterEndPassed && q.revenueActual !== '' && q.revenueActual !== undefined && Number(q.revenueActual) < Number(q.revenueTarget)) {
      alerts.push(mkAlert_('RED', 'Quarterly Gate', q.quarter + ' gate not achieved: revenue ' + numFmt_(q.revenueActual) + ' vs target ' + numFmt_(q.revenueTarget) + '.'));
    }
  });

  return alerts;
}

function mkAlert_(level, area, message) {
  return { level: level, area: area, message: message };
}
function pct_(n) { return Math.round(n * 100) + '%'; }
function numFmt_(n) { return Math.round(Number(n) || 0).toLocaleString(); }
function fmtDate_(d) {
  var dt = new Date(d);
  return dt.getFullYear() + '-' + ('0' + (dt.getMonth() + 1)).slice(-2) + '-' + ('0' + dt.getDate()).slice(-2);
}

function quarterHasEnded_(quarter, today) {
  var endMonth = { Q1: 2, Q2: 5, Q3: 8, Q4: 11 }[quarter];
  if (endMonth === undefined) return false;
  var endDate = new Date(FISCAL_YEAR, endMonth + 1, 0);
  return today > endDate;
}

// ============================================================
// SOURCE: api/WeeklyApi.gs
// ============================================================

/**
 * Section 16: Weekly CEO Review. `weekId` optional — defaults to whichever week contains
 * today's date. Returns both the "start of week" planning view and the "end of week"
 * results view in one call.
 */
function api_getWeeklyReview(weekId) {
  return safeCall_(function () {
    var weeks = readAllRecords(SHEETS.WEEKLY_EXECUTION);
    var week = weekId ? weeks.filter(function (w) { return w.weekId === weekId; })[0] : findCurrentWeek_(weeks);
    if (!week) return null;
    var prevIndex = weeks.findIndex(function (w) { return w.weekId === week.weekId; }) - 1;
    var nextIndex = weeks.findIndex(function (w) { return w.weekId === week.weekId; }) + 1;

    var tasks = readAllRecords(SHEETS.TASKS).filter(function (t) { return t.weekId === week.weekId; });
    var expenses = readAllRecords(SHEETS.EXPENSES).filter(function (e) { return e.week === week.weekId; });
    var revenue = readAllRecords(SHEETS.REVENUE);
    var pipeline = readAllRecords(SHEETS.PIPELINE);
    var start = new Date(week.startDate), end = new Date(week.endDate);

    var collectedThisWeek = sumBy(revenue, 'amountCollected', function (r) { return inRange_(r.collectionDate, start, end); });
    var bookingsThisWeek = sumBy(revenue, 'contractValue', function (r) { return inRange_(r.contractSigningDate, start, end); });
    var pipelineAddedThisWeek = sumBy(pipeline, 'estimatedOpportunityValue', function (p) { return inRange_(p.firstContactDate, start, end); });
    var winsThisWeek = countBy(pipeline, function (p) { return p.stage === 'Won' && inRange_(p.expectedCloseDate, start, end); });
    var meetingsThisWeek = countBy(pipeline, function (p) { return inRange_(p.lastContactDate, start, end); });
    var proposalsThisWeek = countBy(pipeline, function (p) { return (p.stage === 'Proposal Submitted') && inRange_(p.lastContactDate, start, end); });

    var completed = tasks.filter(function (t) { return t.status === 'Completed'; });
    var overdue = tasks.filter(function (t) { return t.status !== 'Completed' && t.status !== 'Cancelled' && t.dueDate && new Date(t.dueDate) < todayMidnight_(); });

    return {
      week: week,
      previousWeekId: prevIndex >= 0 ? weeks[prevIndex].weekId : null,
      nextWeekId: nextIndex < weeks.length ? weeks[nextIndex].weekId : null,
      startOfWeek: {
        topPriorities: tasks.filter(function (t) { return t.priority === 'Critical' || t.priority === 'High'; }).slice(0, 5),
        salesTarget: week.salesTargetWeek,
        expectedCollections: sumBy(revenue, 'outstanding', function (r) { return inRange_(r.dueDate, start, end); }),
        criticalTasks: tasks.filter(function (t) { return t.priority === 'Critical'; }),
        blockedTasks: tasks.filter(function (t) { return t.status === 'Blocked'; }),
        overdueTasks: overdue,
        budgetPlanned: week.budgetPlannedWeek,
        pipelineExpectedToMove: pipeline.filter(function (p) { return inRange_(p.nextActionDate, start, end); }).length,
        dealsExpectedToClose: pipeline.filter(function (p) { return inRange_(p.expectedCloseDate, start, end) && p.stage !== 'Won' && p.stage !== 'Lost'; }).length
      },
      endOfWeek: {
        tasksPlanned: tasks.length,
        tasksCompleted: completed.length,
        completionPct: tasks.length ? completed.length / tasks.length : 0,
        tasksOverdue: overdue.length,
        spendThisWeek: sumBy(expenses, 'actualAmount'),
        revenueCollected: collectedThisWeek,
        bookings: bookingsThisWeek,
        pipelineAdded: pipelineAddedThisWeek,
        meetingsDone: meetingsThisWeek,
        proposalsSubmitted: proposalsThisWeek,
        wins: winsThisWeek,
        mainProblems: tasks.filter(function (t) { return t.blocker; }).map(function (t) { return t.task + ': ' + t.blocker; }),
        ceoDecisionsRequired: tasks.filter(function (t) { return t.ceoAttentionRequired; }).map(function (t) { return t.task; })
      }
    };
  });
}

function findCurrentWeek_(weeks) {
  var today = todayMidnight_();
  var found = weeks.filter(function (w) { return today >= new Date(w.startDate) && today <= new Date(w.endDate); })[0];
  if (found) return found;
  // Outside plan year (e.g. testing before/after 2027) — fall back to nearest week.
  return weeks[0];
}

function inRange_(date, start, end) {
  if (!date) return false;
  var d = new Date(date);
  return d >= start && d <= end;
}

// ============================================================
// SOURCE: api/MonthlyReviewApi.gs
// ============================================================

/**
 * Section 31 (Monthly Business Review) + Section 32 (rule-based automated CEO summary).
 * Entirely rule-based — no external AI dependency — per the brief's explicit instruction.
 */
function api_getMonthlyReview(month) {
  return safeCall_(function () {
    var plan = readAllRecords(SHEETS.MASTER_PLAN).filter(function (p) { return p.month === month; })[0];
    if (!plan) return null;
    var revenue = readAllRecords(SHEETS.REVENUE).filter(function (r) { return r.month === month; });
    var expenses = readAllRecords(SHEETS.EXPENSES).filter(function (e) { return e.month === month; });
    var pipeline = readAllRecords(SHEETS.PIPELINE);
    var tasks = readAllRecords(SHEETS.TASKS);
    var weeksThisMonth = readAllRecords(SHEETS.WEEKLY_EXECUTION).filter(function (w) { return w.month === month; }).map(function (w) { return w.weekId; });
    var tasksThisMonth = tasks.filter(function (t) { return weeksThisMonth.indexOf(t.weekId) > -1; });
    var campaigns = readAllRecords(SHEETS.CAMPAIGNS).filter(function (c) { return c.campaign === plan.campaign; });
    var markets = readAllRecords(SHEETS.MARKETS);

    var revenueActual = sumBy(revenue, 'revenueRecognized');
    var bookingsActual = sumBy(revenue, 'contractValue');
    var spend = sumBy(expenses, 'actualAmount');

    var byMarketThisMonth = {};
    markets.forEach(function (m) {
      byMarketThisMonth[m.market] = sumBy(revenue, 'revenueRecognized', function (r) { return r.market === m.market; });
    });
    var marketEntries = Object.keys(byMarketThisMonth).filter(function (k) { return byMarketThisMonth[k] > 0; });
    var bestMarket = marketEntries.sort(function (a, b) { return byMarketThisMonth[b] - byMarketThisMonth[a]; })[0] || 'N/A';
    var worstMarket = marketEntries.sort(function (a, b) { return byMarketThisMonth[a] - byMarketThisMonth[b]; })[0] || 'N/A';

    var byService = groupSum_(revenue, 'service', 'revenueRecognized');
    var topService = Object.keys(byService).sort(function (a, b) { return byService[b] - byService[a]; })[0] || 'N/A';

    var byCampaignPipeline = groupSum_(readAllRecords(SHEETS.CAMPAIGNS), 'campaign', 'pipelineInfluenced');
    var topCampaign = Object.keys(byCampaignPipeline).sort(function (a, b) { return byCampaignPipeline[b] - byCampaignPipeline[a]; })[0] || 'N/A';

    var campaignSpend = sumBy(campaigns, 'actualSpend');
    var campaignRevenue = sumBy(campaigns, 'revenueInfluenced');
    var roi = campaignSpend > 0 ? (campaignRevenue - campaignSpend) / campaignSpend : 0;

    var lostDeals = pipeline.filter(function (p) { return p.stage === 'Lost'; });
    var tasksMissed = tasksThisMonth.filter(function (t) { return t.status !== 'Completed' && t.status !== 'Cancelled' && t.dueDate && new Date(t.dueDate) < todayMidnight_(); });
    var ceoDecisions = tasksThisMonth.filter(function (t) { return t.ceoAttentionRequired; });

    return {
      month: month, theme: plan.theme,
      revenueTarget: plan.revenueTarget, revenueActual: revenueActual,
      bookingsTarget: plan.salesBookingsTarget, bookingsActual: bookingsActual,
      budget: plan.growthBudget, spend: spend,
      bestMarket: bestMarket, worstMarket: worstMarket, topService: topService, topCampaign: topCampaign,
      roi: roi,
      dealsLost: lostDeals.length,
      lostReasons: distinct_(lostDeals.map(function (d) { return d.lostReason; }).filter(Boolean)),
      tasksMissed: tasksMissed.map(function (t) { return t.task; }),
      ceoDecisionsNeeded: ceoDecisions.map(function (t) { return t.task; }),
      generatedSummary: generateCeoSummary_(month, {
        revenueTarget: plan.revenueTarget, revenueActual: revenueActual,
        bookingsTarget: plan.salesBookingsTarget, bookingsActual: bookingsActual,
        budget: plan.growthBudget, spend: spend, bestMarket: bestMarket, worstMarket: worstMarket,
        dealsWonThisMonth: countBy(pipeline, function (p) { return p.stage === 'Won' && monthNameOf_(p.expectedCloseDate) === month; }),
        tasksMissedCount: tasksMissed.length, ceoDecisionsCount: ceoDecisions.length,
        overdueReceivables: sumBy(readAllRecords(SHEETS.REVENUE), 'outstanding', function (r) { return r.daysOutstanding > ALERT_RECEIVABLE_OVERDUE_DAYS; })
      })
    };
  });
}

/**
 * Section 32: produces a short natural-language executive summary from pure arithmetic
 * and thresholds — deliberately not an LLM call, so the system works with zero external
 * dependencies from day one. Swapping in a generative model later is a documented V2 option.
 */
function generateCeoSummary_(month, m) {
  var lines = [];
  var revPct = m.revenueTarget ? Math.round(m.revenueActual / m.revenueTarget * 100) : 0;
  var bookPct = m.bookingsTarget ? Math.round(m.bookingsActual / m.bookingsTarget * 100) : 0;
  var budgetUtil = m.budget ? Math.round(m.spend / m.budget * 100) : 0;
  var totalPipeline = sumBy(readAllRecords(SHEETS.PIPELINE).filter(function (r) { return r.stage !== 'Won' && r.stage !== 'Lost'; }), 'estimatedOpportunityValue');
  var coverage = REVENUE_TARGET ? Math.round(totalPipeline / REVENUE_TARGET * 10) / 10 : 0;

  lines.push(month + ' performance:');
  lines.push('Revenue achievement: ' + revPct + '%.');
  lines.push('Sales bookings achievement: ' + bookPct + '%.');
  lines.push('Growth budget utilization: ' + budgetUtil + '%.');
  lines.push('Pipeline coverage: ' + coverage + 'x.');
  if (m.dealsWonThisMonth > 0) lines.push(m.dealsWonThisMonth + ' new contract' + (m.dealsWonThisMonth > 1 ? 's' : '') + ' won.');
  if (m.bestMarket && m.bestMarket !== 'N/A') lines.push(m.bestMarket + ' is the strongest-performing market this month.');
  if (m.worstMarket && m.worstMarket !== 'N/A' && m.worstMarket !== m.bestMarket) lines.push(m.worstMarket + ' pipeline requires attention.');
  if (m.tasksMissedCount > 0) lines.push(m.tasksMissedCount + ' high-priority task' + (m.tasksMissedCount > 1 ? 's are' : ' is') + ' overdue.');
  if (m.overdueReceivables > 0) lines.push('EGP ' + numFmt_(m.overdueReceivables) + ' in collections are overdue beyond ' + ALERT_RECEIVABLE_OVERDUE_DAYS + ' days.');
  if (m.ceoDecisionsCount > 0) lines.push('CEO attention required on ' + m.ceoDecisionsCount + ' flagged item' + (m.ceoDecisionsCount > 1 ? 's' : '') + '.');
  return lines.join(' ');
}

// ============================================================
// SOURCE: api/LookupsApi.gs
// ============================================================

/** Everything the frontend needs to populate dropdowns, filters, and form selects in one call. */
function api_getLookups() {
  return safeCall_(function () {
    return {
      taskStatus: TASK_STATUS, taskPriority: TASK_PRIORITY, taskCategories: TASK_CATEGORIES,
      expenseCategories: EXPENSE_CATEGORIES, paymentStatus: PAYMENT_STATUS, paymentMethods: PAYMENT_METHODS,
      collectionStatus: COLLECTION_STATUS, salesStages: SALES_STAGES, campaignTypes: CAMPAIGN_TYPES,
      eventTypes: EVENT_TYPES, accountTiers: ACCOUNT_TIERS, riskCategories: RISK_CATEGORIES,
      riskStatus: RISK_STATUS, decisionStatus: DECISION_STATUS, countries: COUNTRIES,
      markets: readAllRecords(SHEETS.MARKETS).map(function (m) { return m.market; }),
      businessUnits: distinct_(readAllRecords(SHEETS.BUSINESS_UNITS).map(function (b) { return b.businessUnit; })),
      services: readAllRecords(SHEETS.BUSINESS_UNITS).map(function (b) { return b.service; }),
      team: readAllRecords(SHEETS.TEAM).map(function (t) { return t.name; }),
      weeks: readAllRecords(SHEETS.WEEKLY_EXECUTION).map(function (w) { return { weekId: w.weekId, label: 'Week ' + w.weekNumber + ' (' + w.month + ')' }; }),
      months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
      quarters: ['Q1', 'Q2', 'Q3', 'Q4'],
      campaigns: readAllRecords(SHEETS.CAMPAIGNS).map(function (c) { return c.campaign; }),
      events: readAllRecords(SHEETS.EVENTS).map(function (e) { return e.eventName; }),
      clients: readAllRecords(SHEETS.CLIENTS).map(function (c) { return c.clientName; })
    };
  });
}

function api_getSettings() {
  return safeCall_(function () {
    var sheet = ss_().getSheetByName(SHEETS.SETTINGS);
    if (!sheet || sheet.getLastRow() < 2) return {};
    var values = sheet.getRange(2, 1, sheet.getLastRow() - 1, 2).getValues();
    var out = {};
    values.forEach(function (row) { if (row[0]) out[row[0]] = row[1]; });
    return out;
  });
}
