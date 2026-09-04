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
