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
function fmtDate_(d) { return Utilities.formatDate(new Date(d), 'GMT', 'yyyy-MM-dd'); }

function quarterHasEnded_(quarter, today) {
  var endMonth = { Q1: 2, Q2: 5, Q3: 8, Q4: 11 }[quarter];
  if (endMonth === undefined) return false;
  var endDate = new Date(FISCAL_YEAR, endMonth + 1, 0);
  return today > endDate;
}
