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
