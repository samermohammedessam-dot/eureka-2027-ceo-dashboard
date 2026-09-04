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
