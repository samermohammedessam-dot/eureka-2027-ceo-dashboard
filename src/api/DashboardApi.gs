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
