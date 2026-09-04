/** Market performance: target vs actual revenue, pipeline, spend — powers Markets view + heatmap. */
function api_getMarketsPerformance() {
  return safeCall_(function () {
    var markets = readAllRecords(SHEETS.MARKETS).map(stripRowMeta_);
    var revenue = readAllRecords(SHEETS.REVENUE);
    var pipeline = readAllRecords(SHEETS.PIPELINE).filter(function (r) { return r.stage !== 'Won' && r.stage !== 'Lost'; });
    var expenses = readAllRecords(SHEETS.EXPENSES);

    return markets.map(function (m) {
      var revenueActual = sumBy(revenue, 'revenueRecognized', function (r) { return r.market === m.market; });
      var bookings = sumBy(revenue, 'contractValue', function (r) { return r.market === m.market; });
      var pipelineValue = sumBy(pipeline, 'estimatedOpportunityValue', function (r) { return r.market === m.market; });
      var spend = sumBy(expenses, 'actualAmount', function (r) { return r.market === m.market; });
      var achievementPct = m.revenueTarget2027 ? revenueActual / m.revenueTarget2027 : null;
      return {
        market: m.market, country: m.country, revenueTarget: m.revenueTarget2027, revenueActual: revenueActual,
        achievementPct: achievementPct, bookings: bookings, pipelineValue: pipelineValue, spend: spend,
        owner: m.owner, status: m.status,
        health: achievementPct === null ? 'N/A' : (achievementPct >= ALERT_REVENUE_ACHIEVEMENT_FLOOR ? 'GREEN' : (achievementPct >= 0.5 ? 'YELLOW' : 'RED'))
      };
    });
  });
}
