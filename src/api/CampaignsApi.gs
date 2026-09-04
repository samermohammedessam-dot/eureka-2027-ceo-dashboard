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
    return rec.campaignId || true;
  });
}

function api_deleteCampaign(id) {
  return safeCall_(function () { return deleteRecordById(SHEETS.CAMPAIGNS, id); });
}
