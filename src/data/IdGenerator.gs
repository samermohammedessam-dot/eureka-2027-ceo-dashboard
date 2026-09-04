/**
 * Sequential, human-readable ID generation (e.g. TSK-0001, REV-0037).
 * Scans the existing ID column once per call — fine at this data volume (hundreds to a few
 * thousand rows per sheet) and keeps IDs short and sortable, unlike UUIDs.
 */
function generateId(sheetName, prefix) {
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
  var next = max + 1;
  var padded = ('0000' + next).slice(-4);
  return prefix + '-' + padded;
}
