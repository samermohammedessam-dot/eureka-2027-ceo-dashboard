/**
 * Shared helpers for the client-facing API layer (functions called via google.script.run).
 * Every function the frontend can call is prefixed `api_` by convention so it's obvious
 * from the file which functions form the public contract with the frontend (src/ui/*.html,
 * or JavaScript.html in the manual-deploy copy).
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

// Pagination controls, not filter criteria — applyFilters_ must never try to match a record
// field against these (no record has a "page" or "pageSize" column, so a naive filter would
// discard every row). See paginate_() in this file.
var PAGINATION_KEYS_ = { page: true, pageSize: true };

function applyFilters_(records, filters) {
  if (!filters) return records;
  return records.filter(function (r) {
    for (var key in filters) {
      var val = filters[key];
      if (val === undefined || val === null || val === '') continue;
      if (key === '_search' || PAGINATION_KEYS_[key]) continue;
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

/**
 * Performance Sprint instrumentation: writes a timing line to the execution log (visible in
 * the Apps Script editor's Executions view) so slow phases can be identified from real runs.
 * Deliberately just Logger.log — no sheet writes, no state — safe to leave in permanently.
 */
function logTiming_(label, ms) {
  Logger.log('[perf] ' + label + ': ' + ms + 'ms');
}

/**
 * Opt-in server-side pagination: only slices when the caller actually asks for a page (see
 * each api_get* that supports it) — omit `page` entirely and you get the old plain-array
 * behavior, so existing narrow/filtered call sites (e.g. "tasks for this one week") are
 * completely unaffected.
 */
function paginate_(records, filters) {
  var page = Math.max(1, parseInt((filters && filters.page) || 1, 10) || 1);
  var pageSize = Math.min(MAX_PAGE_SIZE, Math.max(1, parseInt((filters && filters.pageSize) || DEFAULT_PAGE_SIZE, 10) || DEFAULT_PAGE_SIZE));
  var total = records.length;
  var start = (page - 1) * pageSize;
  return {
    records: records.slice(start, start + pageSize),
    total: total,
    page: page,
    pageSize: pageSize,
    totalPages: Math.max(1, Math.ceil(total / pageSize))
  };
}
