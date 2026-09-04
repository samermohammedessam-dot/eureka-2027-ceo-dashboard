function api_getPipeline(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.PIPELINE).map(stripRowMeta_), filters);
  });
}

function api_savePipeline(rec) {
  return safeCall_(function () {
    if (rec.opportunityId) {
      updateRecordById(SHEETS.PIPELINE, rec.opportunityId, rec);
    } else {
      rec.stage = rec.stage || 'Target Account';
      appendRecord(SHEETS.PIPELINE, rec);
    }
    recomputePipeline_();
    return rec.opportunityId || true;
  });
}

function api_deletePipeline(id) {
  return safeCall_(function () { return deleteRecordById(SHEETS.PIPELINE, id); });
}

/** Section 11: pipeline value, weighted pipeline, win rate, cycle, average deal, coverage, breakdowns. */
function api_getPipelineSummary() {
  return safeCall_(function () {
    var records = readAllRecords(SHEETS.PIPELINE);
    var open = records.filter(function (r) { return r.stage !== 'Won' && r.stage !== 'Lost'; });
    var won = records.filter(function (r) { return r.stage === 'Won'; });
    var lost = records.filter(function (r) { return r.stage === 'Lost'; });
    var totalPipeline = sumBy(open, 'estimatedOpportunityValue');
    var weightedPipeline = sumBy(open, 'weightedValue');
    var winRate = (won.length + lost.length) ? won.length / (won.length + lost.length) : 0;
    var avgDeal = won.length ? sumBy(won, 'estimatedOpportunityValue') / won.length : 0;
    var cycles = won.filter(function (r) { return r.firstContactDate; })
      .map(function (r) { return daysBetween_(r.firstContactDate, r.expectedCloseDate || r.lastContactDate); });
    var avgCycle = cycles.length ? Math.round(cycles.reduce(function (a, b) { return a + b; }, 0) / cycles.length) : null;
    return {
      totalPipeline: totalPipeline, weightedPipeline: weightedPipeline,
      coverage: REVENUE_TARGET ? totalPipeline / REVENUE_TARGET : 0,
      coverageTarget: PIPELINE_COVERAGE_TARGET, coverageAlertFloor: PIPELINE_COVERAGE_ALERT_FLOOR,
      winRate: winRate, avgDealSize: avgDeal, avgSalesCycleDays: avgCycle,
      byMarket: groupSum_(open, 'market', 'estimatedOpportunityValue'),
      byBusinessUnit: groupSum_(open, 'businessUnit', 'estimatedOpportunityValue'),
      byBdOwner: groupSum_(open, 'bdOwner', 'estimatedOpportunityValue'),
      byStage: groupSum_(open, 'stage', 'estimatedOpportunityValue'),
      wonCount: won.length, lostCount: lost.length
    };
  });
}
