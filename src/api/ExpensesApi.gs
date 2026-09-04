function api_getExpenses(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.EXPENSES).map(stripRowMeta_), filters);
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
    return rec.expenseId || true;
  });
}

function api_deleteExpense(id) {
  return safeCall_(function () { return deleteRecordById(SHEETS.EXPENSES, id); });
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
