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
