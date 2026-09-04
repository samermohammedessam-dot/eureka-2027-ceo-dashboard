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

function monthNameOf_(date) {
  if (!date) return '';
  return Utilities.formatDate(new Date(date), 'GMT', 'MMMM');
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
