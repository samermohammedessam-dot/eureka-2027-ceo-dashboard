/**
 * Breaks the 2027 plan into 52 weekly execution periods (Section 8) and generates a
 * grounded task list per week, derived from that month's "primary actions" and KPI targets
 * in the brief — plus two standing weekly cadences (pipeline/CRM review, CEO/BD sync) that
 * apply every week regardless of theme. Monthly financial targets are split evenly across
 * the weeks that fall in each month so week-level and month-level targets always reconcile.
 */
function seedWeeklyExecutionAndTasks() {
  clearDataRows_(SHEETS.WEEKLY_EXECUTION);
  clearDataRows_(SHEETS.TASKS);

  var plan = getMonthlyStrategyPlan_();
  var planByMonth = {};
  plan.forEach(function (m) { planByMonth[m.month] = m; });
  var quarterOf = { January: 'Q1', February: 'Q1', March: 'Q1', April: 'Q2', May: 'Q2', June: 'Q2', July: 'Q3', August: 'Q3', September: 'Q3', October: 'Q4', November: 'Q4', December: 'Q4' };

  var weeks = buildWeekDateRanges_(); // [{weekNumber,start,end}] x52
  // Group weeks by the month that contains their start date.
  var weeksByMonth = {};
  weeks.forEach(function (w) {
    var monthName = Utilities.formatDate(w.start, 'GMT', 'MMMM');
    weeksByMonth[monthName] = weeksByMonth[monthName] || [];
    weeksByMonth[monthName].push(w);
  });

  var weeklyRecords = [];
  var actionCursor = {}; // per-month index into that month's actions list, so consecutive weeks get different actions

  weeks.forEach(function (w) {
    var monthName = Utilities.formatDate(w.start, 'GMT', 'MMMM');
    var m = planByMonth[monthName];
    var weeksInThisMonth = weeksByMonth[monthName].length;
    w.weekId = 'WK-' + ('00' + w.weekNumber).slice(-2);
    w.month = monthName;
    w.quarter = quarterOf[monthName];
    w.strategicTheme = m.theme;
    w.campaign = m.campaign;
    w.primaryMarket = firstMarketToken_(m.primaryMarket);
    w.secondaryMarket = String(m.primaryMarket).indexOf('+') > -1 ? m.primaryMarket.split('+')[1].trim() : '';
    w.salesTargetWeek = Math.round(m.sales / weeksInThisMonth);
    w.revenueTargetWeek = Math.round(m.revenue / weeksInThisMonth);
    w.budgetPlannedWeek = Math.round(m.budget / weeksInThisMonth);
    weeklyRecords.push({
      weekId: w.weekId, weekNumber: w.weekNumber, startDate: w.start, endDate: w.end,
      month: w.month, quarter: w.quarter, primaryMarket: w.primaryMarket, secondaryMarket: w.secondaryMarket,
      strategicTheme: w.strategicTheme, campaign: w.campaign,
      salesTargetWeek: w.salesTargetWeek, revenueTargetWeek: w.revenueTargetWeek, budgetPlannedWeek: w.budgetPlannedWeek,
      notes: ''
    });
  });
  bulkAppendRecords(SHEETS.WEEKLY_EXECUTION, weeklyRecords);

  var taskRecords = [];
  weeks.forEach(function (w) {
    var m = planByMonth[w.month];
    actionCursor[w.month] = actionCursor[w.month] || 0;
    var action = m.actions[actionCursor[w.month] % m.actions.length];
    actionCursor[w.month]++;

    taskRecords.push(makeTask_(w, action, categoryForOwner_(m.owner), m.owner, 'High', m.kpis));
    taskRecords.push(makeTask_(w, 'Weekly pipeline & CRM update — ' + w.primaryMarket, 'Sales', 'Commercial Director', 'Medium', 'Pipeline data current; stages accurate; next actions set on every open opportunity'));
    taskRecords.push(makeTask_(w, 'Weekly CEO / BD sync — review targets vs actual', 'CEO', 'CEO', 'Medium', 'Decisions logged; blockers escalated'));
  });
  bulkAppendRecords(SHEETS.TASKS, taskRecords);

  return 'Seeded ' + weeklyRecords.length + ' weeks and ' + taskRecords.length + ' tasks.';
}

function makeTask_(w, taskText, category, owner, priority, deliverable) {
  return {
    weekId: w.weekId, task: taskText, taskCategory: category,
    taskDescription: taskText + ' (' + w.strategicTheme + ' — ' + w.campaign + ')',
    expectedDeliverable: deliverable, taskOwner: primaryOwnerToken_(owner), supportingTeam: owner,
    priority: priority, status: 'Not Started', startDate: w.start, dueDate: w.end,
    completionDate: '', percentCompletion: 0, dependency: '', blocker: '', ceoAttentionRequired: false, notes: ''
  };
}

function primaryOwnerToken_(ownerField) {
  return String(ownerField).split('+')[0].trim();
}

function categoryForOwner_(ownerField) {
  var o = String(ownerField);
  if (o.indexOf('International BD') > -1) return 'International Expansion';
  if (o.indexOf('CEO') === 0) return 'CEO';
  return 'Business Development';
}

/** 52 sequential 7-day weeks starting Jan 1 2027; the 52nd week absorbs Dec 31 so the whole year is covered. */
function buildWeekDateRanges_() {
  var weeks = [];
  var cursor = new Date(FISCAL_YEAR, 0, 1);
  for (var i = 1; i <= 52; i++) {
    var start = new Date(cursor);
    var end;
    if (i === 52) {
      end = new Date(FISCAL_YEAR, 11, 31);
    } else {
      end = new Date(cursor);
      end.setDate(end.getDate() + 6);
    }
    weeks.push({ weekNumber: i, start: start, end: end });
    cursor = new Date(end);
    cursor.setDate(cursor.getDate() + 1);
  }
  return weeks;
}
