/** Pass filters.page to get { records, total, page, pageSize, totalPages } instead of a plain array — see paginate_(). */
function api_getExpenses(filters) {
  return safeCall_(function () {
    var all = applyFilters_(readAllRecords(SHEETS.EXPENSES).map(stripRowMeta_), filters);
    return (filters && filters.page) ? paginate_(all, filters) : all;
  });
}

function api_saveExpense(rec) {
  return safeCall_(function () {
    if (rec.expenseId) {
      updateRecordById(SHEETS.EXPENSES, rec.expenseId, rec);
    } else {
      appendRecord(SHEETS.EXPENSES, rec);
    }
    recomputeExpenses_();
    invalidateDashboardCache_();
    return rec.expenseId || true;
  });
}

function api_deleteExpense(id) {
  return safeCall_(function () {
    var result = deleteRecordById(SHEETS.EXPENSES, id);
    invalidateDashboardCache_();
    return result;
  });
}

function api_getExpenseSummary() {
  return safeCall_(function () {
    var records = readAllRecords(SHEETS.EXPENSES);
    var budgeted = sumBy(records, 'budgetedAmount');
    var actual = sumBy(records, 'actualAmount');
    var byMarket = groupSum_(records, 'market', 'actualAmount');
    var byMonth = groupSum_(records, 'month', 'actualAmount');
    var byCampaign = groupSum_(records, 'campaign', 'actualAmount');
    var byEvent = groupSum_(records, 'event', 'actualAmount');
    var byCategory = groupSum_(records, 'expenseCategory', 'actualAmount');
    return {
      budgeted: budgeted, actual: actual, variance: budgeted - actual,
      utilizationPct: budgeted ? actual / budgeted : 0,
      byMarket: byMarket, byMonth: byMonth, byCampaign: byCampaign, byEvent: byEvent, byCategory: byCategory,
      annualBudget: TOTAL_GROWTH_BUDGET_2027
    };
  });
}

function groupSum_(records, groupKey, valueKey) {
  var out = {};
  records.forEach(function (r) {
    var g = r[groupKey] || 'Unassigned';
    out[g] = (out[g] || 0) + (Number(r[valueKey]) || 0);
  });
  return out;
}
