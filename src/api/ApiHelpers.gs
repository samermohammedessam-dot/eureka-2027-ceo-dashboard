/**
 * Shared helpers for the client-facing API layer (functions called via google.script.run).
 * Every function the frontend can call is prefixed `api_` by convention so it's obvious
 * from the file which functions form the public contract with ui/JS_App.html.
 */

// Sheets the generic CRUD API is allowed to touch. Whitelisted deliberately — the frontend
// passes a sheet name as a string, so this stops any arbitrary sheet from being written to.
var GENERIC_CRUD_SHEETS = [
  SHEETS.TARGET_ACCOUNTS, SHEETS.PARTNERSHIPS, SHEETS.ACADEMY, SHEETS.CASE_STUDIES,
  SHEETS.DIGITAL_ROADMAP, SHEETS.DECISIONS, SHEETS.RISKS, SHEETS.PROJECTS, SHEETS.CLIENTS,
  SHEETS.TEAM, SHEETS.MARKETS, SHEETS.BUSINESS_UNITS
];

function assertGenericSheetAllowed_(sheetName) {
  if (GENERIC_CRUD_SHEETS.indexOf(sheetName) === -1) {
    throw new Error('Sheet not permitted for generic CRUD: ' + sheetName);
  }
}

function stripRowMeta_(record) {
  var clean = {};
  for (var k in record) if (k !== '_row') clean[k] = record[k];
  return clean;
}

function applyFilters_(records, filters) {
  if (!filters) return records;
  return records.filter(function (r) {
    for (var key in filters) {
      var val = filters[key];
      if (val === undefined || val === null || val === '') continue;
      if (key === '_search') continue;
      if (String(r[key]) !== String(val)) return false;
    }
    if (filters._search) {
      var needle = String(filters._search).toLowerCase();
      var hay = JSON.stringify(r).toLowerCase();
      if (hay.indexOf(needle) === -1) return false;
    }
    return true;
  });
}

function safeCall_(fn) {
  try {
    return { ok: true, data: fn() };
  } catch (err) {
    Logger.log('API error: ' + err + '\n' + (err && err.stack));
    return { ok: false, error: String(err && err.message || err) };
  }
}
