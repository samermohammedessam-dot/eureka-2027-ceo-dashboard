
// ============================================================
// SOURCE: setup/SetupSheets.gs
// ============================================================

/**
 * Creates every tab defined in SHEET_ORDER, writes its header row, freezes it,
 * and applies basic formatting (bold header, filter, column widths).
 * Safe to re-run: it will not wipe existing data rows, only rewrite headers/formatting.
 */
function runSetupSheets() {
  var spreadsheet = ss_();

  SHEET_ORDER.forEach(function (name) {
    var sheet = getOrCreateSheet(name);
    var headers = getHeaders(name);
    if (headers.length > 0) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      sheet.setFrozenRows(1);
      var headerRange = sheet.getRange(1, 1, 1, headers.length);
      headerRange.setFontWeight('bold')
        .setBackground('#1a2b4c')
        .setFontColor('#ffffff')
        .setVerticalAlignment('middle');
      sheet.setRowHeight(1, 32);
      if (sheet.getFilter()) sheet.getFilter().remove();
      if (sheet.getLastRow() >= 1 && sheet.getLastColumn() >= 1) {
        sheet.getRange(1, 1, Math.max(sheet.getLastRow(), 1), headers.length).createFilter();
      }
      for (var c = 1; c <= headers.length; c++) sheet.autoResizeColumn(c);
      sheet.setTabColor(null);
    }
  });

  buildSettingsSheet_();
  buildMasterDataSheet_();
  buildCeoDashboardSheetShell_();
  buildWeeklyCeoSheetShell_();

  // Reorder tabs to match SHEET_ORDER exactly.
  SHEET_ORDER.forEach(function (name, index) {
    var sheet = spreadsheet.getSheetByName(name);
    if (sheet) spreadsheet.setActiveSheet(sheet), spreadsheet.moveActiveSheet(index + 1);
  });
  spreadsheet.setActiveSheet(spreadsheet.getSheetByName(SHEETS.CEO_DASHBOARD));

  SpreadsheetApp.flush();
  return 'Sheet structure created: ' + SHEET_ORDER.length + ' tabs.';
}

function buildSettingsSheet_() {
  var sheet = getOrCreateSheet(SHEETS.SETTINGS);
  sheet.clear();
  var rows = [
    ['Setting', 'Value', 'Notes'],
    ['Company Name', 'Eureka Healthcare Development Experts', ''],
    ['Fiscal Year', FISCAL_YEAR, ''],
    ['Positioning', 'Strategy. Transformation. Operational Excellence.', ''],
    ['Revenue — Minimum', REVENUE_MIN, 'EGP'],
    ['Revenue — Operating Target', REVENUE_TARGET, 'EGP'],
    ['Revenue — Stretch', REVENUE_STRETCH, 'EGP'],
    ['Annual Sales Bookings Target', ANNUAL_BOOKINGS_TARGET, 'EGP'],
    ['Minimum Qualified Pipeline', PIPELINE_MIN, 'EGP'],
    ['Maximum Qualified Pipeline', PIPELINE_MAX, 'EGP'],
    ['Pipeline Coverage Target (x Revenue)', PIPELINE_COVERAGE_TARGET, ''],
    ['Pipeline Coverage Alert Floor (x Revenue)', PIPELINE_COVERAGE_ALERT_FLOOR, 'Below this = RED ALERT'],
    ['Revenue Achievement Alert Floor', ALERT_REVENUE_ACHIEVEMENT_FLOOR, '% of target, below = RED ALERT'],
    ['Receivable Overdue Alert (days)', ALERT_RECEIVABLE_OVERDUE_DAYS, ''],
    ['Inactive Opportunity Alert (days)', ALERT_INACTIVE_OPPORTUNITY_DAYS, ''],
    ['Web App URL', '', 'Paste after first deployment'],
    ['Last Setup Run', new Date(), '']
  ];
  sheet.getRange(1, 1, rows.length, 3).setValues(rows);
  sheet.getRange(1, 1, 1, 3).setFontWeight('bold').setBackground('#1a2b4c').setFontColor('#ffffff');
  sheet.setFrozenRows(1);
  sheet.setColumnWidth(1, 260);
  sheet.setColumnWidth(2, 220);
  sheet.setColumnWidth(3, 320);
}

/** 26_Master_Data holds every dropdown list as its own column, used both by Apps Script and by sheet-native data validation. */
function buildMasterDataSheet_() {
  var sheet = getOrCreateSheet(SHEETS.MASTER_DATA);
  sheet.clear();
  var lists = getMasterLists_();
  var maxLen = 0;
  var keys = Object.keys(lists);
  keys.forEach(function (k) { maxLen = Math.max(maxLen, lists[k].length); });
  var header = keys;
  var grid = [header];
  for (var r = 0; r < maxLen; r++) {
    var row = keys.map(function (k) { return lists[k][r] !== undefined ? lists[k][r] : ''; });
    grid.push(row);
  }
  sheet.getRange(1, 1, grid.length, header.length).setValues(grid);
  sheet.getRange(1, 1, 1, header.length).setFontWeight('bold').setBackground('#1a2b4c').setFontColor('#ffffff');
  sheet.setFrozenRows(1);
  for (var c = 1; c <= header.length; c++) sheet.autoResizeColumn(c);
}

function getMasterLists_() {
  return {
    TASK_STATUS: TASK_STATUS,
    TASK_PRIORITY: TASK_PRIORITY,
    TASK_CATEGORIES: TASK_CATEGORIES,
    EXPENSE_CATEGORIES: EXPENSE_CATEGORIES,
    PAYMENT_STATUS: PAYMENT_STATUS,
    PAYMENT_METHODS: PAYMENT_METHODS,
    COLLECTION_STATUS: COLLECTION_STATUS,
    SALES_STAGES: SALES_STAGES.map(function (s) { return s.name; }),
    CAMPAIGN_TYPES: CAMPAIGN_TYPES,
    EVENT_TYPES: EVENT_TYPES,
    ACCOUNT_TIERS: ACCOUNT_TIERS,
    RISK_CATEGORIES: RISK_CATEGORIES,
    RISK_STATUS: RISK_STATUS,
    DECISION_STATUS: DECISION_STATUS,
    COUNTRIES: COUNTRIES,
    KPI_CATEGORIES: ['Financial', 'Commercial', 'Marketing', 'Delivery', 'Strategic']
  };
}

/** Dashboard sheet is mostly a live-formula "at a glance" surface for anyone opening the raw Sheet directly. */
function buildCeoDashboardSheetShell_() {
  var sheet = getOrCreateSheet(SHEETS.CEO_DASHBOARD);
  sheet.clear();
  sheet.getRange('A1').setValue('EUREKA 2027 — CEO DASHBOARD (open the web app for the full interactive experience)')
    .setFontWeight('bold').setFontSize(14);
  sheet.getRange('A1:F1').merge();
  sheet.setColumnWidths(1, 6, 200);
  sheet.setFrozenRows(3);
  var labels = [
    ['', '', '', '', '', ''],
    ['Metric', 'Value', '', 'Metric', 'Value', ''],
    ['2027 Revenue Target', '', '', 'Total Pipeline', ''],
    ['Revenue Actual (Recognized)', '', '', 'Weighted Pipeline', ''],
    ['Revenue Achievement %', '', '', 'Pipeline Coverage (x)', ''],
    ['Annual Bookings Target', '', '', 'Cash Collected', ''],
    ['Bookings Actual', '', '', 'Outstanding Receivables', ''],
    ['Growth Budget', '', '', 'Win Rate', ''],
    ['Actual Growth Spend', '', '', 'Deals Won (YTD)', ''],
    ['Budget Variance', '', '', 'Tasks Completion %', '']
  ];
  sheet.getRange(2, 1, labels.length, 6).setValues(labels);
  sheet.getRange(2, 1, 1, 6).setFontWeight('bold');
  sheet.getRange(3, 1, 8, 1).setFontWeight('bold');
  sheet.getRange(3, 4, 8, 1).setFontWeight('bold');
  sheet.getRange('A13').setValue('This sheet is refreshed by Eureka 2027 menu → "Refresh dashboard formulas". Live drill-down, charts and weekly review are in the web app.').setFontStyle('italic');
}

function buildWeeklyCeoSheetShell_() {
  var sheet = getOrCreateSheet(SHEETS.WEEKLY_CEO);
  sheet.clear();
  sheet.getRange('A1').setValue('WEEKLY CEO REVIEW (current week, auto-detected from today\'s date)')
    .setFontWeight('bold').setFontSize(14);
  sheet.getRange('A1:D1').merge();
  var labels = [
    ['', '', '', ''],
    ['This Week Metric', 'Value', 'End of Week Metric', 'Value'],
    ['Current Week ID', '', 'Tasks Planned', ''],
    ['Sales Target', '', 'Tasks Completed', ''],
    ['Expected Collections', '', 'Completion %', ''],
    ['Critical Tasks', '', 'Tasks Overdue', ''],
    ['Blocked Tasks', '', 'Spend This Week', ''],
    ['Overdue Tasks', '', 'Revenue Collected', ''],
    ['Budget Planned This Week', '', 'Bookings', '']
  ];
  sheet.getRange(2, 1, labels.length, 4).setValues(labels);
  sheet.getRange(2, 1, 1, 4).setFontWeight('bold');
  sheet.getRange(3, 1, 7, 1).setFontWeight('bold');
  sheet.getRange(3, 3, 7, 1).setFontWeight('bold');
  sheet.setColumnWidths(1, 4, 220);
}

// ============================================================
// SOURCE: setup/SetupValidation.gs
// ============================================================

/**
 * Applies data validation, number/date formats, conditional formatting (traffic lights),
 * and protects computed columns from manual edits.
 * Reads validation rules straight from SHEET_SCHEMA — never hardcodes a column letter.
 */
function runSetupValidation() {
  SHEET_ORDER.forEach(function (name) {
    var schema = getSchema(name);
    if (!schema.length) return;
    var sheet = ss_().getSheetByName(name);
    if (!sheet) return;
    var maxRows = Math.max(sheet.getMaxRows(), 500);
    if (sheet.getMaxRows() < maxRows) sheet.insertRowsAfter(sheet.getMaxRows(), maxRows - sheet.getMaxRows());

    schema.forEach(function (colDef, i) {
      var colIndex = i + 1;
      var range = sheet.getRange(2, colIndex, maxRows - 1, 1);

      if (colDef.type === 'currency') {
        range.setNumberFormat('#,##0 "EGP"');
      } else if (colDef.type === 'percent') {
        range.setNumberFormat('0%');
      } else if (colDef.type === 'date') {
        range.setNumberFormat('yyyy-mm-dd');
      } else if (colDef.type === 'boolean') {
        range.insertCheckboxes();
      }

      if (colDef.validation) {
        var rule = buildValidationRule_(colDef.validation);
        if (rule) range.setDataValidation(rule);
      }

      if (colDef.computed) {
        range.setFontColor('#888888').setFontStyle('italic');
      }
    });

    applyTrafficLightFormatting_(sheet, schema, name);
  });

  protectComputedColumns_();
  return 'Validation, formatting and protection applied.';
}

function buildValidationRule_(validation) {
  if (validation.indexOf('sheet:') === 0) {
    var parts = validation.split(':'); // sheet:<SheetName>:<key>
    var sourceSheetName = parts[1];
    var sourceKey = parts[2];
    var sourceSchema = getSchema(sourceSheetName);
    var sourceColIndex = sourceSchema.map(function (c) { return c.key; }).indexOf(sourceKey);
    if (sourceColIndex === -1) return null;
    var sourceSheet = ss_().getSheetByName(sourceSheetName);
    if (!sourceSheet) return null;
    var sourceRange = sourceSheet.getRange(2, sourceColIndex + 1, Math.max(sourceSheet.getMaxRows() - 1, 1), 1);
    return SpreadsheetApp.newDataValidation().requireValueInRange(sourceRange, true).setAllowInvalid(true).build();
  }
  var lists = getMasterLists_();
  var list = lists[validation];
  if (!list) return null;
  return SpreadsheetApp.newDataValidation().requireValueInList(list, true).setAllowInvalid(true).build();
}

/** Conditional formatting: RED/YELLOW/GREEN traffic lights on Status/Priority-driven sheets. */
function applyTrafficLightFormatting_(sheet, schema, sheetName) {
  var rules = sheet.getConditionalFormatRules().filter(function (r) {
    return r.getRanges().every(function (rg) { return rg.getSheet().getName() !== sheet.getName(); });
  });

  if (sheetName === SHEETS.TASKS) {
    var statusColIndex = schema.map(function (c) { return c.key; }).indexOf('status') + 1;
    var range = sheet.getRange(2, statusColIndex, Math.max(sheet.getMaxRows() - 1, 1), 1);
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Blocked').setBackground('#f8d7da').setFontColor('#842029').setRanges([range]).build());
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Waiting').setBackground('#fff3cd').setFontColor('#664d03').setRanges([range]).build());
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Completed').setBackground('#d1e7dd').setFontColor('#0f5132').setRanges([range]).build());
    var priorityColIndex = schema.map(function (c) { return c.key; }).indexOf('priority') + 1;
    var priorityRange = sheet.getRange(2, priorityColIndex, Math.max(sheet.getMaxRows() - 1, 1), 1);
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Critical').setBackground('#f8d7da').setFontColor('#842029').setBold(true).setRanges([priorityRange]).build());
  }

  if (sheetName === SHEETS.PIPELINE) {
    var stageColIndex = schema.map(function (c) { return c.key; }).indexOf('stage') + 1;
    var stageRange = sheet.getRange(2, stageColIndex, Math.max(sheet.getMaxRows() - 1, 1), 1);
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Won').setBackground('#d1e7dd').setFontColor('#0f5132').setRanges([stageRange]).build());
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Lost').setBackground('#f8d7da').setFontColor('#842029').setRanges([stageRange]).build());
  }

  if (sheetName === SHEETS.EXPENSES) {
    var varianceColIndex = schema.map(function (c) { return c.key; }).indexOf('variance') + 1;
    var varianceRange = sheet.getRange(2, varianceColIndex, Math.max(sheet.getMaxRows() - 1, 1), 1);
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenNumberLessThan(0).setBackground('#f8d7da').setFontColor('#842029').setRanges([varianceRange]).build());
  }

  if (sheetName === SHEETS.REVENUE) {
    var collStatusColIndex = schema.map(function (c) { return c.key; }).indexOf('collectionStatus') + 1;
    var collRange = sheet.getRange(2, collStatusColIndex, Math.max(sheet.getMaxRows() - 1, 1), 1);
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Overdue').setBackground('#f8d7da').setFontColor('#842029').setRanges([collRange]).build());
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Collected').setBackground('#d1e7dd').setFontColor('#0f5132').setRanges([collRange]).build());
  }

  if (sheetName === SHEETS.RISKS) {
    var scoreColIndex = schema.map(function (c) { return c.key; }).indexOf('riskScore') + 1;
    var scoreRange = sheet.getRange(2, scoreColIndex, Math.max(sheet.getMaxRows() - 1, 1), 1);
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenNumberGreaterThanOrEqualTo(15).setBackground('#f8d7da').setFontColor('#842029').setRanges([scoreRange]).build());
    rules.push(SpreadsheetApp.newConditionalFormatRule().whenNumberBetween(8, 14).setBackground('#fff3cd').setFontColor('#664d03').setRanges([scoreRange]).build());
  }

  sheet.setConditionalFormatRules(rules);
}

/** Protects computed columns so users can't overwrite formula-maintained values (warns, doesn't hard-block owner). */
function protectComputedColumns_() {
  SHEET_ORDER.forEach(function (name) {
    var schema = getSchema(name);
    var computedCols = schema.filter(function (c) { return c.computed; });
    if (!computedCols.length) return;
    var sheet = ss_().getSheetByName(name);
    if (!sheet) return;
    var existing = sheet.getProtections(SpreadsheetApp.ProtectionType.RANGE);
    existing.forEach(function (p) { if (p.getDescription() === 'Eureka computed column') p.remove(); });
    computedCols.forEach(function (c) {
      var colIndex = schema.indexOf(c) + 1;
      var range = sheet.getRange(2, colIndex, Math.max(sheet.getMaxRows() - 1, 1), 1);
      var protection = range.protect().setDescription('Eureka computed column');
      protection.setWarningOnly(true);
    });
  });
}

// ============================================================
// SOURCE: setup/SeedData.gs
// ============================================================

/**
 * Seeds master/reference data and the 2027 strategy skeleton directly from the business
 * plan (Sections 1, 3, 4, 5, 6, 7, 12, 13, 17 of the brief). Transactional sheets
 * (Revenue, Expenses, Pipeline, Projects, Clients, Target Accounts) are intentionally left
 * EMPTY of fabricated numbers — those must reflect real activity as the year runs.
 * Safe to re-run: each seeder clears its own sheet's data rows before rewriting.
 */

function runSeedAll() {
  seedBusinessUnits_();
  seedTeam_();
  seedMarkets_();
  seedMasterPlan_();
  seedCampaigns_();
  seedEvents_();
  seedKpis_();
  seedQuarterlyReview_();
  seedDigitalRoadmap_();
  seedWeeklyExecutionAndTasks(); // src/setup/SeedWeekly.gs
  SpreadsheetApp.flush();
  return 'Seed complete: business units, team, markets, master plan, campaigns, events, KPIs, quarterly gates, digital roadmap, 52 weeks + strategy tasks.';
}

function clearDataRows_(sheetName) {
  var sheet = ss_().getSheetByName(sheetName);
  if (!sheet) return;
  var last = sheet.getLastRow();
  if (last > 1) sheet.getRange(2, 1, last - 1, sheet.getLastColumn()).clearContent();
}

function seedBusinessUnits_() {
  clearDataRows_(SHEETS.BUSINESS_UNITS);
  var bus = [
    ['Eureka Accreditation & Excellence', ['GAHAR', 'CBAHI', 'OHAS', 'JCI Readiness', 'ISO', 'TEMOS', 'Quality Management', 'Patient Safety', 'Clinical Governance']],
    ['Eureka Healthcare Transformation', ['Strategy', 'Governance', 'Organizational Development', 'HR Transformation', 'Performance Management', 'Culture Transformation']],
    ['Eureka Operations', ['Hospital Operations', 'KPI Systems', 'Revenue Cycle', 'Financial Performance', 'Patient Flow', 'Supply Chain', 'Hospital Management Systems', 'Turnaround Management']],
    ['Eureka Healthcare Development', ['Feasibility Studies', 'Healthcare Investment Advisory', 'New Facility Setup', 'Hospital Commissioning', 'Business Planning', 'Healthcare Development']],
    ['Eureka Academy', ['Healthcare Leadership', 'Quality Leadership', 'Hospital Operations', 'Healthcare Finance', 'Clinical Governance', 'Patient Experience', 'Executive Education', 'Corporate Training Contracts']],
    ['Eureka Digital', ['Accreditation Dashboard', 'Evidence Management', 'Action Plans', 'Audit Management', 'KPI Tracking', 'Training Compliance', 'Document Control', 'Executive Dashboards']]
  ];
  var records = [];
  bus.forEach(function (bu) {
    bu[1].forEach(function (service) {
      records.push({ businessUnit: bu[0], service: service, description: '' });
    });
  });
  bulkAppendRecords(SHEETS.BUSINESS_UNITS, records);
}

function seedTeam_() {
  clearDataRows_(SHEETS.TEAM);
  var records = [
    { name: 'CEO', email: '', role: 'CEO', responsibilities: 'Strategic accounts; major proposals; investor relationships; international partnerships; Saudi and Libya anchor clients; thought leadership; strategic alliances', marketsOwned: 'Saudi Arabia, Libya (anchor accounts)', active: true },
    { name: 'Commercial Director', email: '', role: 'Commercial Director / Head of Growth', responsibilities: 'Revenue, pipeline, proposal conversion, commercial forecasting, CRM, BD team', marketsOwned: 'All (commercial oversight)', active: true },
    { name: 'Egypt BD Manager', email: '', role: 'Egypt BD Manager', responsibilities: 'Cairo, Sheikh Zayed, Damietta, Matrouh, Upper Egypt', marketsOwned: 'Cairo, Sheikh Zayed, Damietta, Matrouh, Upper Egypt', active: true },
    { name: 'International BD & Partnerships Manager', email: '', role: 'International BD & Partnerships Manager', responsibilities: 'Saudi Arabia, Libya, Oman, UAE, international partners', marketsOwned: 'Saudi Arabia, Libya, Oman, UAE', active: true },
    { name: 'Marketing & Brand Lead', email: '', role: 'Marketing & Brand Lead', responsibilities: 'Content, campaigns, website, case studies, events, PR, lead generation support', marketsOwned: 'All', active: true },
    { name: 'Performance Marketing', email: '', role: 'Performance Marketing', responsibilities: 'Google Ads, LinkedIn campaigns, lead tracking, remarketing, cost per lead', marketsOwned: 'All', active: true },
    { name: 'PMO / Delivery Director', email: '', role: 'PMO / Delivery Director', responsibilities: 'Project delivery, timelines, consultant utilization, client reporting, profitability, scope management, NPS', marketsOwned: 'All', active: true },
    { name: 'Finance', email: '', role: 'Finance', responsibilities: 'Revenue, invoices, collections, expenses, gross margins, DSO, receivables, project profitability', marketsOwned: 'All', active: true }
  ];
  bulkAppendRecords(SHEETS.TEAM, records);
}

function seedMarkets_() {
  clearDataRows_(SHEETS.MARKETS);
  var records = [
    { market: 'Cairo', country: 'Egypt', revenueTarget2027: 2800000, owner: 'Egypt BD Manager', status: 'Active', launchMonth: 'February' },
    { market: 'Saudi Arabia', country: 'Saudi Arabia', revenueTarget2027: 2000000, owner: 'International BD & Partnerships Manager', status: 'Pipeline Creation', launchMonth: 'May' },
    { market: 'Libya', country: 'Libya', revenueTarget2027: 1800000, owner: 'International BD & Partnerships Manager', status: 'Market Entry', launchMonth: 'April' },
    { market: 'Upper Egypt', country: 'Egypt', revenueTarget2027: 1500000, owner: 'Egypt BD Manager', status: 'Market Entry', launchMonth: 'March' },
    { market: 'UAE', country: 'UAE', revenueTarget2027: 1000000, owner: 'International BD & Partnerships Manager', status: 'Regional Launch', launchMonth: 'January' },
    { market: 'Sheikh Zayed', country: 'Egypt', revenueTarget2027: 900000, owner: 'Egypt BD Manager', status: 'Active', launchMonth: 'February' },
    { market: 'Oman', country: 'Oman', revenueTarget2027: 900000, owner: 'International BD & Partnerships Manager', status: 'Market Creation', launchMonth: 'September' },
    { market: 'Damietta', country: 'Egypt', revenueTarget2027: 700000, owner: 'Egypt BD Manager', status: 'Expansion', launchMonth: 'June' },
    { market: 'Matrouh', country: 'Egypt', revenueTarget2027: 700000, owner: 'Egypt BD Manager', status: 'Expansion', launchMonth: 'June' },
    { market: 'Academy / Digital Standalone', country: 'Egypt', revenueTarget2027: 400000, owner: 'Marketing & Brand Lead', status: 'Active', launchMonth: 'July' },
    { market: 'Alexandria (Existing Base)', country: 'Egypt', revenueTarget2027: 0, owner: 'Egypt BD Manager', status: 'Active — Existing Base', launchMonth: 'January' },
    { market: 'Minya', country: 'Egypt', revenueTarget2027: 0, owner: 'Egypt BD Manager', status: 'Upper Egypt sub-market', launchMonth: 'March' },
    { market: 'Assiut', country: 'Egypt', revenueTarget2027: 0, owner: 'Egypt BD Manager', status: 'Upper Egypt sub-market', launchMonth: 'March' },
    { market: 'Sohag', country: 'Egypt', revenueTarget2027: 0, owner: 'Egypt BD Manager', status: 'Upper Egypt sub-market', launchMonth: 'Future' },
    { market: 'Aswan', country: 'Egypt', revenueTarget2027: 0, owner: 'Egypt BD Manager', status: 'Upper Egypt sub-market', launchMonth: 'Future' }
  ];
  bulkAppendRecords(SHEETS.MARKETS, records);
}

/** Section 6 + 7: the full monthly execution strategy and financial plan, merged into one row per month. */
function getMonthlyStrategyPlan_() {
  return [
    { month: 'January', theme: 'REGIONAL LAUNCH', primaryMarket: 'UAE + GCC', campaign: 'Eureka Goes Regional', eventName: 'WHX Dubai', sales: 900000, revenue: 500000, budget: 200000, owner: 'CEO + International BD + Marketing',
      kpis: '20 pre-booked meetings; 8 qualified opportunities; 4 proposals; EGP 3M new pipeline; 2 potential partners; 1 GCC deal reaching negotiation',
      actions: ['Build UAE/GCC target account database', 'Pre-book GCC meetings for WHX Dubai', 'Prepare international capability statement', 'Finalize Saudi deck', 'Finalize UAE deck', 'Finalize Oman OHAS deck', 'Compile international case studies'] },
    { month: 'February', theme: 'OWN CAIRO & SHEIKH ZAYED', primaryMarket: 'Cairo + Sheikh Zayed', campaign: 'Beyond Accreditation', eventName: 'Eureka Healthcare Executive Breakfast — Sheikh Zayed', sales: 1000000, revenue: 600000, budget: 120000, owner: 'Commercial Director + Egypt BD + CEO',
      kpis: '30 target accounts; 10 CEO meetings; 5 diagnostics; 4 proposals; 2 wins; EGP 2.5M added pipeline',
      actions: ['Build 30 target account list — Cairo & Sheikh Zayed', 'Launch Healthcare Transformation Diagnostic product', 'Book 10 CEO-level meetings', 'Run 5 diagnostics', 'Host Executive Breakfast event'] },
    { month: 'March', theme: 'UPPER EGYPT ENTRY', primaryMarket: 'Minya + Assiut', campaign: 'Ready for the Next Healthcare Era', eventName: 'Eureka Upper Egypt Healthcare Excellence Roadshow', sales: 1300000, revenue: 800000, budget: 150000, owner: 'Egypt BD + CEO + Quality Lead',
      kpis: '40 target organizations; 15 executive meetings; 6 diagnostics; 5 proposals; 3 new clients; EGP 3M pipeline',
      actions: ['Map 40 target organizations — Minya & Assiut', 'Launch Eureka UHIA & GAHAR Readiness Program', 'Run Upper Egypt Healthcare Excellence Roadshow', 'Book 15 executive meetings', 'Deliver 6 diagnostics'] },
    { month: 'April', theme: 'LIBYA MARKET ENTRY', primaryMarket: 'Tripoli, Benghazi, Misrata', campaign: 'Building Sustainable Healthcare Organizations', eventName: 'Libya Healthcare Transformation Executive Roundtable', sales: 1300000, revenue: 900000, budget: 200000, owner: 'CEO + International BD + Libya Partner',
      kpis: '30 target organizations; 10 high-level meetings; 3 major proposals; 1 anchor agreement; EGP 4M Libya pipeline',
      actions: ['Map 30 Libya target organizations', 'Launch Eureka Hospital Transformation Program — Libya (Assessment/Systems Design/Implementation/Training/Mock Assessment/12-Month Sustainability)', 'Host Libya Healthcare Transformation Executive Roundtable', 'Secure Libya anchor agreement negotiation'] },
    { month: 'May', theme: 'SAUDI PIPELINE CREATION', primaryMarket: 'Saudi Arabia', campaign: 'Beyond CBAHI', eventName: 'Online Executive Webinar — Beyond CBAHI', sales: 1400000, revenue: 1000000, budget: 160000, owner: 'International BD + CEO + Marketing',
      kpis: '100 Saudi target accounts; 25 meaningful decision-maker contacts; 10 meetings; 5 qualified opportunities; 3 proposals; EGP 4M Saudi pipeline',
      actions: ['Build 100 Saudi target account database', 'Launch Healthcare Performance Excellence Program (hero product)', 'Run "Beyond CBAHI" webinar', 'Secure 25 decision-maker contacts', 'Book 10 meetings'] },
    { month: 'June', theme: 'EGYPT REGIONAL EXPANSION', primaryMarket: 'Damietta + Matrouh', campaign: 'Healthcare Readiness 2027', eventName: 'Damietta & Matrouh Healthcare Workshops', sales: 1500000, revenue: 1100000, budget: 150000, owner: 'Egypt BD + Quality Team + Commercial Director',
      kpis: '40 facilities mapped; 15 meetings; 8 assessments; 5 proposals; 3 wins; 2 referral partners',
      actions: ['Map 40 facilities — Damietta & Matrouh', 'Launch GAHAR + UHIA Readiness Assessment product', 'Host Damietta Healthcare Owners Workshop', 'Host Matrouh Healthcare Readiness Workshop', 'Sign 2 referral partners'] },
    { month: 'July', theme: 'EXISTING CLIENT MONETIZATION', primaryMarket: 'Egypt', campaign: 'From Accreditation to Excellence', eventName: 'Eureka Client Excellence Day', sales: 1400000, revenue: 1100000, budget: 100000, owner: 'Commercial Director + PMO + Academy Lead',
      kpis: '100% client review; 10 upsell proposals; 4 upsell contracts; 2 annual retainers; Academy first cohort',
      actions: ['Complete 100% existing-client review', 'Prepare upsell proposals (Sustainability Retainers, Operations, HR, Finance, Patient Experience, Training, ISO, Governance, KPI Systems)', 'Launch Eureka Healthcare Leadership Academy', 'Host Eureka Client Excellence Day', 'Close 2 annual retainers'] },
    { month: 'August', theme: 'UAE SPECIALTY HEALTHCARE', primaryMarket: 'UAE', campaign: 'Specialty Healthcare Excellence', eventName: 'Private CEO Meeting Week — Dubai', sales: 1500000, revenue: 1200000, budget: 120000, owner: 'International BD + CEO',
      kpis: '40 facilities mapped; 12 senior meetings; 5 diagnostics; 4 proposals; 1 UAE contract; EGP 3M pipeline',
      actions: ['Map 40 UAE specialty facilities (Oncology, Vascular, Ophthalmology, Day Surgery, Specialized Hospitals)', 'Launch Specialty Healthcare Excellence Program', 'Run Private CEO Meeting Week — Dubai', 'Close first UAE contract'] },
    { month: 'September', theme: 'OMAN MARKET CREATION', primaryMarket: 'Oman', campaign: 'Your OHAS Readiness Partner', eventName: 'OHAS Readiness Executive Masterclass', sales: 1600000, revenue: 1200000, budget: 140000, owner: 'International BD + Accreditation Lead',
      kpis: '40 Oman target hospitals; 15 contacts; 8 meetings; 4 proposals; 2 partner candidates; EGP 2.5M pipeline',
      actions: ['Map 40 Oman target hospitals', 'Launch OHAS Readiness & Implementation Program', 'Run OHAS Readiness Executive Masterclass', 'Identify 2 Oman partner candidates'] },
    { month: 'October', theme: 'SAUDI CONVERSION', primaryMarket: 'Saudi Arabia', campaign: 'Healthcare Performance Excellence — Saudi Arabia', eventName: 'Riyadh Executive Business Mission', sales: 1700000, revenue: 1300000, budget: 220000, owner: 'CEO + International BD',
      kpis: '15 pre-booked senior meetings; 6 opportunities; 4 proposals; 1 anchor Saudi contract; EGP 5M Saudi pipeline; 1 formal Saudi partnership',
      actions: ['Pre-book 15 senior meetings for Riyadh mission', 'Run Riyadh Executive Business Mission', 'Close anchor Saudi contract', 'Formalize Saudi partnership agreement'] },
    { month: 'November', theme: 'OMAN CONVERSION + GCC CROSS-SELL', primaryMarket: 'Oman + UAE', campaign: 'Healthcare Excellence GCC', eventName: 'Muscat OHAS Executive Workshop', sales: 1800000, revenue: 1400000, budget: 190000, owner: 'International BD + CEO + Accreditation Lead',
      kpis: '10 Muscat meetings; 4 OHAS proposals; 1 Oman contract; 2 UAE late-stage opportunities; EGP 3M new pipeline',
      actions: ['Run Muscat OHAS Executive Workshop', 'Close first Oman contract', 'Advance 2 UAE late-stage opportunities', 'Submit 4 OHAS proposals'] },
    { month: 'December', theme: 'RENEW, EXPAND & LOCK 2028', primaryMarket: 'All', campaign: '2028 Starts Now', eventName: 'Eureka Annual Healthcare Excellence Forum — Cairo', sales: 2000000, revenue: 1600000, budget: 200000, owner: 'CEO + Commercial Director + PMO + Finance',
      kpis: '80%+ eligible renewals; 5 annual retainers; 3 management/operations opportunities; EGP 5M+ January 2028 opening pipeline',
      actions: ['Complete client performance reviews across all markets', 'Run renewal & upsell proposal cycle', 'Host Eureka Annual Healthcare Excellence Forum — Cairo', 'Close 5 annual retainers', 'Build EGP 5M+ opening pipeline for January 2028'] }
  ];
}

function seedMasterPlan_() {
  clearDataRows_(SHEETS.MASTER_PLAN);
  var quarterOf = { January: 'Q1', February: 'Q1', March: 'Q1', April: 'Q2', May: 'Q2', June: 'Q2', July: 'Q3', August: 'Q3', September: 'Q3', October: 'Q4', November: 'Q4', December: 'Q4' };
  var plan = getMonthlyStrategyPlan_();
  var records = plan.map(function (m, i) {
    return {
      month: m.month, monthNumber: i + 1, quarter: quarterOf[m.month], theme: m.theme,
      primaryMarket: m.primaryMarket, campaign: m.campaign, eventName: m.eventName,
      salesBookingsTarget: m.sales, revenueTarget: m.revenue, growthBudget: m.budget,
      kpiSummary: m.kpis, owner: m.owner
    };
  });
  bulkAppendRecords(SHEETS.MASTER_PLAN, records);
}

function seedCampaigns_() {
  clearDataRows_(SHEETS.CAMPAIGNS);
  var plan = getMonthlyStrategyPlan_();
  var monthIndexToDates = monthDateRanges_();
  var records = plan.map(function (m, i) {
    return {
      campaign: m.campaign, market: firstMarketToken_(m.primaryMarket), country: '',
      start: monthIndexToDates[i].start, end: monthIndexToDates[i].end,
      businessObjective: m.theme, targetAudience: '', coreMessage: '', product: '',
      channel: 'Account Based Marketing', budget: m.budget, actualSpend: 0,
      leads: 0, qualifiedLeads: 0, meetings: 0, proposals: 0, wins: 0,
      revenueInfluenced: 0, pipelineInfluenced: 0, owner: m.owner, status: 'Planned', lessonsLearned: ''
    };
  });
  bulkAppendRecords(SHEETS.CAMPAIGNS, records);
}

function seedEvents_() {
  clearDataRows_(SHEETS.EVENTS);
  var events = [
    ['WHX Dubai', 'UAE', 'Dubai', 'January', 'Conference'],
    ['Eureka Healthcare Executive Breakfast — Sheikh Zayed', 'Egypt', 'Sheikh Zayed', 'February', 'Executive Breakfast'],
    ['Eureka Upper Egypt Healthcare Excellence Roadshow', 'Egypt', 'Minya / Assiut', 'March', 'Roadshow'],
    ['Libya Healthcare Transformation Executive Roundtable', 'Libya', 'Tripoli', 'April', 'Roundtable'],
    ['Beyond CBAHI — Executive Webinar', 'Saudi Arabia', 'Online', 'May', 'Webinar'],
    ['Damietta Healthcare Owners Workshop', 'Egypt', 'Damietta', 'June', 'Workshop'],
    ['Matrouh Healthcare Readiness Workshop', 'Egypt', 'Matrouh', 'June', 'Workshop'],
    ['Eureka Client Excellence Day', 'Egypt', 'Cairo', 'July', 'Client Day'],
    ['Private CEO Meeting Week — Dubai', 'UAE', 'Dubai', 'August', 'Business Mission'],
    ['OHAS Readiness Executive Masterclass', 'Oman', 'Muscat', 'September', 'Masterclass'],
    ['Riyadh Executive Business Mission', 'Saudi Arabia', 'Riyadh', 'October', 'Business Mission'],
    ['Muscat OHAS Executive Workshop', 'Oman', 'Muscat', 'November', 'Workshop'],
    ['Eureka Annual Healthcare Excellence Forum — Cairo', 'Egypt', 'Cairo', 'December', 'Forum']
  ];
  var monthToRange = {};
  var plan = getMonthlyStrategyPlan_();
  var ranges = monthDateRanges_();
  plan.forEach(function (m, i) { monthToRange[m.month] = ranges[i]; });
  var records = events.map(function (e) {
    var range = monthToRange[e[3]] || ranges[0];
    return {
      eventName: e[0], country: e[1], city: e[2], date: range.start, eventType: e[4],
      targetAudience: '', targetAttendees: 0, actualAttendees: 0, budget: 0, actualCost: 0,
      meetingsGenerated: 0, qualifiedLeads: 0, opportunities: 0, pipelineGenerated: 0,
      proposalsGenerated: 0, contractsWon: 0, revenueGenerated: 0, owner: '', followUpCompletionPct: 0, notes: ''
    };
  });
  bulkAppendRecords(SHEETS.EVENTS, records);
}

function seedKpis_() {
  clearDataRows_(SHEETS.KPIS);
  var records = [
    ['Financial', 'Revenue Target', 'Sum of Master Plan revenue targets for the year', 'EGP 12,700,000'],
    ['Financial', 'Revenue Actual', 'SUM(Revenue.revenueRecognized)', 'Track vs target'],
    ['Financial', 'Sales Bookings', 'SUM(Revenue.contractValue) signed in period', 'EGP 17,400,000 annual'],
    ['Financial', 'Cash Collected', 'SUM(Revenue.amountCollected)', 'Maximize'],
    ['Financial', 'Outstanding Receivables', 'SUM(Revenue.outstanding)', 'Minimize; alert >30 days overdue'],
    ['Financial', 'Gross Margin', '(Revenue - direct delivery cost) / Revenue', '>= 40%'],
    ['Financial', 'DSO', 'Avg days from invoice date to collection date', '<= 45 days'],
    ['Financial', 'Growth Spend', 'SUM(Expenses.actualAmount)', 'EGP 1,950,000 annual budget'],
    ['Financial', 'Budget Variance', 'Budgeted - Actual (Expenses)', 'Track by month/market/campaign'],
    ['Commercial', 'Total Pipeline', 'SUM(Pipeline.estimatedOpportunityValue) excl. Won/Lost', 'EGP 38M–40M'],
    ['Commercial', 'Weighted Pipeline', 'SUM(Pipeline.weightedValue)', 'Track monthly'],
    ['Commercial', 'Pipeline Coverage', 'Total Pipeline / Annual Revenue Target', '~3.0x; alert <2.5x'],
    ['Commercial', 'New Leads', 'COUNT(Pipeline created in period)', 'Track monthly'],
    ['Commercial', 'Qualified Leads', 'COUNT(Pipeline stage >= Discovery Completed)', 'Track monthly'],
    ['Commercial', 'Meetings', 'COUNT(Pipeline stage >= Meeting Scheduled reached in period)', 'Track monthly'],
    ['Commercial', 'Diagnostics', 'COUNT(Pipeline stage = Diagnostic / Assessment reached)', 'Track monthly'],
    ['Commercial', 'Proposals', 'COUNT(Pipeline stage >= Proposal Submitted reached)', 'Track monthly'],
    ['Commercial', 'Wins', 'COUNT(Pipeline stage = Won)', 'Track monthly'],
    ['Commercial', 'Win Rate', 'Won / (Won + Lost)', 'Track monthly'],
    ['Commercial', 'Average Contract Value', 'AVG(Revenue.contractValue)', 'Track monthly'],
    ['Commercial', 'Sales Cycle', 'AVG(days from firstContactDate to Won)', 'Track monthly'],
    ['Marketing', 'Website Leads', 'COUNT(Pipeline.leadSource = Website)', 'Track monthly'],
    ['Marketing', 'LinkedIn Leads', 'COUNT(Pipeline.leadSource = LinkedIn)', 'Track monthly'],
    ['Marketing', 'Google Leads', 'COUNT(Pipeline.leadSource = Google)', 'Track monthly'],
    ['Marketing', 'Campaign Qualified Leads', 'SUM(Campaigns.qualifiedLeads)', 'Track monthly'],
    ['Marketing', 'Cost per Qualified Lead', 'Campaigns.actualSpend / Campaigns.qualifiedLeads', 'Minimize'],
    ['Marketing', 'Pipeline Influenced', 'SUM(Campaigns.pipelineInfluenced)', 'Track monthly'],
    ['Marketing', 'Marketing Revenue Influenced', 'SUM(Campaigns.revenueInfluenced)', 'Track monthly'],
    ['Delivery', 'On-Time Deliverables', '% Projects with endDate met', '>= 90%'],
    ['Delivery', 'Project Completion %', 'AVG(Projects.percentComplete)', 'Track monthly'],
    ['Delivery', 'Client NPS', 'AVG(Projects.nps)', '>= 50'],
    ['Delivery', 'Consultant Utilization', 'AVG(Projects.consultantUtilization)', '>= 75%'],
    ['Delivery', 'Project Gross Margin', 'AVG(Projects.grossMargin)', '>= 35%'],
    ['Delivery', 'Red Projects', 'COUNT(Projects.status = Red)', 'Minimize'],
    ['Delivery', 'Scope Creep Cases', 'COUNT(Projects.scopeCreep = true)', 'Minimize'],
    ['Strategic', 'Revenue from Outside Alexandria', 'SUM(Revenue.revenueRecognized) where market != Alexandria', 'Maximize — diversification'],
    ['Strategic', 'International Revenue', 'SUM(Revenue.revenueRecognized) where country != Egypt', 'EGP 5.7M target (SA+Libya+UAE+Oman)'],
    ['Strategic', 'Recurring Revenue %', 'Retainer revenue / Total revenue', 'Track quarterly'],
    ['Strategic', 'Revenue from New Business Lines', 'SUM(Revenue.revenueRecognized) where businessUnit != Accreditation & Excellence', 'Track quarterly'],
    ['Strategic', 'Markets Entered', 'COUNT(Markets.status = Active)', '10 markets by year end'],
    ['Strategic', 'Strategic Partnerships Signed', 'COUNT(Partnerships.status = Active)', 'Track quarterly']
  ];
  var mapped = records.map(function (r) {
    return { kpiCategory: r[0], kpiName: r[1], description: r[2], target: r[3], frequency: 'Monthly' };
  });
  bulkAppendRecords(SHEETS.KPIS, mapped);
}

function seedQuarterlyReview_() {
  clearDataRows_(SHEETS.QUARTERLY_REVIEW);
  var records = [
    { quarter: 'Q1', year: FISCAL_YEAR, revenueTarget: 1900000, bookingsTarget: 3200000, cumulativeRevenueTarget: 1900000,
      gateObjectives: 'CRM operational; Cairo active; GCC launched; Upper Egypt pipeline built; case studies completed; Saudi database completed. RED ALERT if qualified pipeline < EGP 15M by March 31.',
      pipelineRequirement: 15000000, notes: '' },
    { quarter: 'Q2', year: FISCAL_YEAR, revenueTarget: 3000000, bookingsTarget: 4200000, cumulativeRevenueTarget: 4900000,
      gateObjectives: 'At least one international contract OR serious final-stage international negotiation.',
      pipelineRequirement: 0, notes: '' },
    { quarter: 'Q3', year: FISCAL_YEAR, revenueTarget: 3500000, bookingsTarget: 4500000, cumulativeRevenueTarget: 8400000,
      gateObjectives: 'Oman active; UAE pipeline active; Upper Egypt revenue; Academy producing revenue; existing client upsell demonstrated.',
      pipelineRequirement: 0, notes: '' },
    { quarter: 'Q4', year: FISCAL_YEAR, revenueTarget: 4300000, bookingsTarget: 5500000, cumulativeRevenueTarget: 12700000,
      gateObjectives: 'Annual revenue EGP 12.7M. Minimum January 2028 opening pipeline EGP 10M (preferred EGP 15M+).',
      pipelineRequirement: 10000000, notes: '' }
  ];
  bulkAppendRecords(SHEETS.QUARTERLY_REVIEW, records);
}

function seedDigitalRoadmap_() {
  clearDataRows_(SHEETS.DIGITAL_ROADMAP);
  var ranges = monthDateRanges_();
  var records = [
    { feature: 'Eureka Excellence Portal — Architecture & Client Journey', phase: 'Q1', start: ranges[0].start, deadline: ranges[2].end, status: 'Not Started', priority: 'High', notes: 'Architecture and client journey design' },
    { feature: 'Eureka Excellence Portal — MVP for 2 Clients', phase: 'Q2', start: ranges[3].start, deadline: ranges[5].end, status: 'Not Started', priority: 'High', notes: 'MVP rollout to 2 pilot clients' },
    { feature: 'Eureka Excellence Portal — Rollout to Major Clients', phase: 'Q3', start: ranges[6].start, deadline: ranges[8].end, status: 'Not Started', priority: 'Medium', notes: 'Rollout to major clients' },
    { feature: 'Eureka Excellence Portal — Premium Paid Version', phase: 'Q4', start: ranges[9].start, deadline: ranges[11].end, status: 'Not Started', priority: 'Medium', notes: 'Premium paid version launch' }
  ];
  bulkAppendRecords(SHEETS.DIGITAL_ROADMAP, records);
}

/** Returns 12 {start,end} Date pairs for the fiscal year, one per calendar month. */
function monthDateRanges_() {
  var out = [];
  for (var m = 0; m < 12; m++) {
    var start = new Date(FISCAL_YEAR, m, 1);
    var end = new Date(FISCAL_YEAR, m + 1, 0);
    out.push({ start: start, end: end });
  }
  return out;
}

function firstMarketToken_(marketField) {
  return String(marketField).split(/[+,]/)[0].trim();
}

// ============================================================
// SOURCE: setup/SeedWeekly.gs
// ============================================================

/**
 * Breaks the 2027 plan into 52 weekly execution periods (Section 8) and generates a
 * grounded task list per week, derived from that month's "primary actions" and KPI targets
 * in the brief — plus two standing weekly cadences (pipeline/CRM review, CEO/BD sync) that
 * apply every week regardless of theme. Monthly financial targets are split evenly across
 * the weeks that fall in each month so week-level and month-level targets always reconcile.
 */
function seedWeeklyExecutionAndTasks() {
  clearDataRows_(SHEETS.WEEKLY_EXECUTION);
  clearDataRows_(SHEETS.TASKS);

  var plan = getMonthlyStrategyPlan_();
  var planByMonth = {};
  plan.forEach(function (m) { planByMonth[m.month] = m; });
  var quarterOf = { January: 'Q1', February: 'Q1', March: 'Q1', April: 'Q2', May: 'Q2', June: 'Q2', July: 'Q3', August: 'Q3', September: 'Q3', October: 'Q4', November: 'Q4', December: 'Q4' };

  var weeks = buildWeekDateRanges_(); // [{weekNumber,start,end}] x52
  // Group weeks by the month that contains their start date.
  var weeksByMonth = {};
  weeks.forEach(function (w) {
    var monthName = Utilities.formatDate(w.start, 'GMT', 'MMMM');
    weeksByMonth[monthName] = weeksByMonth[monthName] || [];
    weeksByMonth[monthName].push(w);
  });

  var weeklyRecords = [];
  var actionCursor = {}; // per-month index into that month's actions list, so consecutive weeks get different actions

  weeks.forEach(function (w) {
    var monthName = Utilities.formatDate(w.start, 'GMT', 'MMMM');
    var m = planByMonth[monthName];
    var weeksInThisMonth = weeksByMonth[monthName].length;
    w.weekId = 'WK-' + ('00' + w.weekNumber).slice(-2);
    w.month = monthName;
    w.quarter = quarterOf[monthName];
    w.strategicTheme = m.theme;
    w.campaign = m.campaign;
    w.primaryMarket = firstMarketToken_(m.primaryMarket);
    w.secondaryMarket = String(m.primaryMarket).indexOf('+') > -1 ? m.primaryMarket.split('+')[1].trim() : '';
    w.salesTargetWeek = Math.round(m.sales / weeksInThisMonth);
    w.revenueTargetWeek = Math.round(m.revenue / weeksInThisMonth);
    w.budgetPlannedWeek = Math.round(m.budget / weeksInThisMonth);
    weeklyRecords.push({
      weekId: w.weekId, weekNumber: w.weekNumber, startDate: w.start, endDate: w.end,
      month: w.month, quarter: w.quarter, primaryMarket: w.primaryMarket, secondaryMarket: w.secondaryMarket,
      strategicTheme: w.strategicTheme, campaign: w.campaign,
      salesTargetWeek: w.salesTargetWeek, revenueTargetWeek: w.revenueTargetWeek, budgetPlannedWeek: w.budgetPlannedWeek,
      notes: ''
    });
  });
  bulkAppendRecords(SHEETS.WEEKLY_EXECUTION, weeklyRecords);

  var taskRecords = [];
  weeks.forEach(function (w) {
    var m = planByMonth[w.month];
    actionCursor[w.month] = actionCursor[w.month] || 0;
    var action = m.actions[actionCursor[w.month] % m.actions.length];
    actionCursor[w.month]++;

    taskRecords.push(makeTask_(w, action, categoryForOwner_(m.owner), m.owner, 'High', m.kpis));
    taskRecords.push(makeTask_(w, 'Weekly pipeline & CRM update — ' + w.primaryMarket, 'Sales', 'Commercial Director', 'Medium', 'Pipeline data current; stages accurate; next actions set on every open opportunity'));
    taskRecords.push(makeTask_(w, 'Weekly CEO / BD sync — review targets vs actual', 'CEO', 'CEO', 'Medium', 'Decisions logged; blockers escalated'));
  });
  bulkAppendRecords(SHEETS.TASKS, taskRecords);

  return 'Seeded ' + weeklyRecords.length + ' weeks and ' + taskRecords.length + ' tasks.';
}

function makeTask_(w, taskText, category, owner, priority, deliverable) {
  return {
    weekId: w.weekId, task: taskText, taskCategory: category,
    taskDescription: taskText + ' (' + w.strategicTheme + ' — ' + w.campaign + ')',
    expectedDeliverable: deliverable, taskOwner: primaryOwnerToken_(owner), supportingTeam: owner,
    priority: priority, status: 'Not Started', startDate: w.start, dueDate: w.end,
    completionDate: '', percentCompletion: 0, dependency: '', blocker: '', ceoAttentionRequired: false, notes: ''
  };
}

function primaryOwnerToken_(ownerField) {
  return String(ownerField).split('+')[0].trim();
}

function categoryForOwner_(ownerField) {
  var o = String(ownerField);
  if (o.indexOf('International BD') > -1) return 'International Expansion';
  if (o.indexOf('CEO') === 0) return 'CEO';
  return 'Business Development';
}

/** 52 sequential 7-day weeks starting Jan 1 2027; the 52nd week absorbs Dec 31 so the whole year is covered. */
function buildWeekDateRanges_() {
  var weeks = [];
  var cursor = new Date(FISCAL_YEAR, 0, 1);
  for (var i = 1; i <= 52; i++) {
    var start = new Date(cursor);
    var end;
    if (i === 52) {
      end = new Date(FISCAL_YEAR, 11, 31);
    } else {
      end = new Date(cursor);
      end.setDate(end.getDate() + 6);
    }
    weeks.push({ weekNumber: i, start: start, end: end });
    cursor = new Date(end);
    cursor.setDate(cursor.getDate() + 1);
  }
  return weeks;
}
