/**
 * Section 15: the CEO homepage. ONE call returns every number and chart series the
 * dashboard needs (Performance Sprint: this replaced a version that additionally called
 * computeAlerts_() with no arguments, which re-read Revenue/Expenses/Pipeline/Tasks/Markets
 * a second time — every sheet below is now read exactly once per call).
 *
 * The assembled result is cached whole (DASHBOARD_CACHE_TTL_SECONDS) rather than caching
 * each sheet's raw rows separately: simpler to reason about, and it also skips re-running
 * every aggregation/alert computation on a cache hit, not just the sheet reads.
 * invalidateDashboardCache_() (called after any Tasks/Pipeline/Revenue/Expenses/Campaigns/
 * Events write — see those API files) clears it early so a save is reflected well within
 * the cache's normal lifetime, not after up to 4 stale minutes.
 */
function api_getDashboardBootstrap() {
  return safeCall_(getDashboardBootstrapCached_);
}

// Old name kept as an alias: nothing else needs to change if some future code (or a custom
// menu script) still calls api_getDashboard() directly — same payload shape either way.
function api_getDashboard() {
  return api_getDashboardBootstrap();
}

function getDashboardBootstrapCached_() {
  var cache = CacheService.getScriptCache();
  var cached = cache.get(DASHBOARD_CACHE_KEY);
  if (cached) {
    try { return JSON.parse(cached); } catch (e) { /* corrupt/unexpected cache entry — fall through and rebuild */ }
  }
  var result = buildDashboardBootstrap_();
  try {
    cache.put(DASHBOARD_CACHE_KEY, JSON.stringify(result), DASHBOARD_CACHE_TTL_SECONDS);
  } catch (e) {
    // Payload too large for CacheService's 100KB-per-key limit — skip caching, still return fresh data.
  }
  return result;
}

function invalidateDashboardCache_() {
  CacheService.getScriptCache().remove(DASHBOARD_CACHE_KEY);
}

function buildDashboardBootstrap_() {
  var tStart = new Date().getTime();
  var revenue = readAllRecords(SHEETS.REVENUE);
  var expenses = readAllRecords(SHEETS.EXPENSES);
  var pipelineAll = readAllRecords(SHEETS.PIPELINE);
  var pipelineOpen = pipelineAll.filter(function (r) { return r.stage !== 'Won' && r.stage !== 'Lost'; });
  var won = pipelineAll.filter(function (r) { return r.stage === 'Won'; });
  var lost = pipelineAll.filter(function (r) { return r.stage === 'Lost'; });
  var tasks = readAllRecords(SHEETS.TASKS);
  var plan = readAllRecords(SHEETS.MASTER_PLAN);
  var markets = readAllRecords(SHEETS.MARKETS);
  var businessUnits = readAllRecords(SHEETS.BUSINESS_UNITS);
  var projects = readAllRecords(SHEETS.PROJECTS);
  var campaigns = readAllRecords(SHEETS.CAMPAIGNS);
  var quarters = readAllRecords(SHEETS.QUARTERLY_REVIEW);
  var tReads = new Date().getTime();
  logTiming_('dashboardBootstrap.sheetReads', tReads - tStart);

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

    var tAgg = new Date().getTime();
    logTiming_('dashboardBootstrap.aggregation', tAgg - tReads);

    var alerts = computeAlerts_({
      revenue: revenue, expenses: expenses, pipelineAll: pipelineAll, tasks: tasks,
      projects: projects, campaigns: campaigns, markets: markets, quarters: quarters
    });
    var tAlerts = new Date().getTime();
    logTiming_('dashboardBootstrap.alerts', tAlerts - tAgg);
    logTiming_('dashboardBootstrap.total', tAlerts - tStart);

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
      alerts: alerts
    };
}

function distinct_(arr) {
  var seen = {};
  var out = [];
  arr.forEach(function (v) { if (!seen[v]) { seen[v] = true; out.push(v); } });
  return out;
}
