
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
    ['2027 Revenue Target', '', '', 'Total Pipeline', '', ''],
    ['Revenue Actual (Recognized)', '', '', 'Weighted Pipeline', '', ''],
    ['Revenue Achievement %', '', '', 'Pipeline Coverage (x)', '', ''],
    ['Annual Bookings Target', '', '', 'Cash Collected', '', ''],
    ['Bookings Actual', '', '', 'Outstanding Receivables', '', ''],
    ['Growth Budget', '', '', 'Win Rate', '', ''],
    ['Actual Growth Spend', '', '', 'Deals Won (YTD)', '', ''],
    ['Budget Variance', '', '', 'Tasks Completion %', '', '']
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
  var plan = getMonthlyStrategyPlan_();
  var records = plan.map(function (m, i) {
    return {
      month: m.month, monthNumber: i + 1, quarter: MONTH_TO_QUARTER_[m.month], theme: m.theme,
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

  var weeks = buildWeekDateRanges_(); // [{weekNumber,start,end}] x52
  // Group weeks by the month that contains their start date (the canonical rule: Month,
  // Quarter, Strategic Theme, Campaign and Market are all determined by a week's Start Date).
  var weeksByMonth = {};
  weeks.forEach(function (w) {
    var monthName = monthNameOf_(w.start);
    weeksByMonth[monthName] = weeksByMonth[monthName] || [];
    weeksByMonth[monthName].push(w);
  });

  var weeklyRecords = [];
  var actionCursor = {}; // per-month index into that month's actions list, so consecutive weeks get different actions

  weeks.forEach(function (w) {
    var monthName = monthNameOf_(w.start);
    var m = planByMonth[monthName];
    var weeksInThisMonth = weeksByMonth[monthName].length;
    w.weekId = 'WK-' + ('00' + w.weekNumber).slice(-2);
    w.month = monthName;
    w.quarter = MONTH_TO_QUARTER_[monthName];
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

// ============================================================
// SOURCE: setup/RepairSeedData.gs
// ============================================================

/**
 * ONE-TIME REPAIR for a spreadsheet that was already built and seeded before two seed-data
 * bugs were fixed:
 *
 *  1. Duplicate IDs — bulkAppendRecords() generated every record's ID by re-scanning the
 *     sheet for the current max ID, but did that BEFORE writing any of the batch to the
 *     sheet, so every record in the same seed call saw the same unchanged sheet and got
 *     the same "next" ID (all Tasks came out as TSK-0001, all Campaigns as CMP-0001, etc).
 *     Fixed at the source in SheetService.gs/IdGenerator.gs so a fresh install can't
 *     reproduce it — this file repairs a sheet that was already seeded with the old code.
 *
 *  2. Wrong week->month mapping — the month name for a week was derived with
 *     Utilities.formatDate(date, 'GMT', 'MMMM'), which reinterprets a date built in the
 *     script's Africa/Cairo (UTC+2) timeZone as if it were UTC. That shifts local midnight
 *     back onto the previous calendar day, which only matters when a week starts on the 1st
 *     of a month — that day gets misread as the last day of the PREVIOUS month. Two of the
 *     52 seeded weeks start on the 1st of a month: WK-01 (Jan 1, misread as December) and
 *     WK-40 (Oct 1, misread as September). Fixed at the source in Compute.gs (monthNameOf_)
 *     and SeedWeekly.gs — this file recomputes the 52 Weekly Execution rows and the seeded
 *     Tasks that inherited the wrong month.
 *
 * This function is safe to run on a live, already-seeded sheet:
 *  - Only rewrites the ID column of a table if it actually finds duplicate IDs in it.
 *  - Only rewrites Weekly Execution's derived fields (month, quarter, strategic theme,
 *    campaign, primary/secondary market, and the three weekly target figures) — weekId,
 *    weekNumber, startDate, endDate and notes are left exactly as they are, and no rows are
 *    added or removed.
 *  - Only touches a seeded Task row if its description still carries the *exact* wrong
 *    theme/campaign text the original bug produced, so any task you've since edited, or any
 *    task you've added yourself, is left untouched.
 *  - Never reads or writes 06_Revenue, 07_Expenses, 08_Sales_Pipeline, 09_Target_Accounts,
 *    16_Clients, 17_Projects, 18_Partnerships, 19_Academy, 20_Case_Studies, 24_Risks, or
 *    25_Decisions — none of those sheets are touched by this function.
 *  - Idempotent — every step first checks whether anything is actually wrong, so running it
 *    a second (or fifth) time is harmless and will simply report nothing left to fix.
 */
/**
 * Fails fast with a specific, actionable message instead of a cryptic "X is not defined"
 * ReferenceError. By far the most common cause of that error in a copy-paste (no clasp)
 * deployment is that one of the two other files wasn't pasted in COMPLETELY — a partial
 * selection, or a paste that silently got cut off partway through a very long file. Each
 * name checked here is either near the very start or the very end of the file it lives in,
 * so if it resolves, that whole file made it in; if it doesn't, this says exactly which file
 * to re-paste rather than leaving you to guess from a bare ReferenceError and a line number.
 *
 * (In the multi-file /src project these same symbols live in config/Constants.gs,
 * config/SheetSchema.gs, Code.gs, data/SheetService.gs, api/Compute.gs and api/LookupsApi.gs
 * respectively — this check only matters for the 3-file manual-deploy build, where several
 * of those get concatenated into one file and a partial paste of that file is easy to miss.)
 */
function assertManualDeployFilesLoaded_() {
  var missing = [];
  if (typeof SHEETS === 'undefined') missing.push('SHEETS (defined near the top of Code.gs)');
  if (typeof getHeaders === 'undefined') missing.push('getHeaders (defined in the SheetSchema section of Code.gs)');
  if (typeof resetAllData === 'undefined') missing.push('resetAllData (the last function in Code.gs)');
  if (typeof bulkAppendRecords === 'undefined') missing.push('bulkAppendRecords (defined near the top of Backend.gs)');
  if (typeof MONTH_TO_QUARTER_ === 'undefined') missing.push('MONTH_TO_QUARTER_ (defined in the Compute section of Backend.gs)');
  if (typeof api_getLookups === 'undefined') missing.push('api_getLookups (the last function in Backend.gs)');
  if (missing.length) {
    throw new Error(
      'Cannot run: the following expected to already be loaded but are missing — ' + missing.join('; ') + '. ' +
      'This means Code.gs and/or Backend.gs were not pasted in FULLY. Fix: in the Apps Script editor, open ' +
      'each of those two files, select all (Ctrl/Cmd+A), delete everything, paste the complete current ' +
      'contents of manual-deploy/Code.gs and manual-deploy/Backend.gs, save each file (Ctrl/Cmd+S), then try again.'
    );
  }
}

function repairExisting2027SeedData() {
  assertManualDeployFilesLoaded_();
  var report = [];
  report.push(dedupeAndRenumberIds_(SHEETS.TEAM, 'teamId', 'EMP'));
  report.push(dedupeAndRenumberIds_(SHEETS.MARKETS, 'marketId', 'MKT'));
  report.push(dedupeAndRenumberIds_(SHEETS.BUSINESS_UNITS, 'buId', 'BU'));
  report.push(dedupeAndRenumberIds_(SHEETS.CAMPAIGNS, 'campaignId', 'CMP'));
  report.push(dedupeAndRenumberIds_(SHEETS.EVENTS, 'eventId', 'EVT'));
  report.push(dedupeAndRenumberIds_(SHEETS.KPIS, 'kpiId', 'KPI'));
  report.push(dedupeAndRenumberIds_(SHEETS.QUARTERLY_REVIEW, 'quarterId', 'Q'));
  report.push(dedupeAndRenumberIds_(SHEETS.DIGITAL_ROADMAP, 'featureId', 'FTR'));
  report.push(dedupeAndRenumberIds_(SHEETS.TASKS, 'taskId', 'TSK'));
  report.push(repairWeeklyExecutionAndTasks_());

  recomputeAllCalculatedFields();
  refreshDashboardSheet();

  var summary = 'Eureka 2027 seed-data repair complete:\n\n' + report.join('\n');
  Logger.log(summary);
  try {
    SpreadsheetApp.getUi().alert(summary);
  } catch (e) {
    // No UI context (e.g. run directly from the Apps Script editor's function dropdown) —
    // the summary is still in the Logger output (View > Logs) and in this function's return value.
  }
  return summary;
}

/**
 * Rewrites a sheet's ID column as prefix-0001, prefix-0002, ... in row order, but only if
 * it finds duplicate values there in the first place. Safe even though nothing else in this
 * project stores a foreign key to any of these IDs (every cross-sheet reference in this
 * system is by a human-readable name — market, business unit, team member, campaign, event —
 * never by these internal sequence IDs), so renumbering can't break a lookup elsewhere.
 */
function dedupeAndRenumberIds_(sheetName, idKey, prefix) {
  var sheet = ss_().getSheetByName(sheetName);
  if (!sheet || sheet.getLastRow() < 2) return sheetName + ': no rows — skipped.';
  var schema = getSchema(sheetName);
  var idColIndex = schema.map(function (c) { return c.key; }).indexOf(idKey);
  if (idColIndex === -1) return sheetName + ': no "' + idKey + '" column — skipped.';

  var numRows = sheet.getLastRow() - 1;
  var ids = sheet.getRange(2, idColIndex + 1, numRows, 1).getValues();
  var seen = {};
  var duplicateCount = 0;
  ids.forEach(function (row) {
    var v = row[0];
    if (seen[v]) duplicateCount++;
    seen[v] = true;
  });
  if (duplicateCount === 0) {
    return sheetName + ': ' + numRows + ' row(s), IDs already unique — no change.';
  }

  var newIds = [];
  for (var i = 1; i <= numRows; i++) newIds.push([prefix + '-' + padId_(i)]);
  sheet.getRange(2, idColIndex + 1, numRows, 1).setValues(newIds);
  return sheetName + ': renumbered ' + numRows + ' row(s) (' + duplicateCount + ' duplicate ID value(s) found) -> ' +
    prefix + '-0001..' + prefix + '-' + padId_(numRows) + '.';
}

/**
 * Recomputes Month, Quarter, Strategic Theme, Campaign, Primary/Secondary Market, and the
 * three weekly target figures for every row in 04_Weekly_Execution from that row's own
 * Start Date — the canonical rule requested — then patches any seeded Task rows that still
 * carry the stale (wrong) theme/campaign text.
 */
function repairWeeklyExecutionAndTasks_() {
  var sheet = ss_().getSheetByName(SHEETS.WEEKLY_EXECUTION);
  if (!sheet || sheet.getLastRow() < 2) return SHEETS.WEEKLY_EXECUTION + ': no rows found — skipped.';

  var plan = getMonthlyStrategyPlan_();
  var planByMonth = {};
  plan.forEach(function (m) { planByMonth[m.month] = m; });

  var schema = getSchema(SHEETS.WEEKLY_EXECUTION);
  var idx = {};
  schema.forEach(function (c, i) { idx[c.key] = i; });

  var numRows = sheet.getLastRow() - 1;
  var values = sheet.getRange(2, 1, numRows, schema.length).getValues();

  // Pass 1: the true month for every row, from Start Date alone — then how many weeks land
  // in each month, so each month's targets split evenly across exactly its own weeks.
  var correctedMonths = values.map(function (row) { return monthNameOf_(row[idx.startDate]); });
  var weeksPerMonth = {};
  correctedMonths.forEach(function (mn) { weeksPerMonth[mn] = (weeksPerMonth[mn] || 0) + 1; });

  // Pass 2: apply the correction to every row, and remember which weeks actually changed
  // (together with what was wrong before) so seeded Tasks can be patched to match.
  var fingerprints = {}; // weekId -> { oldTheme, oldCampaign, newWeek }
  for (var r = 0; r < numRows; r++) {
    var row = values[r];
    var monthName = correctedMonths[r];
    var m = planByMonth[monthName];
    if (!m) continue; // defensive: an unrecognized month string is left untouched rather than guessed at

    var weekId = row[idx.weekId];
    var oldTheme = row[idx.strategicTheme];
    var oldCampaign = row[idx.campaign];
    var weeksInMonth = weeksPerMonth[monthName];

    var newValues = {
      month: monthName,
      quarter: MONTH_TO_QUARTER_[monthName],
      primaryMarket: firstMarketToken_(m.primaryMarket),
      secondaryMarket: String(m.primaryMarket).indexOf('+') > -1 ? m.primaryMarket.split('+')[1].trim() : '',
      strategicTheme: m.theme,
      campaign: m.campaign,
      salesTargetWeek: Math.round(m.sales / weeksInMonth),
      revenueTargetWeek: Math.round(m.revenue / weeksInMonth),
      budgetPlannedWeek: Math.round(m.budget / weeksInMonth)
    };

    var changed = String(row[idx.month]) !== String(newValues.month) ||
      String(oldTheme) !== String(newValues.strategicTheme) ||
      String(oldCampaign) !== String(newValues.campaign) ||
      String(row[idx.salesTargetWeek]) !== String(newValues.salesTargetWeek) ||
      String(row[idx.revenueTargetWeek]) !== String(newValues.revenueTargetWeek) ||
      String(row[idx.budgetPlannedWeek]) !== String(newValues.budgetPlannedWeek);

    Object.keys(newValues).forEach(function (key) { row[idx[key]] = newValues[key]; });

    if (changed) {
      fingerprints[weekId] = {
        oldTheme: oldTheme,
        oldCampaign: oldCampaign,
        newWeek: { weekId: weekId, month: monthName, strategicTheme: newValues.strategicTheme, campaign: newValues.campaign, primaryMarket: newValues.primaryMarket }
      };
    }
  }

  sheet.getRange(2, 1, numRows, schema.length).setValues(values);

  var changedWeekIds = Object.keys(fingerprints);
  var taskReport = repairSeededTasksForWeeks_(fingerprints, planByMonth);
  return SHEETS.WEEKLY_EXECUTION + ': recomputed month/quarter/theme/campaign/market and re-split monthly ' +
    'targets across all ' + numRows + ' week rows from each row\'s own Start Date' +
    (changedWeekIds.length ? ' (' + changedWeekIds.length + ' week row(s) had incorrect data: ' + changedWeekIds.join(', ') + ')' : ' (none needed correction)') +
    '. ' + taskReport;
}

/**
 * Patches only the seeded Task rows that still carry the exact wrong theme/campaign text
 * from the original bug — matched by looking for that literal "(oldTheme — oldCampaign)"
 * suffix in the task's description. That fingerprint can only appear on a row this seeder
 * itself generated with the wrong month, so a task you've edited or added by hand (which
 * won't happen to end with that exact wrong text) is never touched.
 */
function repairSeededTasksForWeeks_(fingerprints, planByMonth) {
  var weekIds = Object.keys(fingerprints);
  if (!weekIds.length) return 'No task rows required correction.';

  var taskSheet = ss_().getSheetByName(SHEETS.TASKS);
  if (!taskSheet || taskSheet.getLastRow() < 2) return 'No task rows found.';
  var taskSchema = getSchema(SHEETS.TASKS);
  var tIdx = {};
  taskSchema.forEach(function (c, i) { tIdx[c.key] = i; });

  var numTaskRows = taskSheet.getLastRow() - 1;
  var taskValues = taskSheet.getRange(2, 1, numTaskRows, taskSchema.length).getValues();
  var fixedCount = 0;

  weekIds.forEach(function (weekId) {
    var fp = fingerprints[weekId];
    var w = fp.newWeek;
    var m = planByMonth[w.month];
    if (!m) return;
    var oldFingerprint = ' (' + fp.oldTheme + ' — ' + fp.oldCampaign + ')';

    for (var r = 0; r < taskValues.length; r++) {
      var row = taskValues[r];
      if (row[tIdx.weekId] !== weekId) continue;
      var description = String(row[tIdx.taskDescription] || '');
      if (description.slice(-oldFingerprint.length) !== oldFingerprint) continue; // not a stale seeded row — leave it alone

      var title = row[tIdx.task];
      if (title === 'Weekly CEO / BD sync — review targets vs actual') {
        row[tIdx.taskDescription] = title + ' (' + w.strategicTheme + ' — ' + w.campaign + ')';
      } else if (String(title).indexOf('Weekly pipeline & CRM update') === 0) {
        var newTitle = 'Weekly pipeline & CRM update — ' + w.primaryMarket;
        row[tIdx.task] = newTitle;
        row[tIdx.taskDescription] = newTitle + ' (' + w.strategicTheme + ' — ' + w.campaign + ')';
      } else {
        // The strategy-action task. The original per-week rotation index into that month's
        // action list can't be reconstructed after the fact, so this deterministically uses
        // the corrected month's first action — a genuine action for the right month, just not
        // guaranteed to be the exact rotation slot originally seeded for this specific week.
        var newAction = m.actions[0];
        row[tIdx.task] = newAction;
        row[tIdx.taskDescription] = newAction + ' (' + w.strategicTheme + ' — ' + w.campaign + ')';
        row[tIdx.taskCategory] = categoryForOwner_(m.owner);
        row[tIdx.expectedDeliverable] = m.kpis;
        row[tIdx.taskOwner] = primaryOwnerToken_(m.owner);
        row[tIdx.supportingTeam] = m.owner;
      }
      fixedCount++;
    }
  });

  if (fixedCount > 0) {
    taskSheet.getRange(2, 1, taskValues.length, taskSchema.length).setValues(taskValues);
  }
  return fixedCount + ' seeded task row(s) corrected across ' + weekIds.length + ' affected week(s).';
}
