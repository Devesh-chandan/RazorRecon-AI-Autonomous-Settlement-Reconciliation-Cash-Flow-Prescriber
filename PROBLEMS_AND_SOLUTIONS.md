# RazorRecon — Problems & Solutions Log 🛠️

This document logs **33 technical failure modes** encountered during the engineering lifecycle of RazorRecon — detailing **what broke (symptoms), why it broke (root causes), the engineering solutions applied, and the key technical takeaways**.

---

## 🛠️ Executive Engineering Summary & System Hardening

| Category | Solved Issues | Core Impact & Solution |
| --- | :---: | --- |
| 🔐 **Webhook Security & Ingestion** | 4 Issues | Fixed HMAC-SHA256 byte stream double-consumption, signature validation bypass in dev mode, and ngrok HTTPS header forwarding. |
| 🐘 **Database, Schema & State Hardening** | 10 Issues | Engineered `auto_heal_schema` to auto-migrate missing Postgres columns on startup, resolved Redis UUID serialization crashes, fixed CSV import deduplication counters. |
| 🤖 **AI Engine & Streaming Reliability** | 5 Issues | Resolved Server-Sent Events (SSE) double-dispatch on browser disconnect, fixed Groq LLM JSON schema validation errors, and Hinglish prompt formatting. |
| 🎨 **Frontend UI & Data Flow** | 8 Issues | Eliminated stale fallback data in breakdown charts, fixed What-If cashflow curve filters for null capture dates, resolved table row clipping. |
| 🧪 **DevOps, CI/CD & Testing** | 6 Issues | Fixed Locust load test endpoint, eliminated Pytest database pollution, resolved Docker container name conflicts. |

---

## 📍 Technical Issue Index

| # | Issue Title | Severity | Category |
| :---: | :--- | :---: | :---: |
| 1 | [Webhook Stream Already Consumed (`await request.json()`)](#1-webhook-stream-already-consumed-await-requestjson) | 🔴 High | Webhooks |
| 2 | [HMAC Signature Verification Failure (`401 Unauthorized`)](#2-hmac-signature-verification-failure-401-unauthorized) | 🔴 High | Security |
| 3 | [Webhook Succeeded (200 OK) but Data Didn't Appear in UI After Recon](#3-webhook-succeeded-200-ok-but-data-didnt-appear-in-ui-after-recon) | 🟡 Med | Recon Pipeline |
| 4 | [Razorpay Webhook Fails when sent to Local Nginx (`https://localhost`)](#4-razorpay-webhook-fails-when-sent-to-local-nginx-httpslocalhost) | 🟡 Med | Deployment |
| 5 | [Bulk Test Data Loading without Overwriting Existing Seed Records](#5-bulk-test-data-loading-without-overwriting-existing-seed-records) | 🟢 Low | Data Ingestion |
| 6 | [Windows PowerShell Encoding Error (`UnicodeEncodeError: 'charmap'`)](#6-windows-powershell-encoding-error-unicodeencodeerror-charmap) | 🟢 Low | Windows CLI |
| 7 | [Broken Locust Load Test Endpoint (`/api/cashflow/forecast`)](#7-broken-locust-load-test-endpoint-apicashflowforecast) | 🟡 Med | Benchmarks |
| 8 | [Deprecated `asyncio.get_event_loop()` in Python 3.10+](#8-deprecated-asyncioget_event_loop-in-python-310) | 🟢 Low | Backend Core |
| 9 | [Hardcoded Mock Values in Frontend Table Component](#9-hardcoded-mock-values-in-frontend-table-component) | 🟡 Med | Frontend UI |
| 10 | [Database Truncation Error During CSV Auto-Creation (`StringDataRightTruncation`)](#10-database-truncation-error-during-csv-auto-creation-stringdatarighttruncation) | 🔴 High | PostgreSQL DB |
| 11 | [CORS Preflight Error on OPTIONS Requests (`400 Bad Request`)](#11-cors-preflight-error-on-options-requests-400-bad-request) | 🔴 High | FastAPI CORS |
| 12 | [Test Database Pollution (`134 Settlements / 17 Breaks`)](#12-test-database-pollution-134-settlements--17-breaks) | 🟡 Med | Pytest Suite |
| 13 | [Pytest & Linter Module Import Error (`Cannot find module app...`)](#13-pytest--linter-module-import-error-cannot-find-module-app) | 🟢 Low | Testing Setup |
| 14 | [Pytest Suite Failures on Clean Database (`UndefinedTable` / `rows_imported == 0`)](#14-pytest-suite-failures-on-clean-database-undefinedtable--rows_imported--0) | 🟡 Med | Pytest Suite |
| 15 | [IDE Static Analysis Import Resolution Error (`Cannot find module app.database`)](#15-ide-static-analysis-import-resolution-error-cannot-find-module-appdatabase) | 🟢 Low | Developer DX |
| 16 | [Docker Container Name Conflicts & Connection Refused (`500 Internal Server Error`)](#16-docker-container-name-conflicts--connection-refused-500-internal-server-error) | 🔴 High | Docker Stack |
| 17 | [Obsolete Docker Compose `version` Attribute Warning](#17-obsolete-docker-compose-version-attribute-warning) | 🟢 Low | DevOps |
| 18 | [Pyrefly Linter Exception Handler Type Mismatch (`bad-argument-type`)](#18-pyrefly-linter-exception-handler-type-mismatch-bad-argument-type) | 🟢 Low | Code Quality |
| 19 | [Product Name Mismatches across Frontend, Backend, Docs, and Scripts](#19-product-name-mismatches-across-frontend-backend-docs-and-scripts) | 🟢 Low | Branding |
| 20 | [Dead Space in Analytics Chart & Container Height Imbalance](#20-dead-space-in-analytics-chart--container-height-imbalance) | 🟢 Low | Frontend UX |
| 21 | [Table Row Vertical Clipping & Missing Pagination Controls](#21-table-row-vertical-clipping--missing-pagination-controls) | 🟡 Med | Frontend UX |
| 22 | [Visual Noise & Visual Fatigue from Repeated High-Contrast Badges](#22-visual-noise--visual-fatigue-from-repeated-high-contrast-badges) | 🟢 Low | Frontend UX |
| 23 | [Top Navbar Progress Bar Layout Compression & Language Switcher Clutter](#23-top-navbar-progress-bar-layout-compression--language-switcher-clutter) | 🟢 Low | Frontend UX |
| 24 | [Un-uniform Initial Idle State Across Overview KPI Cards](#24-un-uniform-initial-idle-state-across-overview-kpi-cards) | 🟢 Low | Frontend UX |
| 25 | [Python `hmac.new` Keyword Argument `TypeError` Crash (`500 Internal Server Error`)](#25-python-hmacnew-keyword-argument-typeerror-crash-500-internal-server-error) | 🔴 High | Backend Auth |
| 26 | [Redis Cache Result Missing Primary Key `id` & UUID Object Deserialization Failure](#26-redis-cache-result-missing-primary-key-id--uuid-object-deserialization-failure) | 🔴 High | Redis Cache |
| 27 | [EventSource SSE Listener Double-Dispatch Bug on Browser Disconnect](#27-eventsource-sse-listener-double-dispatch-bug-on-browser-disconnect) | 🔴 High | Realtime SSE |
| 28 | [Hardcoded `96.0%` Match Rate and Stale Fallbacks in Breakdown Analytics Page](#28-hardcoded-960-match-rate-and-stale-fallbacks-in-breakdown-analytics-page) | 🟡 Med | Frontend UI |
| 29 | [Settlement CSV Auto-Generated Payment ID Truncation Mismatch](#29-settlement-csv-auto-generated-payment-id-truncation-mismatch) | 🟡 Med | CSV Importer |
| 30 | [What-If Cashflow Filter Excluding CSV Orders with Null Capture Dates](#30-what-if-cashflow-filter-excluding-csv-orders-with-null-capture-dates) | 🟡 Med | Analytics |
| 31 | [Third-Party Cron Service Ping Failure (`Failed (output too large)`)](#31-third-party-cron-service-ping-failure-failed-output-too-large) | 🔴 High | Cloud Cron |
| 32 | [Duplicate CSV Import Reporting Error (`rows_skipped == 0` instead of `2`)](#32-duplicate-csv-import-reporting-error-rows_skipped--0-instead-of-2) | 🔴 High | Ingestion |
| 33 | [PostgreSQL Production Startup Crash (`UndefinedColumn: column "gateway" does not exist`)](#33-postgresql-production-deployment-startup-crash-undefinedcolumn-column-gateway-of-relation-settlements-does-not-exist) | 🔴 High | Database Auto-Heal |

---

### 1. Webhook Stream Already Consumed (`await request.json()`)

#### ❌ Problem
Calling `await request.json()` inside `POST /api/webhooks/razorpay` returned empty dict or threw an error, breaking webhook event parsing.

#### 🔍 Root Cause
The endpoint executed `await request.body()` first to extract raw bytes for HMAC-SHA256 signature verification. In Starlette / FastAPI, the HTTP request body stream can only be read once. Calling `await request.json()` afterwards tried to read an already-consumed stream.

#### ✅ Solution
FastAPI automatically parses the JSON body into the `body: dict = Body(...)` parameter before route execution. We removed `request.json()` and used the injected `body` dict parameter directly:
```python
# Use the injected body dictionary directly
payload: dict = body  # Injected by FastAPI from Body(...)
```

---

### 2. HMAC Signature Verification Failure (`401 Unauthorized`)

#### ❌ Problem
Manual webhook requests via Swagger UI or PowerShell returned `{"detail": "Invalid X-Razorpay-Signature"}` with HTTP 401.

#### 🔍 Root Cause
When `RAZORPAY_WEBHOOK_SECRET` is set in `.env`, the server enforces strict HMAC-SHA256 signature checking. Manual POST requests lacked a valid signature computed with that secret.

#### ✅ Solution
- **For Manual PowerShell Testing**: Compute the real HMAC-SHA256 signature before sending:
  ```powershell
  $secret = "rzp_whsec_9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c"
  $body = '{"event":"payment.captured",...}'
  $hmac = [System.Security.Cryptography.HMACSHA256]::new([System.Text.Encoding]::UTF8.GetBytes($secret))
  $signature = [BitConverter]::ToString($hmac.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($body))).Replace("-", "").ToLower()
  Invoke-RestMethod -Uri "http://localhost:8000/api/webhooks/razorpay" -Method Post -Headers @{"X-Razorpay-Signature"=$signature} -Body $body
  ```
- **For Automated CLI Simulation**: Run `python -m app.send_test_webhook` in your `backend/` directory. It generates HMAC-SHA256 signatures automatically and fires paired `payment.captured` and `settlement.processed` events directly to your public ngrok endpoint.
- **For Dev Mode (Swagger UI Testing)**: Set `RAZORPAY_WEBHOOK_SECRET=` (blank) in `backend/.env`. The backend automatically skips signature validation in dev mode.

---

### 3. Webhook Succeeded (200 OK) but Data Didn't Appear in UI After Recon

#### ❌ Problem
After sending a `payment.captured` webhook event, the API returned 200 OK, but clicking **Run Recon** on the frontend did not display the transaction in the Reconciliation Workbench table.

#### 🔍 Root Cause
`payment.captured` creates an **Order** record. However, the 4-pass Reconciliation Pipeline iterates over **Settlement** records (`settlements` table) to perform audit matching against ERP ledgers. Without a `settlement.processed` event, no settlement row existed for the engine to reconcile.

#### ✅ Solution
Send the matching `settlement.processed` webhook payload (or trigger a settlement in Razorpay Dashboard → Settlements → Settle Now). Once both Order and Settlement records exist in PostgreSQL, the AI Engine processes the transaction and renders it on the frontend UI!

---

### 4. Razorpay Webhook Fails when sent to Local Nginx (`https://localhost`)

#### ❌ Problem
Setting Razorpay Webhook URL to local Nginx HTTPS endpoint resulted in webhook delivery failures on Razorpay Dashboard.

#### 🔍 Root Cause
Local Nginx uses a self-signed SSL certificate (`selfsigned.crt`). Razorpay's production webhook servers strictly verify SSL certificates and reject connections with untrusted self-signed SSL handshakes.

#### ✅ Solution
For local webhook testing, bypass local Nginx and point `ngrok` directly to FastAPI on port 8000:
```bash
ngrok http 8000
```
ngrok automatically provisions a trusted CA-signed SSL certificate (`*.ngrok-free.dev`) accepted by Razorpay servers.

---

### 5. Bulk Test Data Loading without Overwriting Existing Seed Records

#### ❌ Problem
Running `python -m app.seed` wiped out all existing data from tables before seeding the 100 benchmark records. There was no built-in command to append extra bulk records for stress testing without deleting existing data.

#### 🔍 Root Cause
`app.seed` was designed as a destructive initial seeder (`db.query(...).delete()`).

#### ✅ Solution
1. Created `backend/app/seed_append.py`:
   ```bash
   python -m app.seed_append 50   # Appends 50 new realistic records
   python -m app.seed_append 500  # Appends 500 new realistic records
   ```
2. Created `backend/app/reset.py` for explicit DB wipes:
   ```bash
   python -m app.reset            # Clears all tables completely (0 records)
   ```

---

### 6. Windows PowerShell Encoding Error (`UnicodeEncodeError: 'charmap'`)

#### ❌ Problem
Running Python scripts from Windows PowerShell threw `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'` during `print()` calls.

#### 🔍 Root Cause
The default Windows console code page (cp1252 / Windows-1252) cannot encode Unicode emoji characters printed by Python's standard `print()` output.

#### ✅ Solution
Replaced Unicode emoji characters in `print()` statements with standard ASCII log indicators (`[+]`, `[SUCCESS]`, `[ERROR]`).

---

### 7. Broken Locust Load Test Endpoint (`/api/cashflow/forecast`)

#### ❌ Problem
Running Locust load testing reported 100% 404 Not Found errors on the cashflow task.

#### 🔍 Root Cause
`tests/locustfile.py` called `self.client.get("/api/cashflow/forecast")`, but the actual FastAPI route defined in `routes/cashflow.py` is `/api/cashflow/{run_id}`.

#### ✅ Solution
Updated `locustfile.py` to use `self.client.get(f"/api/cashflow/{self.run_id}")` with a check verifying `self.run_id` is set.

---

### 8. Deprecated `asyncio.get_event_loop()` in Python 3.10+

#### ❌ Problem
Running background threadpool executors triggered `DeprecationWarning: There is no current event loop` in Python 3.10+.

#### 🔍 Root Cause
`asyncio.get_event_loop()` is deprecated inside asynchronous contexts in modern Python.

#### ✅ Solution
Replaced `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in `reconcile.py`.

---

### 9. Hardcoded Mock Values in Frontend Table Component

#### ❌ Problem
The Reconciliation Workbench table rendered static values (`"Nov 12, 2026"`, `"setl_PKJAgXprC2z4a8"`, `"₹194.30"`) regardless of actual DB record values.

#### 🔍 Root Cause
`ReconWorkbench.jsx` used static fallback values in table cell rendering.

#### ✅ Solution
Added dynamic helper functions:
- `formatDate(isoStr)`: Formats actual `created_at` ISO date into local short date.
- `firstDeltaValue(delta)`: Dynamically extracts the first numeric variance from the `delta` JSON object.
- Replaced hardcoded settlement ID string with `'—'` fallback.

---

### 10. Database Truncation Error During CSV Auto-Creation (`StringDataRightTruncation`)

#### ❌ Problem
Uploading ERP or Settlement CSV files raised `Database commit error: (psycopg2.errors.StringDataRightTruncation) value too long for type character varying(20)`.

#### 🔍 Root Cause
When auto-creating matching `Order` records during CSV import, `payment_id` was constructed as `f"pay_{order_id}"`. When `order_id` had length 18 (e.g. `order_demo_csv_001`), the resulting `payment_id` string became 22 characters long (`pay_order_demo_csv_001`), exceeding the `VARCHAR(20)` column limit of `Order.payment_id`.

#### ✅ Solution
1. Truncated all dynamically constructed `order_id` and `payment_id` string variables to a maximum of 20 characters (`order_id[:20]`, `payment_id[:20]`) inside `ingestion.py`.
2. Updated sample CSV files (`sample_razorpay_settlements.csv` and `sample_erp_ledger.csv`) to use clean short IDs (`order_csv_001`, `pay_csv_001`, `setl_csv_001`) that fit PostgreSQL column limits.

---

### 11. CORS Preflight Error on OPTIONS Requests (`400 Bad Request`)

#### ❌ Problem
The React frontend sending POST requests to `/api/recon/run?scope=all` triggered `OPTIONS /api/recon/run?scope=all 400 Bad Request` in FastAPI backend logs.

#### 🔍 Root Cause
Starlette/FastAPI executes middleware in reverse registration order. Rate-limiting middleware (`SlowAPIMiddleware`) intercepted `OPTIONS` preflight requests before CORS middleware could respond, or local dev origins (`http://127.0.0.1:5173`) were rejected.

#### ✅ Solution
1. Added an explicit HTTP preflight middleware in `main.py` to intercept `OPTIONS` requests and return an immediate `200 OK` with CORS headers (`Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`).
2. Added `allow_origin_regex=r"https?://.*"` to `CORSMiddleware` in `main.py`.

---

### 12. Test Database Pollution (`134 Settlements / 17 Breaks`)

#### ❌ Problem
Running `pytest tests/test_csv_importer.py` caused total dashboard settlements to jump from 122 to 134 and unmatched breaks from 6 to 17.

#### 🔍 Root Cause
FastAPI `TestClient(app)` shared the live database session during unit test execution. The test suite inserted 12 temporary CSV settlement rows (`setl_u_*`) into PostgreSQL. Because these test rows lacked corresponding ERP ledger entries, running reconciliation counted them as 11 extra breaks.

#### ✅ Solution
1. Added an `@pytest.fixture(autouse=True)` in `tests/test_csv_importer.py` to auto-clean all `setl_u_*` and `led_u_*` test rows from PostgreSQL immediately after test execution.
2. Re-seeded the database (`python -m app.seed`) to restore the clean 122 benchmark dataset.

---

### 13. Pytest & Linter Module Import Error (`Cannot find module app...`)

#### ❌ Problem
Running `pytest` from the root directory or inspecting test files in VS Code raised `ModuleNotFoundError: No module named 'app'`.

#### 🔍 Root Cause
Test files imported `from app.engine...`, but `app` is located inside `backend/app`. Root-level execution did not automatically include `backend/` in Python's module search path (`sys.path`).

#### ✅ Solution
1. Configured `pythonpath = backend` inside `pytest.ini`.
2. Created `tests/conftest.py` that prepends `backend/` to `sys.path` automatically for IDE linters (Pylance/Pyright) and pytest runners.

---

### 14. Pytest Suite Failures on Clean Database (`UndefinedTable` / `rows_imported == 0`)

#### ❌ Problem
Running `pytest tests/ -v` on fresh database instances (e.g. CI runner with a clean PostgreSQL container) caused 5 out of 21 tests to fail. Webhook tests failed with `(psycopg2.errors.UndefinedTable) relation "orders"/"settlements" does not exist` (500 Error), while CSV import tests failed with `assert 0 == 2` and `assert 0 == 1`.

#### 🔍 Root Cause
Database ORM models (`Order`, `Settlement`, `ErpLedger`, `ReconRun`, `ReconResult`) were defined in `backend/app/models.py`, but `Base.metadata.create_all(bind=engine)` was only executed inside `backend/app/seed.py`. Without explicit table creation before running tests or app startup, fresh databases lacked required tables.

#### ✅ Solution
1. Added an `autouse=True` session-scoped fixture `setup_test_database()` in `tests/conftest.py` executing `Base.metadata.create_all(bind=engine)`.
2. Added `Base.metadata.create_all(bind=engine)` to FastAPI's startup `lifespan` handler in `backend/app/main.py`.

---

### 15. IDE Static Analysis Import Resolution Error (`Cannot find module app.database`)

#### ❌ Problem
IDE static analysis engines (Pyright, Pylance, Pyrefly) displayed static diagnostics such as `Cannot find module app.database` and `Cannot find module app.models` when opening test files like `tests/conftest.py`.

#### 🔍 Root Cause
Static type checkers analyze top-level module imports at analysis time before dynamic `sys.path.insert()` logic executes at runtime. Because `app` is located inside `backend/app/`, static analysis looking from the workspace root failed to locate `app`.

#### ✅ Solution
1. Deferred `app.*` imports inside the `setup_test_database()` fixture function in `tests/conftest.py` so dynamic `sys.path` modifications run prior to module resolution.
2. Created `pyrightconfig.json` and `pyproject.toml` with `extraPaths = ["backend"]` and `pythonpath = ["backend"]` to statically declare `backend/` as an additional top-level search path for IDE linters.

---

### 16. Docker Container Name Conflicts & Connection Refused (`500 Internal Server Error`)

#### ❌ Problem
Running `docker compose up -d` failed with `Conflict. The container name "/razorrecon_postgres" is already in use by container "..."`. Because services failed to start up, triggering `/api/recon/run` returned HTTP 500 with `psycopg2.OperationalError: connection to server at "localhost", port 5432 failed: Connection refused`.

#### 🔍 Root Cause
Pre-existing stopped container instances created under the same container names (`razorrecon_postgres`, `razorrecon_redis`) occupied Docker's container name registry, preventing Docker Compose from creating and launching fresh containers.

#### ✅ Solution
Force-removed stale container instances and re-launched Docker Compose:
```bash
docker rm -f razorrecon_postgres razorrecon_redis
docker compose up -d
$env:PYTHONIOENCODING="utf-8"; python -m app.seed
```

---

### 17. Obsolete Docker Compose `version` Attribute Warning

#### ❌ Problem
Running `docker compose` commands emitted warning messages:
`level=warning msg="C:\...\docker-compose.yml: the attribute 'version' is obsolete, it will be ignored, please remove it to avoid potential confusion"`.

#### 🔍 Root Cause
Docker Compose v2 deprecated top-level `version: "3.x"` declarations in compose files as part of the unified Compose Specification standard.

#### ✅ Solution
Removed `version: "3.9"` from both `docker-compose.yml` and `docker-compose.prod.yml`.

---

### 18. Pyrefly Linter Exception Handler Type Mismatch (`bad-argument-type`)

#### ❌ Problem
IDE static type checker (Pyrefly) highlighted `app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)` in `backend/app/main.py` with `bad-argument-type`.

#### 🔍 Root Cause
Starlette's `add_exception_handler` expects a callback with signature `(Request, Exception) -> Response`. SlowAPI's `_rate_limit_exceeded_handler` explicitly types its parameter as `(Request, RateLimitExceeded) -> Response`. Static type checkers enforce parameter contravariance, flagging the subtype requirement.

#### ✅ Solution
19. [Product Name Mismatches across Frontend, Backend, Docs, and Scripts](#19-product-name-mismatches-across-frontend-backend-docs-and-scripts)
20. [Dead Space in Analytics Chart & Container Height Imbalance](#20-dead-space-in-analytics-chart--container-height-imbalance)
21. [Table Row Vertical Clipping & Missing Pagination Controls](#21-table-row-vertical-clipping--missing-pagination-controls)
22. [Visual Noise & Visual Fatigue from Repeated High-Contrast Badges](#22-visual-noise--visual-fatigue-from-repeated-high-contrast-badges)
23. [Top Navbar Progress Bar Layout Compression & Language Switcher Clutter](#23-top-navbar-progress-bar-layout-compression--language-switcher-clutter)
24. [Un-uniform Initial Idle State Across Overview KPI Cards](#24-un-uniform-initial-idle-state-across-overview-kpi-cards)

---

### 19. Product Name Mismatches across Frontend, Backend, Docs, and Scripts

#### ❌ Problem
The project used inconsistent naming variations (`RazorRecon & Flow`, `RazorRecon AI`, `RazorRecon-AI`, `razorrecon-ai`) across HTML `<title>`, UI tooltips, FastAPI backend `title`, Makefile, shell scripts, and Markdown logs.

#### 🔍 Root Cause
Different features and documentation pages were written at different development phases using varying suffixes.

#### ✅ Solution
Standardized all user-facing product display titles to **`RazorRecon`** across `frontend/index.html`, `backend/app/main.py`, `Sidebar.jsx`, `quickstart.sh`, `Makefile`, and `README.md`, while preserving lowercase database and cache slugs (`razorrecon`).

---

### 20. Dead Space in Analytics Chart & Container Height Imbalance

#### ❌ Problem
The **7-Day Cash Flow** card stretched vertically to match the table's height, creating a massive blank void across the top half of the widget.

#### 🔍 Root Cause
`CashFlowChart` was configured with `height: 100%` in the split workbench right panel without a fixed height constraint or secondary stacked widget.

#### ✅ Solution
Rebalanced the right panel layout by setting a fixed chart height (`280px`) on `CashFlowChart` and stacking a secondary `Gateway Volume Distribution` widget beneath it to display real-time gateway channel volume splits (Razorpay Cards/Netbanking 68%, UPI Auto-Collect 22%, BNPL/Subscriptions 10%).

---

### 21. Table Row Vertical Clipping & Missing Pagination Controls

#### ❌ Problem
The settlements table rendered all records in a single scrolling list, vertically slicing the bottom row in half without container boundaries or pagination controls.

#### 🔍 Root Cause
Lack of client-side pagination bounds and container overflow styling in `ReconWorkbench.jsx`.

#### ✅ Solution
1. Added 10-item client-side pagination (`currentPage`, `pageSize = 10`) in `ReconWorkbench.jsx`.
2. Created a sticky table footer featuring `Showing 1–10 of 100 records` with `Prev` and `Next` pagination controls and `1 / 10` page indicator.

---

### 22. Visual Noise & Visual Fatigue from Repeated High-Contrast Badges

#### ❌ Problem
Every visible row rendered identical bright green `Processed` pills and bright blue `Pass 1` boxes, creating visual fatigue and obscuring actual break exceptions (`1 Break`).

#### 🔍 Root Cause
Uniform high-contrast badge styling applied across matched and break records alike.

#### ✅ Solution
Updated normal matched rows to render a subtle `● Processed` indicator in muted slate text (`color: #475569`), neutral pass tags (`Pass 1`), allowing break exceptions (`1 Break` in amber/red alert badge) to stand out immediately.

---

### 23. Top Navbar Progress Bar Layout Compression & Language Switcher Clutter

#### ❌ Problem
During reconciliation runs, the live progress bar `Pass 4 — AI Diagnostics: 96/100 matched` was jammed directly in the top navbar between search input and status pill, compressing the layout.

#### 🔍 Root Cause
Inline flex placement of progress elements inside the header navigation row.

#### ✅ Solution
1. Moved the live progress bar out of the top navbar into a full-width thin animated progress banner (`.header-progress-banner`) positioned directly beneath the header row.
2. Moved the `EN | HI` language toggle into the user profile menu card to give primary action CTAs (`Import CSV`, `Run Recon`) breathing room.

---

### 24. Un-uniform Initial Idle State Across Overview KPI Cards

#### ❌ Problem
Before executing reconciliation (`!hasData`), the `Current balance` KPI card displayed `₹ 0.00` while all other 3 cards showed `—` and `Awaiting Reconciliation`.

#### 🔍 Root Cause
`KPIRow.jsx` lacked an explicit `!hasData` idle state check for the `Current balance` metric column.

#### ✅ Solution
Added a `!hasData` check to render `—` with `Awaiting Reconciliation` across all 4 KPI metric cards in initial idle state before pipeline execution.

---

### 25. Python `hmac.new` Keyword Argument `TypeError` Crash (`500 Internal Server Error`)

#### ❌ Problem
Every incoming Razorpay webhook POST request crashed with HTTP 500 `TypeError: new() got an unexpected keyword argument 'key'`.

#### 🔍 Root Cause
In Python's standard `hmac` library, `hmac.new(key, msg=None, digestmod='')` enforces positional parameters for `key` and `msg` in CPython. Calling `hmac.new(key=..., msg=..., digestmod=...)` with keyword arguments raises a runtime `TypeError`.

#### ✅ Solution
Updated `app/routes/ingestion.py` to pass parameters positionally:
```python
expected = hmac.new(
    settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
    raw_body,
    hashlib.sha256,
).hexdigest()
```

---

### 26. Redis Cache Result Missing Primary Key `id` & UUID Object Deserialization Failure

#### ❌ Problem
Fetching reconciliation results from Redis cache caused missing React keys (`result.id` returning `undefined`) and occasional Pydantic `ValidationError` when `run_id` was cached as a raw UUID object.

#### 🔍 Root Cause
1. In `app/engine/reconcile.py`, `recon_results_to_insert` objects were added to the DB session, but `all_results_for_cache` was populated before calling `db.flush()`, leaving `r.id` as `None`.
2. `r.run_id` was stored as a Python `uuid.UUID` instance in Redis dicts, causing type mismatch during serialization/deserialization.

#### ✅ Solution
1. Added `db.flush()` immediately after `db.add_all()` to populate database auto-increment primary keys.
2. Explicitly mapped `"id": r.id` and `"run_id": str(r.run_id)` in the Redis caching dictionary payload.

---

### 27. EventSource SSE Listener Double-Dispatch Bug on Browser Disconnect

#### ❌ Problem
Network drops during real-time reconciliation streaming triggered duplicate `RECON_ERROR` state dispatches and threw warnings when calling `.close()` on already-closed `EventSource` instances.

#### 🔍 Root Cause
Both `es.addEventListener('error', ...)` and `es.onerror = ...` executed independently when the browser lost connection, causing double invocation of the error handler callback.

#### ✅ Solution
Created a named single-invocation handler with an `errorFired` boolean guard in `frontend/src/api/client.js`:
```javascript
let errorFired = false;
const handleSseError = (data) => {
  if (errorFired) return;
  errorFired = true;
  onEvent({ event: 'error', data });
  es.close();
};
```

---

### 28. Hardcoded `96.0%` Match Rate and Stale Fallbacks in Breakdown Analytics Page

#### ❌ Problem
The Reconciliation Breakdown page always displayed `96.0% Match Accuracy` regardless of the actual reconciliation run match rate (e.g. 78% or 100%).

#### 🔍 Root Cause
`ReconBreakdownFullView.jsx` hardcoded `96.0%` in its JSX markup instead of connecting to `stats.match_rate` from `ReconciliationContext`.

#### ✅ Solution
Replaced hardcoded string with live context state binding:
```javascript
{stats?.match_rate != null ? `${Number(stats.match_rate).toFixed(1)}%` : '—'}
```

---

### 29. Settlement CSV Auto-Generated Payment ID Truncation Mismatch

#### ❌ Problem
Uploading settlement CSV files with long `entity_id` strings created `payment_id` values that mismatched settlement transaction IDs, breaking Pass 1 deterministic matching.

#### 🔍 Root Cause
`payment_id` was evaluated as `str(data.get("entity_id", "") or f"pay_{order_id}")[:20]`. If `entity_id` was absent, `f"pay_{order_id}"` exceeded 20 chars before slicing, causing improper truncation.

#### ✅ Solution
Cleanly sanitized raw entity ID strings before slice in `app/routes/ingestion.py`:
```python
entity_id_raw = str(data.get("entity_id", "") or "").strip()
payment_id = (entity_id_raw if entity_id_raw else f"pay_{order_id}")[:20]
```

---

### 30. What-If Cashflow Filter Excluding CSV Orders with Null Capture Dates

#### ❌ Problem
Simulating AI break resolution (`POST /api/cashflow/whatif`) failed to reflect cash-flow gains for CSV-imported transactions.

#### 🔍 Root Cause
`what_if_resolve` in `app/engine/cashflow.py` filtered `Order.captured_at.isnot(None)`. CSV-imported orders had dates in `settled_at`, causing them to be excluded from the What-If recomputation loop.

#### ✅ Solution
Removed the overly strict `captured_at.isnot(None)` requirement from the What-If resolution query, allowing all captured and partial refund orders to participate in 7-day cash flow projections.

---

### 31. Third-Party Cron Service Ping Failure (`Failed (output too large)`)

#### ❌ Problem
Pinging `https://razorrecon-backend.onrender.com/api/recon/cron` from external cron job triggers (such as `cron-job.org`) failed with:
`Status: Failed (output too large) — The response was larger than the allowed limit and was aborted. Make the endpoint return less data.`

#### 🔍 Root Cause
1. **HTTP Method Mismatch**: External cron triggers default to HTTP `GET` requests. The endpoint was registered exclusively as `@router.post("/cron")`.
2. **HTML Error Response Overflow**: Calling `GET /api/recon/cron` returned `HTTP 405 Method Not Allowed` with a Render/FastAPI HTML trace page (>10 KB with styles), exceeding cron-job.org's strict 10 KB log limit.

#### ✅ Solution
1. Updated `/api/recon/cron` in `backend/app/routes/recon.py` using `@router.api_route("/cron", methods=["GET", "POST", "HEAD"])` to accept `GET`, `POST`, and `HEAD` methods.
2. Returned a lightweight JSON response (~75 bytes) with `HTTP 200 OK`:
   ```json
   {
     "status": "ok",
     "message": "Reconciliation job started",
     "run_id": "c71a39f6-1234-4567-89ab-cdef01234567"
   }
   ```
3. Updated unit tests in `tests/test_cron_logging.py` to verify both `GET` and `POST` triggers.

---

### 32. Duplicate CSV Import Reporting Error (`rows_skipped == 0` instead of `2`)

#### ❌ Problem
### 31. Third-Party Cron Service Ping Failure (`Failed (output too large)`)

📌 **Severity**: 🔴 Critical Production Issue | **Category**: Cloud Integration / Cron Engine

#### 💥 What Broke (The Symptom)
Setting up automated 15-minute background reconciliation via `cron-job.org` caused cron jobs to fail with `HTTP 405 Method Not Allowed` and `Failed (HTTP response output buffer exceeded limit)`.

#### 🔬 Root Cause (Under the Hood)
The `/api/recon/cron` endpoint only accepted `POST` requests and returned full reconciliation execution logs. Third-party cron pingers send HTTP `GET` or `HEAD` requests by default and have a strict 10 KB response size ceiling. Returning full JSON logs exceeded their log buffer.

#### 🛠️ How We Fixed It (The Engineering Solution)
1. Updated `/api/recon/cron` in `backend/app/routes/recon.py` to accept `GET`, `POST`, and `HEAD` requests.
2. Returned a lightweight JSON response (~75 bytes) containing only status, message, and `run_id`:
   ```json
   {
     "status": "ok",
     "message": "Reconciliation job started",
     "run_id": "c71a39f6-1234-4567-89ab-cdef01234567"
   }
   ```
3. Offloaded the heavy reconciliation process to an asynchronous background task thread (`BackgroundTasks`).

#### 💡 Key Takeaway
Prevented log buffer overflows on third-party cron monitors while enabling background reconciliation.

---

### 32. Duplicate CSV Import Reporting Error (`rows_skipped == 0` instead of `2`)

📌 **Severity**: 🔴 High Impact | **Category**: Data Ingestion & Deduplication

#### 💥 What Broke (The Symptom)
Re-importing a settlement CSV file containing duplicate rows returned `rows_skipped == 0` instead of `2`, causing `pytest tests/test_csv_importer.py` test `test_duplicate_rows_skipped` to fail with `assert 0 == 2`.

#### 🔬 Root Cause (Under the Hood)
In `backend/app/routes/ingestion.py` function `_import_settlements`, when an existing settlement row was found in PostgreSQL, the function executed `imported += 1` instead of `skipped += 1`.

#### 🛠️ How We Fixed It (The Engineering Solution)
Updated duplicate row handling in `_import_settlements` to increment `skipped += 1` when an `existing` record is present:
```python
existing = db.query(Settlement).filter(Settlement.settlement_id == settlement_id).first()
if existing:
    existing.import_source = "csv_import"
    if data.get("gateway"):
        existing.gateway = str(data.get("gateway", "") or "Razorpay Stack")
    skipped += 1
    continue
```

#### 💡 Key Takeaway
Guaranteed mathematical accuracy for batch CSV data deduplication reports.

---

### 33. PostgreSQL Production Deployment Startup Crash (`UndefinedColumn: column "gateway" does not exist`)

📌 **Severity**: 🔴 Critical Deployment Blocker | **Category**: Schema Auto-Healing & Persistence

#### 💥 What Broke (The Symptom)
Deploying backend code updates to production failed during database seeding with `(psycopg2.errors.UndefinedColumn) column "gateway" of relation "settlements" does not exist`.

#### 🔬 Root Cause (Under the Hood)
`Base.metadata.create_all(bind=engine)` only creates tables if they do not exist. On existing production PostgreSQL databases created prior to adding `gateway` and `import_source` columns, `create_all` silently ignored missing columns.

#### 🛠️ How We Fixed It (The Engineering Solution)
1. Engineered `auto_heal_schema(db_engine)` in `backend/app/database.py` using SQLAlchemy `inspect(db_engine)` to automatically inspect table definitions and execute DDL migrations on startup:
   - `ALTER TABLE settlements ADD COLUMN gateway VARCHAR(50);`
   - `ALTER TABLE settlements ADD COLUMN import_source VARCHAR(20) DEFAULT 'seeded';`
   - `ALTER TABLE orders ADD COLUMN refund_amount NUMERIC(12, 2) DEFAULT 0;`
   - `ALTER TABLE orders ADD COLUMN erp_invoice VARCHAR(30);`
2. Integrated `auto_heal_schema(engine)` into application startup (`lifespan` in `main.py`) and dataset seeding (`seed.py`).

#### 💡 Key Takeaway
Zero-downtime, self-healing database schema migrations without requiring manual SQL scripts or breaking production tables.


