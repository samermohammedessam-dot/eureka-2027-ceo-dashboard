/**
 * Column schema for every sheet/tab. This is the relational model of the system.
 * Each entry: { key, header, type, idPrefix?, validation? }
 * - key: property name used everywhere in code (camelCase)
 * - header: exact column header text written into row 1 of the sheet
 * - type: 'text' | 'number' | 'date' | 'percent' | 'currency' | 'boolean'
 * - validation: name of a list in MASTER_LISTS (see SetupValidation.gs), or 'sheet:<SheetName>:<idKey>' for a
 *   foreign-key dropdown sourced from another sheet's ID column.
 *
 * Columns marked computed:true are written by Apps Script (never typed by a user) and are
 * protected from manual edits by SetupSheets.gs.
 */

function col(key, header, type, extra) {
  var c = { key: key, header: header, type: type || 'text' };
  if (extra) for (var k in extra) c[k] = extra[k];
  return c;
}

var SHEET_SCHEMA = {};

SHEET_SCHEMA[SHEETS.MASTER_PLAN] = [
  col('month', 'Month'),
  col('monthNumber', 'Month Number', 'number'),
  col('quarter', 'Quarter'),
  col('theme', 'Strategic Theme'),
  col('primaryMarket', 'Primary Market'),
  col('campaign', 'Campaign'),
  col('eventName', 'Major Event'),
  col('salesBookingsTarget', 'Sales Bookings Target', 'currency'),
  col('revenueTarget', 'Revenue Target', 'currency'),
  col('growthBudget', 'Growth Budget', 'currency'),
  col('kpiSummary', 'KPI Summary'),
  col('owner', 'Owner')
];

SHEET_SCHEMA[SHEETS.WEEKLY_EXECUTION] = [
  col('weekId', 'Week ID', 'text', { idPrefix: 'WK' }),
  col('weekNumber', 'Week Number', 'number'),
  col('startDate', 'Start Date', 'date'),
  col('endDate', 'End Date', 'date'),
  col('month', 'Month'),
  col('quarter', 'Quarter'),
  col('primaryMarket', 'Primary Market'),
  col('secondaryMarket', 'Secondary Market'),
  col('strategicTheme', 'Strategic Theme'),
  col('campaign', 'Campaign'),
  col('salesTargetWeek', 'Sales Target (Week)', 'currency'),
  col('revenueTargetWeek', 'Revenue Target (Week)', 'currency'),
  col('budgetPlannedWeek', 'Budget Planned (Week)', 'currency'),
  col('notes', 'Notes')
];

SHEET_SCHEMA[SHEETS.TASKS] = [
  col('taskId', 'Task ID', 'text', { idPrefix: 'TSK' }),
  col('weekId', 'Week ID', 'text', { validation: 'sheet:' + SHEETS.WEEKLY_EXECUTION + ':weekId' }),
  col('task', 'Task'),
  col('taskCategory', 'Task Category', 'text', { validation: 'TASK_CATEGORIES' }),
  col('taskDescription', 'Task Description'),
  col('expectedDeliverable', 'Expected Deliverable'),
  col('taskOwner', 'Task Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('supportingTeam', 'Supporting Team'),
  col('priority', 'Priority', 'text', { validation: 'TASK_PRIORITY' }),
  col('status', 'Status', 'text', { validation: 'TASK_STATUS' }),
  col('startDate', 'Start Date', 'date'),
  col('dueDate', 'Due Date', 'date'),
  col('completionDate', 'Completion Date', 'date'),
  col('percentCompletion', '% Completion', 'percent'),
  col('dependency', 'Dependency'),
  col('blocker', 'Blocker'),
  col('ceoAttentionRequired', 'CEO Attention Required?', 'boolean'),
  col('notes', 'Notes'),
  col('trafficLight', 'Traffic Light', 'text', { computed: true })
];

SHEET_SCHEMA[SHEETS.REVENUE] = [
  col('revenueId', 'Revenue ID', 'text', { idPrefix: 'REV' }),
  col('client', 'Client', 'text', { validation: 'sheet:' + SHEETS.CLIENTS + ':clientName' }),
  col('project', 'Project'),
  col('contractNumber', 'Contract Number'),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('city', 'City'),
  col('market', 'Market', 'text', { validation: 'sheet:' + SHEETS.MARKETS + ':market' }),
  col('businessUnit', 'Business Unit', 'text', { validation: 'sheet:' + SHEETS.BUSINESS_UNITS + ':businessUnit' }),
  col('service', 'Service'),
  col('bdOwner', 'BD Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('contractValue', 'Contract Value', 'currency'),
  col('contractSigningDate', 'Contract Signing Date', 'date'),
  col('projectStart', 'Project Start', 'date'),
  col('projectEnd', 'Project End', 'date'),
  col('invoiceAmount', 'Invoice Amount', 'currency'),
  col('invoiceDate', 'Invoice Date', 'date'),
  col('dueDate', 'Due Date', 'date'),
  col('amountCollected', 'Amount Collected', 'currency'),
  col('collectionDate', 'Collection Date', 'date'),
  col('outstanding', 'Outstanding', 'currency', { computed: true }),
  col('revenueRecognized', 'Revenue Recognized', 'currency'),
  col('month', 'Month', 'text', { computed: true }),
  col('quarter', 'Quarter', 'text', { computed: true }),
  col('paymentStatus', 'Payment Status', 'text', { validation: 'PAYMENT_STATUS' }),
  col('collectionStatus', 'Collection Status', 'text', { validation: 'COLLECTION_STATUS' }),
  col('daysOutstanding', 'Days Outstanding', 'number', { computed: true }),
  col('notes', 'Notes')
];

SHEET_SCHEMA[SHEETS.EXPENSES] = [
  col('expenseId', 'Expense ID', 'text', { idPrefix: 'EXP' }),
  col('date', 'Date', 'date'),
  col('week', 'Week', 'text', { computed: true }),
  col('month', 'Month', 'text', { computed: true }),
  col('quarter', 'Quarter', 'text', { computed: true }),
  col('market', 'Market', 'text', { validation: 'sheet:' + SHEETS.MARKETS + ':market' }),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('city', 'City'),
  col('campaign', 'Campaign', 'text', { validation: 'sheet:' + SHEETS.CAMPAIGNS + ':campaign' }),
  col('event', 'Event', 'text', { validation: 'sheet:' + SHEETS.EVENTS + ':eventName' }),
  col('businessUnit', 'Business Unit', 'text', { validation: 'sheet:' + SHEETS.BUSINESS_UNITS + ':businessUnit' }),
  col('expenseCategory', 'Expense Category', 'text', { validation: 'EXPENSE_CATEGORIES' }),
  col('expenseDescription', 'Expense Description'),
  col('vendor', 'Vendor'),
  col('budgetedAmount', 'Budgeted Amount', 'currency'),
  col('actualAmount', 'Actual Amount', 'currency'),
  col('variance', 'Variance', 'currency', { computed: true }),
  col('paymentStatus', 'Payment Status', 'text', { validation: 'PAYMENT_STATUS' }),
  col('paymentMethod', 'Payment Method', 'text', { validation: 'PAYMENT_METHODS' }),
  col('invoiceNumber', 'Invoice Number'),
  col('responsiblePerson', 'Responsible Person', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('approvedBy', 'Approved By', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('notes', 'Notes')
];

SHEET_SCHEMA[SHEETS.PIPELINE] = [
  col('opportunityId', 'Opportunity ID', 'text', { idPrefix: 'OPP' }),
  col('organization', 'Organization'),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('city', 'City'),
  col('market', 'Market', 'text', { validation: 'sheet:' + SHEETS.MARKETS + ':market' }),
  col('organizationType', 'Organization Type'),
  col('decisionMaker', 'Decision Maker'),
  col('decisionMakerTitle', 'Decision Maker Title'),
  col('phone', 'Phone'),
  col('email', 'Email'),
  col('linkedin', 'LinkedIn'),
  col('leadSource', 'Lead Source'),
  col('bdOwner', 'BD Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('businessUnit', 'Business Unit', 'text', { validation: 'sheet:' + SHEETS.BUSINESS_UNITS + ':businessUnit' }),
  col('potentialService', 'Potential Service'),
  col('estimatedOpportunityValue', 'Estimated Opportunity Value', 'currency'),
  col('stage', 'Stage', 'text', { validation: 'SALES_STAGES' }),
  col('probabilityPct', 'Probability %', 'percent', { computed: true }),
  col('weightedValue', 'Weighted Value', 'currency', { computed: true }),
  col('firstContactDate', 'First Contact Date', 'date'),
  col('lastContactDate', 'Last Contact Date', 'date'),
  col('nextAction', 'Next Action'),
  col('nextActionDate', 'Next Action Date', 'date'),
  col('expectedCloseDate', 'Expected Close Date', 'date'),
  col('competitor', 'Competitor'),
  col('notes', 'Notes'),
  col('lostReason', 'Lost Reason')
];

SHEET_SCHEMA[SHEETS.TARGET_ACCOUNTS] = [
  col('accountId', 'Account ID', 'text', { idPrefix: 'ACC' }),
  col('organization', 'Organization'),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('city', 'City'),
  col('type', 'Type'),
  col('specialty', 'Specialty'),
  col('website', 'Website'),
  col('ownerGroup', 'Owner / Group'),
  col('ceo', 'CEO'),
  col('coo', 'COO'),
  col('medicalDirector', 'Medical Director'),
  col('qualityDirector', 'Quality Director'),
  col('hrDirector', 'HR Director'),
  col('strategyDirector', 'Strategy Director'),
  col('investmentDirector', 'Investment Director'),
  col('contactInformation', 'Contact Information'),
  col('accreditationStatus', 'Accreditation Status'),
  col('expansionStatus', 'Expansion Status'),
  col('potentialNeed', 'Potential Need'),
  col('priorityTier', 'Priority Tier', 'text', { validation: 'ACCOUNT_TIERS' }),
  col('estimatedOpportunity', 'Estimated Opportunity', 'currency'),
  col('assignedBD', 'Assigned BD', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('lastContact', 'Last Contact', 'date'),
  col('nextAction', 'Next Action'),
  col('notes', 'Notes')
];

SHEET_SCHEMA[SHEETS.CAMPAIGNS] = [
  col('campaignId', 'Campaign ID', 'text', { idPrefix: 'CMP' }),
  col('campaign', 'Campaign'),
  col('market', 'Market', 'text', { validation: 'sheet:' + SHEETS.MARKETS + ':market' }),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('start', 'Start', 'date'),
  col('end', 'End', 'date'),
  col('businessObjective', 'Business Objective'),
  col('targetAudience', 'Target Audience'),
  col('coreMessage', 'Core Message'),
  col('product', 'Product'),
  col('channel', 'Channel', 'text', { validation: 'CAMPAIGN_TYPES' }),
  col('budget', 'Budget', 'currency'),
  col('actualSpend', 'Actual Spend', 'currency'),
  col('leads', 'Leads', 'number'),
  col('qualifiedLeads', 'Qualified Leads', 'number'),
  col('meetings', 'Meetings', 'number'),
  col('proposals', 'Proposals', 'number'),
  col('wins', 'Wins', 'number'),
  col('revenueInfluenced', 'Revenue Influenced', 'currency'),
  col('pipelineInfluenced', 'Pipeline Influenced', 'currency'),
  col('costPerLead', 'Cost per Lead', 'currency', { computed: true }),
  col('costPerQualifiedLead', 'Cost per Qualified Lead', 'currency', { computed: true }),
  col('roi', 'ROI', 'percent', { computed: true }),
  col('owner', 'Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('status', 'Status'),
  col('lessonsLearned', 'Lessons Learned')
];

SHEET_SCHEMA[SHEETS.EVENTS] = [
  col('eventId', 'Event ID', 'text', { idPrefix: 'EVT' }),
  col('eventName', 'Event Name'),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('city', 'City'),
  col('date', 'Date', 'date'),
  col('eventType', 'Event Type', 'text', { validation: 'EVENT_TYPES' }),
  col('targetAudience', 'Target Audience'),
  col('targetAttendees', 'Target Attendees', 'number'),
  col('actualAttendees', 'Actual Attendees', 'number'),
  col('budget', 'Budget', 'currency'),
  col('actualCost', 'Actual Cost', 'currency'),
  col('meetingsGenerated', 'Meetings Generated', 'number'),
  col('qualifiedLeads', 'Qualified Leads', 'number'),
  col('opportunities', 'Opportunities', 'number'),
  col('pipelineGenerated', 'Pipeline Generated', 'currency'),
  col('proposalsGenerated', 'Proposals Generated', 'number'),
  col('contractsWon', 'Contracts Won', 'number'),
  col('revenueGenerated', 'Revenue Generated', 'currency'),
  col('owner', 'Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('eventROI', 'Event ROI', 'percent', { computed: true }),
  col('followUpCompletionPct', 'Follow-Up Completion %', 'percent'),
  col('notes', 'Notes')
];

SHEET_SCHEMA[SHEETS.KPIS] = [
  col('kpiId', 'KPI ID', 'text', { idPrefix: 'KPI' }),
  col('kpiCategory', 'KPI Category', 'text', { validation: 'KPI_CATEGORIES' }),
  col('kpiName', 'KPI Name'),
  col('description', 'Description / Formula'),
  col('target', 'Target', 'text'),
  col('actual', 'Actual', 'text', { computed: true }),
  col('frequency', 'Frequency'),
  col('owner', 'Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' })
];

SHEET_SCHEMA[SHEETS.MARKETS] = [
  col('marketId', 'Market ID', 'text', { idPrefix: 'MKT' }),
  col('market', 'Market'),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('revenueTarget2027', 'Revenue Target 2027', 'currency'),
  col('owner', 'Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('status', 'Status'),
  col('launchMonth', 'Launch Month'),
  col('notes', 'Notes')
];

SHEET_SCHEMA[SHEETS.BUSINESS_UNITS] = [
  col('buId', 'BU ID', 'text', { idPrefix: 'BU' }),
  col('businessUnit', 'Business Unit'),
  col('service', 'Service'),
  col('description', 'Description')
];

SHEET_SCHEMA[SHEETS.TEAM] = [
  col('teamId', 'Team ID', 'text', { idPrefix: 'EMP' }),
  col('name', 'Name'),
  col('email', 'Email'),
  col('role', 'Role'),
  col('responsibilities', 'Responsibilities'),
  col('marketsOwned', 'Markets Owned'),
  col('active', 'Active', 'boolean')
];

SHEET_SCHEMA[SHEETS.CLIENTS] = [
  col('clientId', 'Client ID', 'text', { idPrefix: 'CLI' }),
  col('clientName', 'Client Name'),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('city', 'City'),
  col('market', 'Market', 'text', { validation: 'sheet:' + SHEETS.MARKETS + ':market' }),
  col('sector', 'Sector'),
  col('primaryContact', 'Primary Contact'),
  col('title', 'Title'),
  col('phone', 'Phone'),
  col('email', 'Email'),
  col('relationshipOwner', 'Relationship Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('clientSince', 'Client Since', 'date'),
  col('status', 'Status'),
  col('notes', 'Notes')
];

SHEET_SCHEMA[SHEETS.PROJECTS] = [
  col('projectId', 'Project ID', 'text', { idPrefix: 'PRJ' }),
  col('projectName', 'Project Name'),
  col('clientId', 'Client ID', 'text', { validation: 'sheet:' + SHEETS.CLIENTS + ':clientId' }),
  col('revenueId', 'Revenue ID', 'text', { validation: 'sheet:' + SHEETS.REVENUE + ':revenueId' }),
  col('businessUnit', 'Business Unit', 'text', { validation: 'sheet:' + SHEETS.BUSINESS_UNITS + ':businessUnit' }),
  col('service', 'Service'),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('market', 'Market', 'text', { validation: 'sheet:' + SHEETS.MARKETS + ':market' }),
  col('pmoOwner', 'PMO Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('startDate', 'Start Date', 'date'),
  col('endDate', 'End Date', 'date'),
  col('status', 'Status'),
  col('percentComplete', '% Complete', 'percent'),
  col('grossMargin', 'Gross Margin', 'percent'),
  col('consultantUtilization', 'Consultant Utilization', 'percent'),
  col('nps', 'NPS', 'number'),
  col('scopeCreep', 'Scope Creep Case?', 'boolean'),
  col('notes', 'Notes')
];

SHEET_SCHEMA[SHEETS.PARTNERSHIPS] = [
  col('partnershipId', 'Partnership ID', 'text', { idPrefix: 'PTN' }),
  col('partner', 'Partner'),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('company', 'Company'),
  col('contact', 'Contact'),
  col('strategicValue', 'Strategic Value'),
  col('marketAccess', 'Market Access'),
  col('healthcareAccess', 'Healthcare Access'),
  col('governmentAccess', 'Government Access'),
  col('commercialTerms', 'Commercial Terms'),
  col('commission', 'Commission', 'percent'),
  col('exclusivity', 'Exclusivity'),
  col('agreementStart', 'Agreement Start', 'date'),
  col('agreementEnd', 'Agreement End', 'date'),
  col('opportunitiesGenerated', 'Opportunities Generated', 'number'),
  col('revenueGenerated', 'Revenue Generated', 'currency'),
  col('performance', 'Performance'),
  col('status', 'Status')
];

SHEET_SCHEMA[SHEETS.ACADEMY] = [
  col('academyId', 'Academy ID', 'text', { idPrefix: 'ACD' }),
  col('program', 'Program'),
  col('country', 'Country', 'text', { validation: 'COUNTRIES' }),
  col('audience', 'Audience'),
  col('client', 'Client'),
  col('programType', 'Program Type'),
  col('datesStart', 'Start Date', 'date'),
  col('datesEnd', 'End Date', 'date'),
  col('participants', 'Participants', 'number'),
  col('price', 'Price', 'currency'),
  col('revenue', 'Revenue', 'currency'),
  col('cost', 'Cost', 'currency'),
  col('margin', 'Margin', 'currency', { computed: true }),
  col('leadSource', 'Lead Source'),
  col('upsellOpportunity', 'Upsell Opportunity'),
  col('nps', 'NPS', 'number')
];

SHEET_SCHEMA[SHEETS.CASE_STUDIES] = [
  col('caseStudyId', 'Case Study ID', 'text', { idPrefix: 'CS' }),
  col('caseStudy', 'Case Study'),
  col('client', 'Client'),
  col('sector', 'Sector'),
  col('problem', 'Problem'),
  col('intervention', 'Intervention'),
  col('results', 'Results'),
  col('metrics', 'Metrics'),
  col('accreditation', 'Accreditation'),
  col('testimonial', 'Testimonial'),
  col('pdfReady', 'PDF Ready', 'boolean'),
  col('websiteReady', 'Website Ready', 'boolean'),
  col('linkedinReady', 'LinkedIn Ready', 'boolean'),
  col('videoReady', 'Video Ready', 'boolean'),
  col('salesDeckReady', 'Sales Deck Ready', 'boolean'),
  col('owner', 'Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' })
];

SHEET_SCHEMA[SHEETS.DIGITAL_ROADMAP] = [
  col('featureId', 'Feature ID', 'text', { idPrefix: 'FTR' }),
  col('feature', 'Feature'),
  col('phase', 'Phase'),
  col('owner', 'Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('start', 'Start', 'date'),
  col('deadline', 'Deadline', 'date'),
  col('status', 'Status', 'text', { validation: 'TASK_STATUS' }),
  col('cost', 'Cost', 'currency'),
  col('testing', 'Testing'),
  col('clientFeedback', 'Client Feedback'),
  col('priority', 'Priority', 'text', { validation: 'TASK_PRIORITY' }),
  col('notes', 'Notes')
];

SHEET_SCHEMA[SHEETS.MONTHLY_REVIEW] = [
  col('monthlyReviewId', 'Monthly Review ID', 'text', { idPrefix: 'MR' }),
  col('month', 'Month'),
  col('year', 'Year', 'number'),
  col('revenueTarget', 'Revenue Target', 'currency'),
  col('revenueActual', 'Revenue Actual', 'currency', { computed: true }),
  col('bookingsTarget', 'Bookings Target', 'currency'),
  col('bookingsActual', 'Bookings Actual', 'currency', { computed: true }),
  col('bestMarket', 'Best Market', 'text', { computed: true }),
  col('worstMarket', 'Worst Market', 'text', { computed: true }),
  col('topCampaign', 'Top Campaign', 'text', { computed: true }),
  col('spend', 'Spend', 'currency', { computed: true }),
  col('roi', 'ROI', 'percent', { computed: true }),
  col('dealsLost', 'Deals Lost', 'number', { computed: true }),
  col('lostReasonsSummary', 'Lost Reasons Summary', 'text', { computed: true }),
  col('tasksMissed', 'Tasks Missed', 'number', { computed: true }),
  col('ceoDecisionsNeeded', 'CEO Decisions Needed', 'text'),
  col('changesNextMonth', 'Changes Next Month', 'text'),
  col('generatedSummary', 'Generated Summary', 'text', { computed: true })
];

SHEET_SCHEMA[SHEETS.QUARTERLY_REVIEW] = [
  col('quarterId', 'Quarter ID', 'text', { idPrefix: 'Q' }),
  col('quarter', 'Quarter'),
  col('year', 'Year', 'number'),
  col('revenueTarget', 'Quarter Revenue Target', 'currency'),
  col('revenueActual', 'Quarter Revenue Actual', 'currency', { computed: true }),
  col('bookingsTarget', 'Quarter Bookings Target', 'currency'),
  col('bookingsActual', 'Quarter Bookings Actual', 'currency', { computed: true }),
  col('cumulativeRevenueTarget', 'Cumulative Revenue Target', 'currency'),
  col('gateObjectives', 'Gate Objectives'),
  col('gateStatus', 'Gate Status', 'text', { computed: true }),
  col('pipelineRequirement', 'Pipeline Requirement', 'currency'),
  col('pipelineActual', 'Pipeline Actual', 'currency', { computed: true }),
  col('notes', 'Notes')
];

SHEET_SCHEMA[SHEETS.RISKS] = [
  col('riskId', 'Risk ID', 'text', { idPrefix: 'RSK' }),
  col('risk', 'Risk'),
  col('category', 'Category', 'text', { validation: 'RISK_CATEGORIES' }),
  col('market', 'Market', 'text', { validation: 'sheet:' + SHEETS.MARKETS + ':market' }),
  col('project', 'Project', 'text', { validation: 'sheet:' + SHEETS.PROJECTS + ':projectName' }),
  col('probability', 'Probability', 'number'),
  col('impact', 'Impact', 'number'),
  col('riskScore', 'Risk Score', 'number', { computed: true }),
  col('mitigation', 'Mitigation'),
  col('owner', 'Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('dueDate', 'Due Date', 'date'),
  col('status', 'Status', 'text', { validation: 'RISK_STATUS' })
];

SHEET_SCHEMA[SHEETS.DECISIONS] = [
  col('decisionId', 'Decision ID', 'text', { idPrefix: 'DEC' }),
  col('date', 'Date', 'date'),
  col('meeting', 'Meeting'),
  col('issue', 'Issue'),
  col('decision', 'Decision'),
  col('ceoDecision', 'CEO Decision?', 'boolean'),
  col('decisionOwner', 'Decision Owner', 'text', { validation: 'sheet:' + SHEETS.TEAM + ':name' }),
  col('deadline', 'Deadline', 'date'),
  col('status', 'Status', 'text', { validation: 'DECISION_STATUS' }),
  col('impact', 'Impact'),
  col('notes', 'Notes')
];

/** Returns the ordered header row (array of strings) for a given sheet name. */
function getHeaders(sheetName) {
  var schema = SHEET_SCHEMA[sheetName];
  if (!schema) return [];
  return schema.map(function (c) { return c.header; });
}

/** Returns the schema array for a given sheet name. */
function getSchema(sheetName) {
  return SHEET_SCHEMA[sheetName] || [];
}
