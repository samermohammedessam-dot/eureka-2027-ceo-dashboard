/**
 * Generic CRUD endpoints for the "reference/tracker" sheets that don't need bespoke
 * calculated fields: Target Accounts, Partnerships, Academy, Case Studies, Digital Roadmap,
 * Decisions, Risks, Projects, Clients, Team, Markets, Business Units.
 */
function api_getGenericRecords(sheetName, filters) {
  return safeCall_(function () {
    assertGenericSheetAllowed_(sheetName);
    var records = readAllRecords(sheetName).map(stripRowMeta_);
    return applyFilters_(records, filters);
  });
}

function api_saveGenericRecord(sheetName, record) {
  return safeCall_(function () {
    assertGenericSheetAllowed_(sheetName);
    var schema = getSchema(sheetName);
    var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
    var idKey = idCol ? idCol.key : null;
    if (idKey && record[idKey]) {
      updateRecordById(sheetName, record[idKey], record);
      recomputeAllCalculatedFields();
      return record[idKey];
    }
    var newId = appendRecord(sheetName, record);
    recomputeAllCalculatedFields();
    return newId;
  });
}

function api_deleteGenericRecord(sheetName, idValue) {
  return safeCall_(function () {
    assertGenericSheetAllowed_(sheetName);
    return deleteRecordById(sheetName, idValue);
  });
}
