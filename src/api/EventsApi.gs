function api_getEvents(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.EVENTS).map(stripRowMeta_), filters);
  });
}

function api_saveEvent(rec) {
  return safeCall_(function () {
    if (rec.eventId) {
      updateRecordById(SHEETS.EVENTS, rec.eventId, rec);
    } else {
      appendRecord(SHEETS.EVENTS, rec);
    }
    recomputeEvents_();
    invalidateDashboardCache_();
    invalidateLookupsCache_(); // event names feed the Event dropdown in api_getLookups
    return rec.eventId || true;
  });
}

function api_deleteEvent(id) {
  return safeCall_(function () {
    var result = deleteRecordById(SHEETS.EVENTS, id);
    invalidateDashboardCache_();
    invalidateLookupsCache_();
    return result;
  });
}
