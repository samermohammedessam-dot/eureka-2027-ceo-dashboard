function api_getCampaigns(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.CAMPAIGNS).map(stripRowMeta_), filters);
  });
}

function api_saveCampaign(rec) {
  return safeCall_(function () {
    if (rec.campaignId) {
      updateRecordById(SHEETS.CAMPAIGNS, rec.campaignId, rec);
    } else {
      appendRecord(SHEETS.CAMPAIGNS, rec);
    }
    recomputeCampaigns_();
    invalidateDashboardCache_();
    invalidateLookupsCache_(); // campaign names feed the Campaign dropdown in api_getLookups
    return rec.campaignId || true;
  });
}

function api_deleteCampaign(id) {
  return safeCall_(function () {
    var result = deleteRecordById(SHEETS.CAMPAIGNS, id);
    invalidateDashboardCache_();
    invalidateLookupsCache_();
    return result;
  });
}
