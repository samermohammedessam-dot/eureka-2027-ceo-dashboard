/**
 * Sequential, human-readable ID generation (e.g. TSK-0001, REV-0037).
 * Scans the existing ID column once per call — fine at this data volume (hundreds to a few
 * thousand rows per sheet) and keeps IDs short and sortable, unlike UUIDs.
 *
 * IMPORTANT: this scans the SHEET as it currently stands. A caller that needs several new
 * IDs in a row (see bulkAppendRecords in SheetService.gs) must NOT call this once per record
 * before anything has been written — every call would see the same unchanged sheet and
 * return the same "next" ID. Use nextIdSequenceStart_() once, then increment in memory,
 * for that case instead.
 */
function generateId(sheetName, prefix) {
  return prefix + '-' + padId_(nextIdSequenceStart_(sheetName, prefix));
}

/** Returns the next free sequence number (not yet formatted/prefixed) for a sheet's ID column. */
function nextIdSequenceStart_(sheetName, prefix) {
  var sheet = ss_().getSheetByName(sheetName);
  var schema = getSchema(sheetName);
  var idCol = schema.filter(function (c) { return c.idPrefix; })[0];
  var max = 0;
  if (sheet && idCol) {
    var idColIndex = schema.indexOf(idCol);
    var lastRow = sheet.getLastRow();
    if (lastRow >= 2) {
      var ids = sheet.getRange(2, idColIndex + 1, lastRow - 1, 1).getValues();
      for (var i = 0; i < ids.length; i++) {
        var m = String(ids[i][0]).match(new RegExp('^' + prefix + '-(\\d+)$'));
        if (m) max = Math.max(max, parseInt(m[1], 10));
      }
    }
  }
  return max + 1;
}

function padId_(n) {
  return ('0000' + n).slice(-4);
}
