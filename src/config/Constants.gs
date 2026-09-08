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

// ---- Performance: whole-payload caches (Performance Sprint) ----
// These cache the fully-assembled JSON a client receives, not raw sheet rows — cheaper and
// simpler to invalidate than per-sheet caching once several sheets feed one response.
var DASHBOARD_CACHE_KEY = 'perf_dashboard_bootstrap_v1';
var DASHBOARD_CACHE_TTL_SECONDS = 240; // 4 minutes
var LOOKUPS_CACHE_KEY = 'perf_lookups_v1';
var LOOKUPS_CACHE_TTL_SECONDS = 300; // 5 minutes
var DEFAULT_PAGE_SIZE = 50;
var MAX_PAGE_SIZE = 100;
