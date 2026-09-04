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
    return rec.eventId || true;
  });
}

function api_deleteEvent(id) {
  return safeCall_(function () { return deleteRecordById(SHEETS.EVENTS, id); });
}
