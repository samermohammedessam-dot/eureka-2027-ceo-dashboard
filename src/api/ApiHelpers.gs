/**
 * Shared helpers for the client-facing API layer (functions called via google.script.run).
 * Every function the frontend can call is prefixed `api_` by convention so it's obvious
 * from the file which functions form the public contract with ui/JS_App.html.
 */

// Sheets the generic CRUD API is allowed to touch. Whitelisted deliberately — the frontend
// passes a sheet name as a string, so this stops any arbitrary sheet from being written to.
// Built lazily (not a top-level array literal) so it never depends on file load order —
// safe even if this file's code is pasted/merged ahead of the file that defines SHEETS.
function genericCrudSheets_() {
  return [
    SHEETS.TARGET_ACCOUNTS, SHEETS.PARTNERSHIPS, SHEETS.ACADEMY, SHEETS.CASE_STUDIES,
    SHEETS.DIGITAL_ROADMAP, SHEETS.DECISIONS, SHEETS.RISKS, SHEETS.PROJECTS, SHEETS.CLIENTS,
    SHEETS.TEAM, SHEETS.MARKETS, SHEETS.BUSINESS_UNITS
  ];
}

function assertGenericSheetAllowed_(sheetName) {
  if (genericCrudSheets_().indexOf(sheetName) === -1) {
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
