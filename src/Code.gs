/**
 * Entry point: web app bootstrap, custom menu, and HTML include helper.
 */

function doGet(e) {
  var page = (e && e.parameter && e.parameter.page) || 'Index';
  var template = HtmlService.createTemplateFromFile(page);
  return template.evaluate()
    .setTitle('Eureka 2027 — CEO Execution System')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .setFaviconUrl('https://www.gstatic.com/images/branding/product/1x/sheets_48dp.png');
}

/** Used inside Index.html: <?!= include('CSS'); ?> and <?!= include('JavaScript'); ?> */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Eureka 2027')
    .addItem('1. Build sheet structure', 'runSetupSheets')
    .addItem('2. Apply validation & formatting', 'runSetupValidation')
    .addItem('3. Seed master + strategy data', 'runSeedAll')
    .addSeparator()
    .addItem('Refresh dashboard formulas', 'refreshDashboardSheet')
    .addItem('Recompute traffic lights & calculated fields', 'recomputeAllCalculatedFields')
    .addSeparator()
    .addItem('🔧 One-time repair: fix seed-data IDs & week mapping', 'confirmRepairExisting2027SeedData')
    .addSeparator()
    .addItem('⚠ Reset ALL data (danger)', 'confirmResetAllData')
    .addToUi();
}

/**
 * Menu entry point for repairExisting2027SeedData() — asks for confirmation first since it
 * rewrites cells, even though the repair itself only fixes what it finds actually wrong and
 * is safe to run more than once.
 */
function confirmRepairExisting2027SeedData() {
  var ui = SpreadsheetApp.getUi();
  var resp = ui.alert(
    'Repair 2027 seed data?',
    'Fixes duplicate seeded IDs and corrects Weekly Execution month/quarter/theme/campaign/target ' +
    'mapping using each week\'s own Start Date. Only touches seeded reference tables and the 52 ' +
    'weekly rows — Revenue, Expenses, Pipeline, Projects, Clients, Decisions and Risks are never ' +
    'read or modified. Safe to run more than once. Continue?',
    ui.ButtonSet.YES_NO
  );
  if (resp === ui.Button.YES) repairExisting2027SeedData();
}

/** One-click full install, in the correct dependency order. Safe to re-run. */
function fullInstall() {
  runSetupSheets();
  runSetupValidation();
  runSeedAll();
  recomputeAllCalculatedFields();
  refreshDashboardSheet();
  return 'Eureka 2027 system installed successfully.';
}

function confirmResetAllData() {
  var ui = SpreadsheetApp.getUi();
  var resp = ui.alert('Reset ALL data?', 'This deletes every sheet and rebuilds an empty structure. This cannot be undone. Continue?', ui.ButtonSet.YES_NO);
  if (resp === ui.Button.YES) {
    resetAllData();
    ui.alert('Reset complete. Run "Seed master + strategy data" to reload the 2027 plan.');
  }
}

function resetAllData() {
  var spreadsheet = ss_();
  var sheets = spreadsheet.getSheets();
  sheets.forEach(function (sh) { spreadsheet.deleteSheet(sh); });
  spreadsheet.insertSheet('temp_placeholder');
  runSetupSheets();
  spreadsheet.deleteSheet(spreadsheet.getSheetByName('temp_placeholder'));
  runSetupValidation();
}
