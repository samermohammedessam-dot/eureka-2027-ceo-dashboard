/**
 * Generic CRUD endpoints for the "reference/tracker" sheets that don't need bespoke
 * calculated fields: Target Accounts, Partnerships, Academy, Case Studies, Digital Roadmap,
 * Decisions, Risks, Projects, Clients, Team, Markets, Business Units.
 */
/** Pass filters.page to get { records, total, page, pageSize, totalPages } instead of a plain array — see paginate_(). */
function api_getGenericRecords(sheetName, filters) {
  return safeCall_(function () {
    assertGenericSheetAllowed_(sheetName);
    var records = readAllRecords(sheetName).map(stripRowMeta_);
    var filtered = applyFilters_(records, filters);
    return (filters && filters.page) ? paginate_(filtered, filters) : filtered;
  });
}

function api_saveGenericRecord(sheetName, record) {
  return safeCall_(function () {
    assertGenericSheetAllowed_(sheetName);
    var schema = getSchema(sheetName);
    var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
    var idKey = idCol ? idCol.key : null;
    var resultId;
    if (idKey && record[idKey]) {
      updateRecordById(sheetName, record[idKey], record);
      resultId = record[idKey];
    } else {
      resultId = appendRecord(sheetName, record);
    }
    recomputeAllCalculatedFields();
    invalidateCachesForSheet_(sheetName);
    return resultId;
  });
}

function api_deleteGenericRecord(sheetName, idValue) {
  return safeCall_(function () {
    assertGenericSheetAllowed_(sheetName);
    var result = deleteRecordById(sheetName, idValue);
    invalidateCachesForSheet_(sheetName);
    return result;
  });
}

/** Team/Markets/Business Units/Clients feed api_getLookups(); every generic sheet can affect dashboard alerts (e.g. Projects). */
function invalidateCachesForSheet_(sheetName) {
  invalidateDashboardCache_();
  if ([SHEETS.TEAM, SHEETS.MARKETS, SHEETS.BUSINESS_UNITS, SHEETS.CLIENTS].indexOf(sheetName) > -1) {
    invalidateLookupsCache_();
  }
}
