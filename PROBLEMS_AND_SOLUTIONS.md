# RazorRecon AI — Problems & Solutions Log 🛠️

This document logs all technical challenges, edge-case bugs, webhook integration issues, and troubleshooting steps faced during development, testing, and integration of RazorRecon AI, along with their exact solutions.

---

## 📋 Table of Contents
1. [Webhook Stream Already Consumed (`await request.json()`)](#1-webhook-stream-already-consumed-await-requestjson)
2. [HMAC Signature Verification Failure (`401 Unauthorized`)](#2-hmac-signature-verification-failure-401-unauthorized)
3. [Webhook Succeeded (200 OK) but Data Didn't Appear in UI After Recon](#3-webhook-succeeded-200-ok-but-data-didnt-appear-in-ui-after-recon)
4. [Razorpay Webhook Fails when sent to Local Nginx (`https://localhost`)](#4-razorpay-webhook-fails-when-sent-to-local-nginx-httpslocalhost)
5. [Bulk Test Data Loading without Overwriting Existing Seed Records](#5-bulk-test-data-loading-without-overwriting-existing-seed-records)
6. [Windows PowerShell Encoding Error (`UnicodeEncodeError: 'charmap'`)](#6-windows-powershell-encoding-error-unicodeencodeerror-charmap)
7. [Broken Locust Load Test Endpoint (`/api/cashflow/forecast`)](#7-broken-locust-load-test-endpoint-apicashflowforecast)
8. [Deprecated `asyncio.get_event_loop()` in Python 3.10+](#8-deprecated-asyncioget_event_loop-in-python-310)
9. [Hardcoded Mock Values in Frontend Table Component](#9-hardcoded-mock-values-in-frontend-table-component)
10. [Database Truncation Error During CSV Auto-Creation (`StringDataRightTruncation`)](#10-database-truncation-error-during-csv-auto-creation-stringdatarighttruncation)
11. [CORS Preflight Error on OPTIONS Requests (`400 Bad Request`)](#11-cors-preflight-error-on-options-requests-400-bad-request)
12. [Test Database Pollution (`134 Settlements / 17 Breaks`)](#12-test-database-pollution-134-settlements--17-breaks)
13. [Pytest & Linter Module Import Error (`Cannot find module app...`)](#13-pytest--linter-module-import-error-cannot-find-module-app)
14. [Pytest Suite Failures on Clean Database (`UndefinedTable` / `rows_imported == 0`)](#14-pytest-suite-failures-on-clean-database-undefinedtable--rows_imported--0)
15. [IDE Static Analysis Import Resolution Error (`Cannot find module app.database`)](#15-ide-static-analysis-import-resolution-error-cannot-find-module-appdatabase)

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



