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
