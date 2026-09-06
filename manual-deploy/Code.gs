
// ============================================================
// SOURCE: config/Constants.gs
// ============================================================

/**
 * Eureka 2027 CEO Execution System — global constants.
 * Single source of truth for sheet names, enumerations, and strategic targets.
 * Nothing outside this file should hardcode a sheet name or a target number.
 */

var SHEETS = {
  SETTINGS: '00_Settings',
  CEO_DASHBOARD: '01_CEO_Dashboard',
  WEEKLY_CEO: '02_Weekly_CEO',
  MASTER_PLAN: '03_2027_Master_Plan',
  WEEKLY_EXECUTION: '04_Weekly_Execution',
  TASKS: '05_Tasks',
  REVENUE: '06_Revenue',
  EXPENSES: '07_Expenses',
  PIPELINE: '08_Sales_Pipeline',
  TARGET_ACCOUNTS: '09_Target_Accounts',
  CAMPAIGNS: '10_Campaigns',
  EVENTS: '11_Events',
  KPIS: '12_KPIs',
  MARKETS: '13_Markets',
  BUSINESS_UNITS: '14_Business_Units',
  TEAM: '15_Team',
  CLIENTS: '16_Clients',
  PROJECTS: '17_Projects',
  PARTNERSHIPS: '18_Partnerships',
  ACADEMY: '19_Academy',
  CASE_STUDIES: '20_Case_Studies',
  DIGITAL_ROADMAP: '21_Digital_Roadmap',
  MONTHLY_REVIEW: '22_Monthly_Review',
  QUARTERLY_REVIEW: '23_Quarterly_Review',
  RISKS: '24_Risks',
  DECISIONS: '25_Decisions',
  MASTER_DATA: '26_Master_Data'
};

// Order controls tab creation order left-to-right.
var SHEET_ORDER = [
  SHEETS.SETTINGS, SHEETS.CEO_DASHBOARD, SHEETS.WEEKLY_CEO, SHEETS.MASTER_PLAN,
  SHEETS.WEEKLY_EXECUTION, SHEETS.TASKS, SHEETS.REVENUE, SHEETS.EXPENSES,
  SHEETS.PIPELINE, SHEETS.TARGET_ACCOUNTS, SHEETS.CAMPAIGNS, SHEETS.EVENTS,
  SHEETS.KPIS, SHEETS.MARKETS, SHEETS.BUSINESS_UNITS, SHEETS.TEAM,
  SHEETS.CLIENTS, SHEETS.PROJECTS, SHEETS.PARTNERSHIPS, SHEETS.ACADEMY,
  SHEETS.CASE_STUDIES, SHEETS.DIGITAL_ROADMAP, SHEETS.MONTHLY_REVIEW,
  SHEETS.QUARTERLY_REVIEW, SHEETS.RISKS, SHEETS.DECISIONS, SHEETS.MASTER_DATA
];

var FISCAL_YEAR = 2027;

// ---- Section 2: 2027 financial north star ----
var REVENUE_MIN = 10000000;
var REVENUE_TARGET = 12700000;
var REVENUE_STRETCH = 15000000;
var ANNUAL_BOOKINGS_TARGET = 17400000;
var TOTAL_GROWTH_BUDGET_2027 = 1950000;
var PIPELINE_MIN = 38000000;
var PIPELINE_MAX = 40000000;
var PIPELINE_COVERAGE_TARGET = 3; // 3x annual revenue target
var PIPELINE_COVERAGE_ALERT_FLOOR = 2.5;

// ---- Task enumerations (Section 8) ----
var TASK_STATUS = ['Not Started', 'In Progress', 'Waiting', 'Blocked', 'Completed', 'Cancelled'];
var TASK_PRIORITY = ['Critical', 'High', 'Medium', 'Low'];
var TASK_CATEGORIES = [
  'Sales', 'Business Development', 'Marketing', 'Event', 'Partnership',
  'International Expansion', 'Client Delivery', 'Finance', 'Academy',
  'Digital', 'Recruitment', 'Operations', 'CEO', 'Research', 'Case Study',
  'Content', 'PR'
];

// ---- Expense categories (Section 9) ----
var EXPENSE_CATEGORIES = [
  'Travel', 'Flights', 'Hotels', 'Transportation', 'Events', 'Venue',
  'Food & Catering', 'Digital Ads', 'Google Ads', 'LinkedIn Ads', 'Meta Ads',
  'Content Production', 'Design', 'Video', 'Printing', 'PR', 'Consultants',
  'Business Development', 'Partner Commission', 'Software', 'CRM', 'Website',
  'Training', 'Sponsorship', 'Subscriptions', 'Other'
];
var PAYMENT_STATUS = ['Unpaid', 'Partially Paid', 'Paid', 'Overdue'];
var PAYMENT_METHODS = ['Bank Transfer', 'Cheque', 'Cash', 'Credit Card', 'Other'];

// ---- Revenue / collections (Section 10) ----
var COLLECTION_STATUS = ['Not Due', 'Due', 'Overdue', 'Collected', 'Partially Collected'];

// ---- Sales CRM stages with fixed probability weights (Section 11) ----
var SALES_STAGES = [
  { name: 'Target Account', probability: 0.05 },
  { name: 'Contacted', probability: 0.10 },
  { name: 'Meeting Scheduled', probability: 0.20 },
  { name: 'Discovery Completed', probability: 0.30 },
  { name: 'Diagnostic / Assessment', probability: 0.40 },
  { name: 'Proposal Preparation', probability: 0.50 },
  { name: 'Proposal Submitted', probability: 0.60 },
  { name: 'Negotiation', probability: 0.75 },
  { name: 'Verbal Agreement', probability: 0.90 },
  { name: 'Won', probability: 1.00 },
  { name: 'Lost', probability: 0.00 }
];
var OPPORTUNITY_STALE_DAYS = 21; // no activity beyond this => alert

// ---- Campaign types (Section 12) ----
var CAMPAIGN_TYPES = [
  'LinkedIn', 'Google Search', 'Meta', 'Email Outreach', 'CEO Personal Branding',
  'Webinar', 'Roundtable', 'Roadshow', 'Conference', 'Partnership Campaign',
  'PR', 'Direct Outreach', 'Account Based Marketing'
];

// ---- Event types (Section 13) ----
var EVENT_TYPES = [
  'Conference', 'Executive Breakfast', 'Roadshow', 'Roundtable', 'Webinar',
  'Workshop', 'Masterclass', 'Business Mission', 'Client Day', 'Forum', 'Other'
];

// ---- Account tiers (Section 18) ----
var ACCOUNT_TIERS = ['A — Strategic', 'B — Strong Prospect', 'C — Long-Term'];

// ---- Risk register (Section 30) ----
var RISK_CATEGORIES = [
  'Commercial', 'Financial', 'Delivery', 'International', 'People',
  'Compliance', 'Reputation', 'Technology'
];
var RISK_STATUS = ['Open', 'Mitigating', 'Closed', 'Escalated'];

// ---- Decision register (Section 29) ----
var DECISION_STATUS = ['Open', 'Decided', 'Deferred', 'Cancelled'];

// ---- Countries / markets in scope (Section 1) ----
var COUNTRIES = ['Egypt', 'Saudi Arabia', 'Libya', 'Oman', 'UAE'];

// ---- Alert thresholds (Section 28) ----
var ALERT_REVENUE_ACHIEVEMENT_FLOOR = 0.80;
var ALERT_RECEIVABLE_OVERDUE_DAYS = 30;
var ALERT_INACTIVE_OPPORTUNITY_DAYS = OPPORTUNITY_STALE_DAYS;

// ---- Traffic light colors ----
var TRAFFIC_LIGHT = { RED: 'RED', YELLOW: 'YELLOW', GREEN: 'GREEN' };

var CACHE_TTL_SECONDS = 90;

// ============================================================
// SOURCE: config/SheetSchema.gs
// ============================================================

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

// ============================================================
// SOURCE: Code.gs
// ============================================================

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
    .addItem('⚠ Reset ALL data (danger)', 'confirmResetAllData')
    .addToUi();
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
