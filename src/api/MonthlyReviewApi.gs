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
