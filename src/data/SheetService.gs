/**
 * Generic data-access layer. Every other module reads/writes sheets exclusively through
 * these functions so batching, caching, and header-mapping logic lives in one place.
 */

function ss_() {
  return SpreadsheetApp.getActiveSpreadsheet();
}

function getOrCreateSheet(name) {
  var sheet = ss_().getSheetByName(name);
  if (!sheet) sheet = ss_().insertSheet(name);
  return sheet;
}

/**
 * Reads all data rows of a sheet as an array of plain objects keyed by schema `key`.
 * Empty trailing rows are skipped. Adds `_row` (1-based sheet row number) to every object
 * so callers can write updates back without re-scanning.
 */
function readAllRecords(sheetName) {
  var sheet = ss_().getSheetByName(sheetName);
  if (!sheet || sheet.getLastRow() < 2) return [];
  var schema = getSchema(sheetName);
  var numCols = schema.length;
  var values = sheet.getRange(2, 1, sheet.getLastRow() - 1, numCols).getValues();
  var records = [];
  for (var r = 0; r < values.length; r++) {
    var row = values[r];
    if (row.join('') === '') continue; // fully blank row
    var obj = { _row: r + 2 };
    for (var c = 0; c < schema.length; c++) {
      obj[schema[c].key] = row[c];
    }
    records.push(obj);
  }
  return records;
}

/** Cached read for dashboard-style aggregations. TTL defined in Constants.gs. */
function readAllRecordsCached(sheetName) {
  var cache = CacheService.getScriptCache();
  var cacheKey = 'records_' + sheetName;
  var cached = cache.get(cacheKey);
  if (cached) {
    try { return JSON.parse(cached); } catch (e) { /* fall through to fresh read */ }
  }
  var records = readAllRecords(sheetName);
  try {
    cache.put(cacheKey, JSON.stringify(records), CACHE_TTL_SECONDS);
  } catch (e) {
    // Payload too large for cache (>100KB) — silently skip caching, still return fresh data.
  }
  return records;
}

function invalidateCache(sheetName) {
  CacheService.getScriptCache().remove('records_' + sheetName);
}

/** Appends one record (plain object keyed by schema `key`). Returns the generated ID if the schema has an idPrefix column. */
function appendRecord(sheetName, record) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheet = getOrCreateSheet(sheetName);
    var schema = getSchema(sheetName);
    var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
    if (idCol && !record[idCol.key]) {
      record[idCol.key] = generateId(sheetName, idCol.idPrefix);
    }
    var row = schema.map(function (c) {
      return (record[c.key] === undefined || record[c.key] === null) ? '' : record[c.key];
    });
    sheet.appendRow(row);
    invalidateCache(sheetName);
    return record[idCol ? idCol.key : null] || sheet.getLastRow();
  } finally {
    lock.releaseLock();
  }
}

/** Updates a record identified by its ID column value. Only keys present in `patch` are overwritten. */
function updateRecordById(sheetName, idValue, patch) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheet = ss_().getSheetByName(sheetName);
    if (!sheet) return false;
    var schema = getSchema(sheetName);
    var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
    if (!idCol) return false;
    var idColIndex = schema.indexOf(idCol);
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return false;
    var ids = sheet.getRange(2, idColIndex + 1, lastRow - 1, 1).getValues();
    for (var r = 0; r < ids.length; r++) {
      if (String(ids[r][0]) === String(idValue)) {
        var rowNum = r + 2;
        var existing = {};
        var rowValues = sheet.getRange(rowNum, 1, 1, schema.length).getValues()[0];
        schema.forEach(function (c, i) { existing[c.key] = rowValues[i]; });
        var merged = existing;
        for (var k in patch) merged[k] = patch[k];
        var newRow = schema.map(function (c) {
          return (merged[c.key] === undefined || merged[c.key] === null) ? '' : merged[c.key];
        });
        sheet.getRange(rowNum, 1, 1, schema.length).setValues([newRow]);
        invalidateCache(sheetName);
        return true;
      }
    }
    return false;
  } finally {
    lock.releaseLock();
  }
}

/** Deletes a record identified by its ID column value. */
function deleteRecordById(sheetName, idValue) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheet = ss_().getSheetByName(sheetName);
    if (!sheet) return false;
    var schema = getSchema(sheetName);
    var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
    if (!idCol) return false;
    var idColIndex = schema.indexOf(idCol);
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return false;
    var ids = sheet.getRange(2, idColIndex + 1, lastRow - 1, 1).getValues();
    for (var r = 0; r < ids.length; r++) {
      if (String(ids[r][0]) === String(idValue)) {
        sheet.deleteRow(r + 2);
        invalidateCache(sheetName);
        return true;
      }
    }
    return false;
  } finally {
    lock.releaseLock();
  }
}

/** Bulk-appends many records in a single write (used by seeders — far fewer API calls than looping appendRecord). */
function bulkAppendRecords(sheetName, records) {
  if (!records || records.length === 0) return;
  var sheet = getOrCreateSheet(sheetName);
  var schema = getSchema(sheetName);
  var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
  var rows = records.map(function (record) {
    if (idCol && !record[idCol.key]) {
      record[idCol.key] = generateId(sheetName, idCol.idPrefix);
    }
    return schema.map(function (c) {
      return (record[c.key] === undefined || record[c.key] === null) ? '' : record[c.key];
    });
  });
  sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, schema.length).setValues(rows);
  invalidateCache(sheetName);
}

function sumBy(records, valueKey, predicate) {
  var total = 0;
  for (var i = 0; i < records.length; i++) {
    if (!predicate || predicate(records[i])) {
      var v = Number(records[i][valueKey]);
      if (!isNaN(v)) total += v;
    }
  }
  return total;
}

function countBy(records, predicate) {
  var n = 0;
  for (var i = 0; i < records.length; i++) if (!predicate || predicate(records[i])) n++;
  return n;
}
