/** Pass filters.page to get { records, total, page, pageSize, totalPages } instead of a plain array — see paginate_(). */
function api_getRevenue(filters) {
  return safeCall_(function () {
    var all = applyFilters_(readAllRecords(SHEETS.REVENUE).map(stripRowMeta_), filters);
    return (filters && filters.page) ? paginate_(all, filters) : all;
  });
}

function api_saveRevenue(rec) {
  return safeCall_(function () {
    if (rec.revenueId) {
      updateRecordById(SHEETS.REVENUE, rec.revenueId, rec);
    } else {
      appendRecord(SHEETS.REVENUE, rec);
    }
    recomputeRevenue_();
    invalidateDashboardCache_();
    return rec.revenueId || true;
  });
}

function api_deleteRevenue(id) {
  return safeCall_(function () {
    var result = deleteRecordById(SHEETS.REVENUE, id);
    invalidateDashboardCache_();
    return result;
  });
}

/** Section 10: outstanding, collection %, DSO, revenue vs targets — computed on demand for the Revenue view. */
function api_getRevenueSummary() {
  return safeCall_(function () {
    var records = readAllRecords(SHEETS.REVENUE);
    var invoiced = sumBy(records, 'invoiceAmount');
    var collected = sumBy(records, 'amountCollected');
    var outstanding = sumBy(records, 'outstanding');
    var recognized = sumBy(records, 'revenueRecognized');
    var bookings = sumBy(records, 'contractValue');
    var dso = computeDSO_(records);
    return {
      invoiced: invoiced, collected: collected, outstanding: outstanding, recognized: recognized,
      bookings: bookings, collectionPct: invoiced ? collected / invoiced : 0, dso: dso,
      revenueTarget: REVENUE_TARGET, bookingsTarget: ANNUAL_BOOKINGS_TARGET
    };
  });
}

function computeDSO_(records) {
  var withDays = records.filter(function (r) { return r.amountCollected > 0 && r.collectionDate && r.invoiceDate; });
  if (!withDays.length) return null;
  var totalDays = withDays.reduce(function (sum, r) { return sum + daysBetween_(r.invoiceDate, r.collectionDate); }, 0);
  return Math.round(totalDays / withDays.length);
}
