/**
 * ONE-TIME REPAIR for a spreadsheet that was already built and seeded before two seed-data
 * bugs were fixed:
 *
 *  1. Duplicate IDs — bulkAppendRecords() generated every record's ID by re-scanning the
 *     sheet for the current max ID, but did that BEFORE writing any of the batch to the
 *     sheet, so every record in the same seed call saw the same unchanged sheet and got
 *     the same "next" ID (all Tasks came out as TSK-0001, all Campaigns as CMP-0001, etc).
 *     Fixed at the source in SheetService.gs/IdGenerator.gs so a fresh install can't
 *     reproduce it — this file repairs a sheet that was already seeded with the old code.
 *
 *  2. Wrong week->month mapping — the month name for a week was derived with
 *     Utilities.formatDate(date, 'GMT', 'MMMM'), which reinterprets a date built in the
 *     script's Africa/Cairo (UTC+2) timeZone as if it were UTC. That shifts local midnight
 *     back onto the previous calendar day, which only matters when a week starts on the 1st
 *     of a month — that day gets misread as the last day of the PREVIOUS month. Two of the
 *     52 seeded weeks start on the 1st of a month: WK-01 (Jan 1, misread as December) and
 *     WK-40 (Oct 1, misread as September). Fixed at the source in Compute.gs (monthNameOf_)
 *     and SeedWeekly.gs — this file recomputes the 52 Weekly Execution rows and the seeded
 *     Tasks that inherited the wrong month.
 *
 * This function is safe to run on a live, already-seeded sheet:
 *  - Only rewrites the ID column of a table if it actually finds duplicate IDs in it.
 *  - Only rewrites Weekly Execution's derived fields (month, quarter, strategic theme,
 *    campaign, primary/secondary market, and the three weekly target figures) — weekId,
 *    weekNumber, startDate, endDate and notes are left exactly as they are, and no rows are
 *    added or removed.
 *  - Only touches a seeded Task row if its description still carries the *exact* wrong
 *    theme/campaign text the original bug produced, so any task you've since edited, or any
 *    task you've added yourself, is left untouched.
 *  - Never reads or writes 06_Revenue, 07_Expenses, 08_Sales_Pipeline, 09_Target_Accounts,
 *    16_Clients, 17_Projects, 18_Partnerships, 19_Academy, 20_Case_Studies, 24_Risks, or
 *    25_Decisions — none of those sheets are touched by this function.
 *  - Idempotent — every step first checks whether anything is actually wrong, so running it
 *    a second (or fifth) time is harmless and will simply report nothing left to fix.
 */
function repairExisting2027SeedData() {
  var report = [];
  report.push(dedupeAndRenumberIds_(SHEETS.TEAM, 'teamId', 'EMP'));
  report.push(dedupeAndRenumberIds_(SHEETS.MARKETS, 'marketId', 'MKT'));
  report.push(dedupeAndRenumberIds_(SHEETS.BUSINESS_UNITS, 'buId', 'BU'));
  report.push(dedupeAndRenumberIds_(SHEETS.CAMPAIGNS, 'campaignId', 'CMP'));
  report.push(dedupeAndRenumberIds_(SHEETS.EVENTS, 'eventId', 'EVT'));
  report.push(dedupeAndRenumberIds_(SHEETS.KPIS, 'kpiId', 'KPI'));
  report.push(dedupeAndRenumberIds_(SHEETS.QUARTERLY_REVIEW, 'quarterId', 'Q'));
  report.push(dedupeAndRenumberIds_(SHEETS.DIGITAL_ROADMAP, 'featureId', 'FTR'));
  report.push(dedupeAndRenumberIds_(SHEETS.TASKS, 'taskId', 'TSK'));
  report.push(repairWeeklyExecutionAndTasks_());

  recomputeAllCalculatedFields();
  refreshDashboardSheet();

  var summary = 'Eureka 2027 seed-data repair complete:\n\n' + report.join('\n');
  Logger.log(summary);
  try {
    SpreadsheetApp.getUi().alert(summary);
  } catch (e) {
    // No UI context (e.g. run directly from the Apps Script editor's function dropdown) —
    // the summary is still in the Logger output (View > Logs) and in this function's return value.
  }
  return summary;
}

/**
 * Rewrites a sheet's ID column as prefix-0001, prefix-0002, ... in row order, but only if
 * it finds duplicate values there in the first place. Safe even though nothing else in this
 * project stores a foreign key to any of these IDs (every cross-sheet reference in this
 * system is by a human-readable name — market, business unit, team member, campaign, event —
 * never by these internal sequence IDs), so renumbering can't break a lookup elsewhere.
 */
function dedupeAndRenumberIds_(sheetName, idKey, prefix) {
  var sheet = ss_().getSheetByName(sheetName);
  if (!sheet || sheet.getLastRow() < 2) return sheetName + ': no rows — skipped.';
  var schema = getSchema(sheetName);
  var idColIndex = schema.map(function (c) { return c.key; }).indexOf(idKey);
  if (idColIndex === -1) return sheetName + ': no "' + idKey + '" column — skipped.';

  var numRows = sheet.getLastRow() - 1;
  var ids = sheet.getRange(2, idColIndex + 1, numRows, 1).getValues();
  var seen = {};
  var duplicateCount = 0;
  ids.forEach(function (row) {
    var v = row[0];
    if (seen[v]) duplicateCount++;
    seen[v] = true;
  });
  if (duplicateCount === 0) {
    return sheetName + ': ' + numRows + ' row(s), IDs already unique — no change.';
  }

  var newIds = [];
  for (var i = 1; i <= numRows; i++) newIds.push([prefix + '-' + padId_(i)]);
  sheet.getRange(2, idColIndex + 1, numRows, 1).setValues(newIds);
  return sheetName + ': renumbered ' + numRows + ' row(s) (' + duplicateCount + ' duplicate ID value(s) found) -> ' +
    prefix + '-0001..' + prefix + '-' + padId_(numRows) + '.';
}

/**
 * Recomputes Month, Quarter, Strategic Theme, Campaign, Primary/Secondary Market, and the
 * three weekly target figures for every row in 04_Weekly_Execution from that row's own
 * Start Date — the canonical rule requested — then patches any seeded Task rows that still
 * carry the stale (wrong) theme/campaign text.
 */
function repairWeeklyExecutionAndTasks_() {
  var sheet = ss_().getSheetByName(SHEETS.WEEKLY_EXECUTION);
  if (!sheet || sheet.getLastRow() < 2) return SHEETS.WEEKLY_EXECUTION + ': no rows found — skipped.';

  var plan = getMonthlyStrategyPlan_();
  var planByMonth = {};
  plan.forEach(function (m) { planByMonth[m.month] = m; });

  var schema = getSchema(SHEETS.WEEKLY_EXECUTION);
  var idx = {};
  schema.forEach(function (c, i) { idx[c.key] = i; });

  var numRows = sheet.getLastRow() - 1;
  var values = sheet.getRange(2, 1, numRows, schema.length).getValues();

  // Pass 1: the true month for every row, from Start Date alone — then how many weeks land
  // in each month, so each month's targets split evenly across exactly its own weeks.
  var correctedMonths = values.map(function (row) { return monthNameOf_(row[idx.startDate]); });
  var weeksPerMonth = {};
  correctedMonths.forEach(function (mn) { weeksPerMonth[mn] = (weeksPerMonth[mn] || 0) + 1; });

  // Pass 2: apply the correction to every row, and remember which weeks actually changed
  // (together with what was wrong before) so seeded Tasks can be patched to match.
  var fingerprints = {}; // weekId -> { oldTheme, oldCampaign, newWeek }
  for (var r = 0; r < numRows; r++) {
    var row = values[r];
    var monthName = correctedMonths[r];
    var m = planByMonth[monthName];
    if (!m) continue; // defensive: an unrecognized month string is left untouched rather than guessed at

    var weekId = row[idx.weekId];
    var oldTheme = row[idx.strategicTheme];
    var oldCampaign = row[idx.campaign];
    var weeksInMonth = weeksPerMonth[monthName];

    var newValues = {
      month: monthName,
      quarter: MONTH_TO_QUARTER_[monthName],
      primaryMarket: firstMarketToken_(m.primaryMarket),
      secondaryMarket: String(m.primaryMarket).indexOf('+') > -1 ? m.primaryMarket.split('+')[1].trim() : '',
      strategicTheme: m.theme,
      campaign: m.campaign,
      salesTargetWeek: Math.round(m.sales / weeksInMonth),
      revenueTargetWeek: Math.round(m.revenue / weeksInMonth),
      budgetPlannedWeek: Math.round(m.budget / weeksInMonth)
    };

    var changed = String(row[idx.month]) !== String(newValues.month) ||
      String(oldTheme) !== String(newValues.strategicTheme) ||
      String(oldCampaign) !== String(newValues.campaign) ||
      String(row[idx.salesTargetWeek]) !== String(newValues.salesTargetWeek) ||
      String(row[idx.revenueTargetWeek]) !== String(newValues.revenueTargetWeek) ||
      String(row[idx.budgetPlannedWeek]) !== String(newValues.budgetPlannedWeek);

    Object.keys(newValues).forEach(function (key) { row[idx[key]] = newValues[key]; });

    if (changed) {
      fingerprints[weekId] = {
        oldTheme: oldTheme,
        oldCampaign: oldCampaign,
        newWeek: { weekId: weekId, month: monthName, strategicTheme: newValues.strategicTheme, campaign: newValues.campaign, primaryMarket: newValues.primaryMarket }
      };
    }
  }

  sheet.getRange(2, 1, numRows, schema.length).setValues(values);

  var changedWeekIds = Object.keys(fingerprints);
  var taskReport = repairSeededTasksForWeeks_(fingerprints, planByMonth);
  return SHEETS.WEEKLY_EXECUTION + ': recomputed month/quarter/theme/campaign/market and re-split monthly ' +
    'targets across all ' + numRows + ' week rows from each row\'s own Start Date' +
    (changedWeekIds.length ? ' (' + changedWeekIds.length + ' week row(s) had incorrect data: ' + changedWeekIds.join(', ') + ')' : ' (none needed correction)') +
    '. ' + taskReport;
}

/**
 * Patches only the seeded Task rows that still carry the exact wrong theme/campaign text
 * from the original bug — matched by looking for that literal "(oldTheme — oldCampaign)"
 * suffix in the task's description. That fingerprint can only appear on a row this seeder
 * itself generated with the wrong month, so a task you've edited or added by hand (which
 * won't happen to end with that exact wrong text) is never touched.
 */
function repairSeededTasksForWeeks_(fingerprints, planByMonth) {
  var weekIds = Object.keys(fingerprints);
  if (!weekIds.length) return 'No task rows required correction.';

  var taskSheet = ss_().getSheetByName(SHEETS.TASKS);
  if (!taskSheet || taskSheet.getLastRow() < 2) return 'No task rows found.';
  var taskSchema = getSchema(SHEETS.TASKS);
  var tIdx = {};
  taskSchema.forEach(function (c, i) { tIdx[c.key] = i; });

  var numTaskRows = taskSheet.getLastRow() - 1;
  var taskValues = taskSheet.getRange(2, 1, numTaskRows, taskSchema.length).getValues();
  var fixedCount = 0;

  weekIds.forEach(function (weekId) {
    var fp = fingerprints[weekId];
    var w = fp.newWeek;
    var m = planByMonth[w.month];
    if (!m) return;
    var oldFingerprint = ' (' + fp.oldTheme + ' — ' + fp.oldCampaign + ')';

    for (var r = 0; r < taskValues.length; r++) {
      var row = taskValues[r];
      if (row[tIdx.weekId] !== weekId) continue;
      var description = String(row[tIdx.taskDescription] || '');
      if (description.slice(-oldFingerprint.length) !== oldFingerprint) continue; // not a stale seeded row — leave it alone

      var title = row[tIdx.task];
      if (title === 'Weekly CEO / BD sync — review targets vs actual') {
        row[tIdx.taskDescription] = title + ' (' + w.strategicTheme + ' — ' + w.campaign + ')';
      } else if (String(title).indexOf('Weekly pipeline & CRM update') === 0) {
        var newTitle = 'Weekly pipeline & CRM update — ' + w.primaryMarket;
        row[tIdx.task] = newTitle;
        row[tIdx.taskDescription] = newTitle + ' (' + w.strategicTheme + ' — ' + w.campaign + ')';
      } else {
        // The strategy-action task. The original per-week rotation index into that month's
        // action list can't be reconstructed after the fact, so this deterministically uses
        // the corrected month's first action — a genuine action for the right month, just not
        // guaranteed to be the exact rotation slot originally seeded for this specific week.
        var newAction = m.actions[0];
        row[tIdx.task] = newAction;
        row[tIdx.taskDescription] = newAction + ' (' + w.strategicTheme + ' — ' + w.campaign + ')';
        row[tIdx.taskCategory] = categoryForOwner_(m.owner);
        row[tIdx.expectedDeliverable] = m.kpis;
        row[tIdx.taskOwner] = primaryOwnerToken_(m.owner);
        row[tIdx.supportingTeam] = m.owner;
      }
      fixedCount++;
    }
  });

  if (fixedCount > 0) {
    taskSheet.getRange(2, 1, taskValues.length, taskSchema.length).setValues(taskValues);
  }
  return fixedCount + ' seeded task row(s) corrected across ' + weekIds.length + ' affected week(s).';
}
