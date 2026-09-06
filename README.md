# Eureka 2027 — CEO Execution Management System

A Google Sheets–backed web application for managing and executing Eureka Healthcare
Development Experts' 2027 growth strategy: weekly execution, tasks, budgets, revenue,
sales pipeline, campaigns, markets, events, KPIs, and strategic initiatives — for the CEO
and management team.

- **Backend / database:** Google Sheets (one spreadsheet, 27 structured tabs)
- **Application layer:** Google Apps Script (`src/*.gs`)
- **Frontend:** a single-page app served by Apps Script's `HtmlService` (`src/ui/*.html`) —
  looks and behaves like a management SaaS dashboard, not a spreadsheet in a browser.

This repository ships **two equivalent copies of the same application**:

| Folder | Use it if… | File count |
|---|---|---|
| `src/` | You use `clasp` + git to develop and deploy (multi-file, organized by concern) | 30 files |
| `manual-deploy/` | You want to copy-paste directly into the Apps Script web editor — no clasp, no terminal, no npm | 7 files |

Both contain 100% of the same functionality — `manual-deploy/` is `src/` with every `.gs`
file concatenated into 3 files and every `.html` partial concatenated into 3 files, so
copy-paste deployment has the fewest possible files to create. **If you're not using
clasp/GitHub/terminal, skip straight to Section 3A below and use only `manual-deploy/`.**

---

## 1. Architecture

```
Browser (SPA)  ── google.script.run ──►  Apps Script (Code.gs + api/*.gs)
     ▲                                          │
     │ JSON                                     ▼
     └───────────────────────────────  Google Sheet (00_Settings … 26_Master_Data)
```

- **Data access layer** (`src/data/`) — `SheetService.gs` is the only code that talks to
  `SpreadsheetApp` for reads/writes. Everything else goes through it. Reads for
  dashboard-style aggregation are cached for 90s (`CacheService`) to keep the UI fast
  without hammering the Sheets API; writes go through `LockService` to prevent concurrent
  edits from corrupting rows.
- **Config layer** (`src/config/`) — `Constants.gs` holds every enum, threshold, and 2027
  target number. `SheetSchema.gs` is the single relational model: one entry per sheet
  column (key, header, type, validation source). Nothing else hardcodes a sheet name,
  column position, or target figure — change a target in `Constants.gs` and it propagates
  everywhere (dashboard, alerts, KPI actuals, monthly summary).
- **Setup layer** (`src/setup/`) — idempotent scripts that build the 27 tabs, apply data
  validation / conditional formatting / protection, and seed master + strategy data. Safe
  to re-run at any time from the **Eureka 2027** spreadsheet menu.
- **API layer** (`src/api/`) — one file per business module (Tasks, Revenue, Expenses,
  Pipeline, Campaigns, Events, KPIs, Markets, Alerts, Monthly Review, Weekly Review,
  Dashboard, generic CRUD for reference tables). Every function callable from the browser
  is prefixed `api_` and returns `{ ok, data }` or `{ ok:false, error }` — the frontend
  never sees a raw exception.
- **UI layer** (`src/ui/`) — `Index.html` is the shell; `JS_Core.html` holds state, the
  `google.script.run` wrapper, and generic table/chart/modal builders; `JS_Views.html`
  renders every nav section; `JS_Forms.html` holds the CRUD modals.

### Why Apps Script executes as the deploying user

`appsscript.json` sets `"executeAs": "USER_DEPLOYING"` and `"access": "DOMAIN"`. That means:
- The app runs with **your** Google account's Sheet access — teammates don't need direct
  edit access to the spreadsheet, only to the web app URL.
- Only people inside your Google Workspace domain can open the URL at all (see Section 9,
  Data Safety, for the alternative if you don't have Workspace).

---

## 2. Google Sheet structure (27 tabs)

| # | Tab | Purpose |
|---|-----|---------|
| 00 | `00_Settings` | Company-level config and 2027 north-star numbers |
| 01 | `01_CEO_Dashboard` | Live-formula summary for anyone opening the raw Sheet |
| 02 | `02_Weekly_CEO` | Live-formula "this week" summary |
| 03 | `03_2027_Master_Plan` | One row per month: theme, targets, owner (Section 6/7 of the brief) |
| 04 | `04_Weekly_Execution` | One row per ISO-style week (52 rows/year): dates, market, targets |
| 05 | `05_Tasks` | Granular task list, FK'd to a week |
| 06 | `06_Revenue` | Contracts, invoicing, collections, recognized revenue |
| 07 | `07_Expenses` | Budget vs actual spend |
| 08 | `08_Sales_Pipeline` | CRM opportunities with weighted stage values |
| 09 | `09_Target_Accounts` | Named-account database (450-account target) |
| 10 | `10_Campaigns` | Marketing campaigns |
| 11 | `11_Events` | Conferences, roadshows, webinars |
| 12 | `12_KPIs` | KPI master list + live actuals |
| 13 | `13_Markets` | City/country markets + 2027 revenue targets |
| 14 | `14_Business_Units` | 6 business units × their services |
| 15 | `15_Team` | Roles and responsibilities |
| 16 | `16_Clients` | Client master |
| 17 | `17_Projects` | Delivery/PMO tracking |
| 18 | `18_Partnerships` | International partner agreements |
| 19 | `19_Academy` | Training programs |
| 20 | `20_Case_Studies` | Sales-enablement case study readiness |
| 21 | `21_Digital_Roadmap` | Eureka Excellence Portal milestones |
| 22 | `22_Monthly_Review` | Monthly review log (auto-computed on demand by the app) |
| 23 | `23_Quarterly_Review` | The four quarterly gates from Section 17 |
| 24 | `24_Risks` | Risk register |
| 25 | `25_Decisions` | Executive decision log |
| 26 | `26_Master_Data` | Every dropdown list, in one place, for both Apps Script and native Sheets validation |

**Full column-by-column schema for every tab lives in code, not just in this document:**
`src/config/SheetSchema.gs`. That file *is* the authoritative data dictionary — it is what
actually builds the sheets, so it cannot drift out of sync with reality the way a written
spec can.

### Relationship map (foreign keys)

```
13_Markets ─┬─< 06_Revenue.market            13_Markets ─┬─< 07_Expenses.market
            ├─< 08_Sales_Pipeline.market                 ├─< 08_Sales_Pipeline.market
            ├─< 09_Target_Accounts.country               └─< 17_Projects.market
            └─< 24_Risks.market

14_Business_Units ─< 06_Revenue.businessUnit, 08_Sales_Pipeline.businessUnit,
                     07_Expenses.businessUnit, 17_Projects.businessUnit

15_Team ─< 05_Tasks.taskOwner, 06_Revenue.bdOwner, 07_Expenses.responsiblePerson,
           08_Sales_Pipeline.bdOwner, 09_Target_Accounts.assignedBD,
           10_Campaigns.owner, 11_Events.owner, 17_Projects.pmoOwner, 24_Risks.owner,
           25_Decisions.decisionOwner

04_Weekly_Execution.weekId ─< 05_Tasks.weekId  (one week → many tasks)

16_Clients.clientId ─< 17_Projects.clientId
06_Revenue.revenueId ─< 17_Projects.revenueId

10_Campaigns.campaign ─< 07_Expenses.campaign        (spend attribution)
11_Events.eventName   ─< 07_Expenses.event           (spend attribution)
```

IDs are short and sequential (`TSK-0001`, `REV-0037`, …) generated by
`src/data/IdGenerator.gs` — sortable and human-readable, unlike UUIDs, which matters when
a CEO is reading the raw sheet.

### Calculated fields (never hand-typed)

| Sheet | Field(s) | Rule |
|---|---|---|
| Tasks | `trafficLight` | RED if Blocked or past due · YELLOW if due ≤3 days · GREEN otherwise/Completed |
| Revenue | `outstanding`, `daysOutstanding`, `month`, `quarter` | `invoiceAmount − amountCollected`; days from due date to today |
| Expenses | `variance`, `week`, `month`, `quarter` | `budgetedAmount − actualAmount`; week looked up from date range |
| Pipeline | `probabilityPct`, `weightedValue` | Fixed weight per stage (Section 11) × opportunity value |
| Campaigns | `costPerLead`, `costPerQualifiedLead`, `roi` | spend ÷ leads; (revenue influenced − spend) ÷ spend |
| Events | `eventROI` | (revenue generated − actual cost) ÷ actual cost |
| Academy | `margin` | revenue − cost |
| Risks | `riskScore` | probability × impact |

These are recomputed by `recomputeAllCalculatedFields()` (`src/api/Compute.gs`) after every
CRUD write from the web app, and on demand from the spreadsheet menu.

---

## 3A. Manual deployment (no clasp, no terminal, no GitHub)

Everything you need is in the **`manual-deploy/`** folder — 7 files total, meant to be
copy-pasted directly into the Apps Script web editor at script.google.com. Ignore the
`src/` folder entirely for this path; it's the same application split into more files for
git/clasp-based development.

### FILES TO CREATE IN GOOGLE APPS SCRIPT

| # | Filename (exactly as typed in the Apps Script editor) | Type | Source in this repo |
|---|---|---|---|
| 1 | `Code` | Script | `manual-deploy/Code.gs` |
| 2 | `Setup` | Script | `manual-deploy/Setup.gs` |
| 3 | `Backend` | Script | `manual-deploy/Backend.gs` |
| 4 | `Index` | HTML | `manual-deploy/Index.html` |
| 5 | `CSS` | HTML | `manual-deploy/CSS.html` |
| 6 | `JavaScript` | HTML | `manual-deploy/JavaScript.html` |
| 7 | *(manifest — see note below)* | — | `manual-deploy/appsscript.json` |

*Apps Script auto-creates a file named `Code.gs` in every new project — just open it and
replace its contents rather than creating a duplicate.* When you click **+ → Script** for
files 2–3, Apps Script appends `.gs` automatically; when you click **+ → HTML** for files
4–6, it appends `.html` automatically — type only the base name shown above.

### IGNORE these repository files/folders for manual deployment

- The entire `src/` folder (30 files) — that's the clasp/developer copy of the exact same
  app, not needed if you're pasting manually.
- `.clasp.json.example` — only relevant to the clasp workflow.
- `.gitignore` — a git-only file, irrelevant to Apps Script.

### Steps

1. **Create the spreadsheet.** Go to [sheets.google.com](https://sheets.google.com) → new
   blank spreadsheet → name it "Eureka 2027 — CEO Execution System".
2. **Open the script editor.** In the Sheet: **Extensions → Apps Script**. This opens a
   bound script project with one default file, `Code.gs`.
3. **Replace `Code.gs`.** Open the `Code` file already there, delete its placeholder
   content, and paste in the full contents of `manual-deploy/Code.gs`.
4. **Add `Setup.gs`.** Click the **+** next to "Files" → **Script**. Name it `Setup` (the
   `.gs` extension is added automatically). Paste in `manual-deploy/Setup.gs`.
5. **Add `Backend.gs`.** Same as step 4, named `Backend`, pasted from
   `manual-deploy/Backend.gs`.
6. **Add `Index.html`.** Click **+ → HTML**. Name it `Index`. Paste in
   `manual-deploy/Index.html`.
7. **Add `CSS.html`.** Click **+ → HTML**. Name it `CSS`. Paste in `manual-deploy/CSS.html`.
8. **Add `JavaScript.html`.** Click **+ → HTML**. Name it `JavaScript`. Paste in
   `manual-deploy/JavaScript.html`.
9. **(Optional) Set the manifest.** Click the gear icon (**Project Settings**) → check
   **"Show 'appsscript.json' manifest file in editor"**. A new `appsscript.json` file
   appears in the file list — open it and replace its contents with
   `manual-deploy/appsscript.json`. This step is optional: it only controls who can access
   the deployed web app by default (see Step 13); you can also set that directly in the
   deployment dialog without touching this file.
10. **Save.** `Ctrl+S` / `Cmd+S`, or the 💾 icon.
11. **Install the data model.** Close the script editor tab and reload the Google Sheet
    tab. A new **Eureka 2027** menu appears at the top. Click it, then run, top to bottom:
    - **1. Build sheet structure**
    - **2. Apply validation & formatting**
    - **3. Seed master + strategy data**

    The first click will show Google's standard authorization prompt ("This app isn't
    verified" is expected for a script you just wrote yourself — click **Advanced → Go to
    [project name] (unsafe)** → **Allow**). This is Google asking your permission for the
    script to edit *your own* spreadsheet; nothing leaves your account.

    (Equivalent one-click shortcut: in the script editor, select the `fullInstall`
    function from the function dropdown at the top and click ▶ **Run** — this does all
    three steps at once.)
12. **Deploy the web app.** Back in the script editor: **Deploy → New deployment** → click
    the gear next to "Select type" → **Web app**. Set **Execute as: Me**, and **Who has
    access:** *Anyone within [your domain]* (Workspace accounts) or *Anyone with the link*
    (personal Gmail — see Section 6, Data Safety, for what that means). Click **Deploy**,
    authorize again if prompted, then copy the web app URL.
13. **Share the URL** with the CEO and management team. They open the link directly —
    they do not need edit access to the underlying Sheet.

To update the app later: edit the relevant file(s) in the script editor, save, then
**Deploy → Manage deployments → ✏️ (edit) → Version: New version → Deploy**. Saving alone
does not push changes to an already-deployed web app URL.

---

## 3B. Deployment instructions (clasp / developer workflow)

Use this path only if you're comfortable with git, npm, and a terminal — it develops from
the `src/` folder instead of `manual-deploy/`. If you followed Section 3A above, skip this
entirely.

### Step A — Create the spreadsheet and script project (5 minutes)

1. Go to [sheets.google.com](https://sheets.google.com) and create a new blank spreadsheet.
   Name it "Eureka 2027 — CEO Execution System".
2. In the Sheet, open **Extensions → Apps Script**. This creates a bound Apps Script
   project and gives you its Script ID (**Project Settings** → Script ID).

### Step B — Push this code into that project

**Option 1 — clasp (recommended, keeps the Sheet's Apps Script in sync with this repo):**
```bash
npm install -g @google/clasp
clasp login                     # opens a browser to authorize your Google account
cp .clasp.json.example .clasp.json
# edit .clasp.json and paste the Script ID from Step A
clasp push                      # uploads everything under src/
```

**Option 2 — manual copy-paste (no Node/clasp required):** in the Apps Script editor,
create each file listed in `src/` (matching folder-qualified names, e.g. `config/Constants`,
`ui/Index`) and paste its contents. Tedious but works with zero local tooling.

### Step C — Install the data model into the Sheet

Back in the Google Sheet, reload the page — a new **Eureka 2027** menu appears (from
`onOpen()` in `Code.gs`). Run, in order:
1. **Eureka 2027 → 1. Build sheet structure** — creates all 27 tabs with headers.
2. **Eureka 2027 → 2. Apply validation & formatting** — dropdowns, traffic lights, protection.
3. **Eureka 2027 → 3. Seed master + strategy data** — loads business units, team roles,
   markets + 2027 targets, the 12-month master plan, all 52 weeks, and the strategy-derived
   task list. (Or run `fullInstall()` once from the Apps Script editor to do A–C in one call.)

The first run will prompt you to **authorize** the script (it needs permission to edit the
spreadsheet it's bound to) — this is Google's standard consent screen, not a third party.

### Step D — Deploy the web app

1. In the Apps Script editor: **Deploy → New deployment → type: Web app**.
2. **Execute as:** *Me* (matches `USER_DEPLOYING` in `appsscript.json`).
3. **Who has access:** *Anyone within [your Workspace domain]* — keeps the app off the
   open internet while letting any teammate with a company Google account open it without
   individual Sheet-sharing. See Section 9 below if you're on a personal Gmail account
   without Workspace.
4. Click **Deploy**, copy the web app URL, and paste it into `00_Settings` → *Web App URL*
   row so it's easy to find again.
5. Share that URL with the CEO and management team (e.g. pin it in a Slack channel or
   browser bookmark bar). They do **not** need Sheet access — only the URL.

Re-deploying after a code change: **Deploy → Manage deployments → edit (pencil) → New
version → Deploy**. `clasp push` alone does not update a live web app deployment.

---

## 4. User guide

- **Dashboard** — the CEO homepage. Revenue/bookings/pipeline/collections headline tiles,
  progress toward the EGP 10M / 12.7M / 15M scenarios, active alerts, and six charts
  (revenue & bookings vs target by month, revenue by market/business unit, pipeline by
  stage, budget vs actual spend).
- **Weekly Execution** — pick any of the 52 weeks; see its theme, campaign, market, targets,
  and every task due that week, with inline add/edit.
- **Tasks** — the full task manager: filter by status/priority, search, traffic-light
  indicator, CEO-attention flag, add/edit/delete.
- **Sales CRM** — pipeline table with stage, weighted value, next action; summary tiles for
  total/weighted pipeline, coverage ratio, win rate, average deal size.
- **Revenue** — contract → invoice → collection lifecycle, with outstanding receivables and
  DSO computed automatically. This is deliberately **not** the same number as "Sales
  Bookings" or "Pipeline" — see Section 2 of the brief; the schema keeps them as separate
  fields precisely so they never get collapsed into one figure by mistake.
- **Expenses** — budget vs actual with variance, utilization %, and breakdowns by category
  and market.
- **Markets** — a red/yellow/green performance heatmap (achievement vs each market's 2027
  target) plus the full detail table.
- **Campaigns / Events** — marketing and event tracking with ROI, cost-per-lead, and
  pipeline/revenue influenced.
- **Projects / Academy / Partnerships** — delivery, training, and international-partner
  tracking (generic CRUD tables).
- **KPIs** — the full KPI catalogue (Financial / Commercial / Marketing / Delivery /
  Strategic) with live actuals joined in.
- **Monthly Review** — pick a month; get target-vs-actual, best/worst market, top service,
  top pipeline-generating campaign, lost deals & reasons, missed tasks, and an
  **auto-generated rule-based CEO summary paragraph**.
- **CEO Weekly Review** — the Section 16 "start of week" (priorities, sales target, critical/
  blocked/overdue tasks, budget) and "end of week" (completion %, collections, bookings,
  pipeline added, wins, problems, decisions required) screens, auto-detecting the current
  week from today's date.
- **Settings** — tabbed admin area for Team, Markets, Business Units, Clients, Target
  Accounts, Case Studies, Digital Roadmap, Decisions, and Risks, plus a read-only view of
  `00_Settings`.

### Alerts (Section 28), always-on and rule-based

Computed fresh on every dashboard load from `src/api/AlertsApi.gs` — no manual flagging
required: revenue achievement below 80%, pipeline coverage below 2.5×, an overdue Critical
task, a receivable overdue >30 days, a Red-status project, a campaign over budget, an
international market with a target but no open pipeline, a proposal/negotiation with no
next action, an opportunity untouched for 21+ days, and a quarterly gate missed once its
quarter has closed.

---

## 5. What's seeded vs what you enter

**Seeded automatically** (from the strategy brief, so day one isn't a blank slate):
business units & services, team roles, all 10+ markets with their 2027 revenue targets, the
12-month master plan, all 52 weeks with pro-rated weekly targets, a task derived from each
month's stated primary actions for every week (plus two standing weekly cadences — pipeline/
CRM review and CEO/BD sync), the 13 named campaigns and events, the KPI catalogue, and the
four quarterly gates.

**Deliberately left empty** for you to fill with real activity: Revenue, Expenses, and
Sales Pipeline transactional rows, Target Accounts (the 450-account list — no real account
names were provided to seed), Clients, Projects, Case Studies, Partnerships, Academy runs,
Decisions, and Risks. Seeding these with invented company names or numbers would make the
dashboard lie to the CEO on day one — better to start at zero and watch it fill in for real.

---

## 6. Data safety

- The web app is **not** publicly exposed: deployment access is restricted to your Google
  Workspace domain (`"access": "DOMAIN"` in `appsscript.json`). If you're on personal Gmail
  without Workspace, use **Anyone with the link** instead, but understand that means anyone
  who has the URL can open it — treat the link itself as a secret, same as a shared
  document link.
- The script runs `executeAs: USER_DEPLOYING`, so end users never need direct Sheet access
  and can't open the raw spreadsheet unless you separately share it with them.
- No credentials, API keys, or secrets are embedded anywhere in the frontend JavaScript —
  the only privileged calls are `google.script.run`, which routes through Google's own
  authenticated Apps Script execution context, not a bearer token sitting in browser code.
- All generic-CRUD sheet writes are whitelisted server-side (`GENERIC_CRUD_SHEETS` in
  `src/api/ApiHelpers.gs`) so the frontend cannot direct a write at an arbitrary tab.

---

## 7. Recommended V2 improvements

1. **Natural-language CEO summary via an LLM** — the current summary generator
   (`generateCeoSummary_` in `src/api/MonthlyReviewApi.gs`) is intentionally rule-based with
   zero external dependency, per the brief. A V2 could call an LLM API with the same
   computed inputs for a more fluent narrative, with the rule-based version kept as a
   fallback if the API call fails or quota runs out.
2. **Google OAuth-based per-user roles** — today the app trusts the deployment's domain
   restriction. A V2 could check `Session.getActiveUser().getEmail()` against the `15_Team`
   sheet to show/hide modules by role (e.g., Finance sees Revenue/Expenses edit rights,
   BD reps see only their own pipeline).
3. **Email/Slack digest** — a time-driven trigger that emails the CEO the Monday "Start of
   Week" screen and the Friday "End of Week" screen automatically.
4. **Real-time collaboration cues** — surface "last edited by / at" on records using
   `Session.getActiveUser()` and a lightweight audit-log sheet.
5. **CSV/PDF export** — one-click export of the Monthly/Quarterly Review as a formatted PDF
   (`DriveApp` + `Utilities.newBlob`) for board packs.
6. **Target Accounts import wizard** — a CSV upload flow for populating the 450-account
   database in bulk once the real list exists, with de-duplication against existing rows.
7. **Historical trend storage** — the dashboard currently computes everything live; a V2
   could snapshot weekly/monthly KPI actuals into an append-only log sheet so multi-year
   trend charts become possible without re-deriving history from raw transactions.
8. **Mobile app wrapper** — the responsive web app already works on mobile browsers; a thin
   PWA manifest would let the CEO "install" it to a home screen.

---

## 8. Repository layout

```
manual-deploy/              Flattened copy for manual paste into script.google.com (Section 3A)
  Code.gs                   Constants + SheetSchema + doGet()/onOpen()/fullInstall()
  Setup.gs                  Sheet creation, validation/formatting, all seeding
  Backend.gs                Data access, calculated fields, every api_* function
  Index.html                SPA shell
  CSS.html                  Design system
  JavaScript.html           All frontend JS (state, views, CRUD forms)
  appsscript.json           Manifest (execution + access mode)

src/                        Same application, organized by concern for clasp/git development (Section 3B)
  appsscript.json          Apps Script manifest (execution + access mode)
  Code.gs                  doGet(), onOpen() menu, include(), fullInstall()
  config/
    Constants.gs           Every enum, threshold, and 2027 target number
    SheetSchema.gs          The relational model — one entry per column, per sheet
  data/
    SheetService.gs        Generic read/write/cache/lock layer over Sheets
    IdGenerator.gs         Sequential human-readable IDs (TSK-0001, …)
  setup/
    SetupSheets.gs         Builds all 27 tabs + headers + formatting
    SetupValidation.gs     Data validation, conditional formatting, column protection
    SeedData.gs            Business units, team, markets, master plan, campaigns, events, KPIs, quarterly gates, digital roadmap
    SeedWeekly.gs          52 weeks + strategy-derived task list
  api/
    ApiHelpers.gs          Shared filter/whitelist/error-envelope helpers
    Compute.gs             Calculated-field engine (traffic lights, variance, weighting, …)
    RefreshDashboardSheet.gs  Native Sheets formulas for 01_CEO_Dashboard / 02_Weekly_CEO
    DashboardApi.gs, WeeklyApi.gs, TasksApi.gs, RevenueApi.gs, ExpensesApi.gs,
    PipelineApi.gs, CampaignsApi.gs, EventsApi.gs, KpiApi.gs, MarketsApi.gs,
    MonthlyReviewApi.gs, AlertsApi.gs, GenericCrudApi.gs, LookupsApi.gs
  ui/
    Index.html             SPA shell (sidebar, topbar, content mount point)
    CSS_Styles.html        Design system (cards, badges, traffic lights, tables, modals)
    JS_Core.html           State, google.script.run wrapper, table/chart/modal builders
    JS_Views.html          Every nav-section view
    JS_Forms.html          CRUD modal forms
.clasp.json.example        Copy to .clasp.json and add your Script ID to deploy with clasp
```
