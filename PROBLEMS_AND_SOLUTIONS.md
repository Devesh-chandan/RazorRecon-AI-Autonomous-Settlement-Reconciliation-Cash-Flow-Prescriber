# RazorRecon — Engineering Issues & Fixes 🛠️

A running log of 33 real technical failure modes encountered while building RazorRecon, why they happened (root cause analysis), and how they were resolved. Covers webhook ingestion, database state, reconciliation/AI core, frontend real-time streaming, and DevOps.

---

## 📊 Summary by Area

| Area | Solved Issues | Focus |
|---|:---:|---|
| 🔐 **Webhook Security & Ingestion** | 4 | HMAC signature handling, request-body double-read, ngrok/SSL local tunneling |
| 🐘 **Database & Schema Hardening** | 10 | Auto-heal migrations on startup, Redis/UUID serialization, CSV dedup counters |
| 🤖 **AI Engine & Streaming Reliability** | 5 | SSE double-dispatch, cron endpoint compatibility, JSON & prompt handling |
| 🎨 **Frontend UI & Data Flow** | 8 | Stale fallback data, filter edge cases, layout clipping, pagination controls |
| 🧪 **DevOps, CI/CD & Testing** | 6 | Locust load test endpoint, pytest DB pollution, Docker container conflicts |

---

## 📍 Index

1. [Webhook stream already consumed (`await request.json()`)](#1)
2. [HMAC signature verification failure (401)](#2)
3. [Webhook returns 200 but data doesn't show up after recon](#3)
4. [Razorpay webhook fails against local Nginx over HTTPS](#4)
5. [Bulk test data loading without wiping existing seed records](#5)
6. [Windows PowerShell Unicode encoding error](#6)
7. [Locust load test hitting the wrong endpoint](#7)
8. [Deprecated `asyncio.get_event_loop()` on Python 3.10+](#8)
9. [Hardcoded mock values in the frontend table](#9)
10. [CSV import truncation error (`StringDataRightTruncation`)](#10)
11. [CORS preflight 400 on OPTIONS requests](#11)
12. [Test suite polluting the live database](#12)
13. [Pytest/linter can't find the `app` module](#13)
14. [Pytest fails on a fresh database (`UndefinedTable`)](#14)
15. [IDE static analysis can't resolve `app.database`](#15)
16. [Docker container name conflicts → connection refused](#16)
17. [Obsolete `version` key in docker-compose.yml](#17)
18. [Linter flags the SlowAPI exception handler signature](#18)
19. [Inconsistent product naming across the codebase](#19)
20. [Dead space in the analytics chart panel](#20)
21. [Table rows clipped, no pagination](#21)
22. [Badge styling causing visual fatigue](#22)
23. [Navbar progress bar cramped against the language switcher](#23)
24. [Inconsistent idle state across KPI cards](#24)
25. [`hmac.new()` TypeError on every webhook](#25)
26. [Redis cache missing `id`, UUID serialization failure](#26)
27. [SSE error handler firing twice on disconnect](#27)
28. [Hardcoded 96.0% match rate on the breakdown page](#28)
29. [CSV-generated payment IDs truncated incorrectly](#29)
30. [What-If cashflow filter dropping CSV orders with null capture dates](#30)
31. [Cron pinger failing on oversized/wrong-method response](#31)
32. [Duplicate CSV rows not counted as skipped](#32)
33. [Production startup crash — missing `gateway` column](#33)

---

<a id="1"></a>
### 1. Webhook stream already consumed (`await request.json()`)

**Symptom:** `await request.json()` inside `POST /api/webhooks/razorpay` returned an empty dict or threw an error.

**Root cause:** The handler called `await request.body()` first to get raw bytes for HMAC verification. Starlette only lets you read the request body stream once, so the later `request.json()` call was reading an already-consumed stream.

**Fix:** FastAPI already parses the body via the `body: dict = Body(...)` parameter before the route runs. Dropped the manual `request.json()` call and used that injected dict directly:

```python
payload: dict = body  # injected by FastAPI from Body(...)
```

---

<a id="2"></a>
### 2. HMAC signature verification failure (401)

**Symptom:** Manual webhook requests from Swagger UI or PowerShell got `{"detail": "Invalid X-Razorpay-Signature"}`.

**Root cause:** With `RAZORPAY_WEBHOOK_SECRET` set, the server enforces HMAC-SHA256 checking, and manual requests weren't signed with that secret.

**Fix — three paths depending on how you're testing:**

- **Manual PowerShell:** compute the signature yourself before sending:
  ```powershell
  $secret = "rzp_whsec_9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c"
  $body = '{"event":"payment.captured",...}'
  $hmac = [System.Security.Cryptography.HMACSHA256]::new([System.Text.Encoding]::UTF8.GetBytes($secret))
  $signature = [BitConverter]::ToString($hmac.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($body))).Replace("-", "").ToLower()
  Invoke-RestMethod -Uri "http://localhost:8000/api/webhooks/razorpay" -Method Post -Headers @{"X-Razorpay-Signature"=$signature} -Body $body
  ```
- **Automated:** `python -m app.send_test_webhook` generates the signature and fires paired `payment.captured` / `settlement.processed` events at the public ngrok URL.
- **Dev mode:** leave `RAZORPAY_WEBHOOK_SECRET=` blank in `backend/.env` — the backend skips signature checks when it's unset.

---

<a id="3"></a>
### 3. Webhook returns 200 but data doesn't show up after recon

**Symptom:** Sending a `payment.captured` event returned 200 OK, but the transaction never appeared in the Reconciliation Workbench after clicking **Run Recon**.

**Root cause:** `payment.captured` only creates an **Order** row. The reconciliation pipeline matches against **Settlement** rows, and without a corresponding `settlement.processed` event, there's nothing to reconcile.

**Fix:** Send the `settlement.processed` payload too (or trigger it from Razorpay Dashboard → Settlements → Settle Now). Once both rows exist, reconciliation picks it up.

---

<a id="4"></a>
### 4. Razorpay webhook fails against local Nginx over HTTPS

**Symptom:** Pointing the Razorpay webhook URL at the local Nginx HTTPS endpoint caused delivery failures on the dashboard.

**Root cause:** Local Nginx uses a self-signed cert. Razorpay's webhook servers verify SSL and reject untrusted self-signed handshakes.

**Fix:** Skip local Nginx for webhook testing and point ngrok straight at FastAPI:
```bash
ngrok http 8000
```
ngrok's `*.ngrok-free.dev` cert is CA-signed and Razorpay accepts it.

---

<a id="5"></a>
### 5. Bulk test data loading without wiping existing seed records

**Symptom:** `python -m app.seed` deleted all existing rows before inserting the 100 benchmark records — no way to append more data for stress testing without losing what was there.

**Root cause:** `app.seed` was written as a destructive initial seeder (`db.query(...).delete()`).

**Fix:** Split it into two scripts:
```bash
python -m app.seed_append 50   # appends 50 records
python -m app.seed_append 500  # appends 500 records
python -m app.reset            # explicit full wipe
```

---

<a id="6"></a>
### 6. Windows PowerShell Unicode encoding error

**Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'` when running scripts from PowerShell.

**Root cause:** The default Windows console code page (cp1252) can't render emoji characters passed to `print()`.

**Fix:** Swapped emoji in log output for plain ASCII markers (`[+]`, `[SUCCESS]`, `[ERROR]`).

---

<a id="7"></a>
### 7. Locust load test hitting the wrong endpoint

**Symptom:** Locust reported 100% 404s on the cashflow task.

**Root cause:** `tests/locustfile.py` called `GET /api/cashflow/forecast`, but the actual route is `/api/cashflow/{run_id}`.

**Fix:** Updated the locustfile to `self.client.get(f"/api/cashflow/{self.run_id}")`, with a guard that `run_id` is set before the call.

---

<a id="8"></a>
### 8. Deprecated `asyncio.get_event_loop()` on Python 3.10+

**Symptom:** `DeprecationWarning: There is no current event loop` from background threadpool executors.

**Root cause:** `asyncio.get_event_loop()` is deprecated in async contexts on modern Python.

**Fix:** Swapped to `asyncio.get_running_loop()` in `reconcile.py`.

---

<a id="9"></a>
### 9. Hardcoded mock values in the frontend table

**Symptom:** The Reconciliation Workbench table always showed the same static values (`"Nov 12, 2026"`, `"setl_PKJAgXprC2z4a8"`, `"₹194.30"`) regardless of what was actually in the DB.

**Root cause:** `ReconWorkbench.jsx` used hardcoded fallback strings in the cell renderers.

**Fix:** Added `formatDate(isoStr)` to format the real `created_at` value and `firstDeltaValue(delta)` to pull the actual first numeric variance out of the `delta` JSON; replaced the hardcoded settlement ID with a `'—'` fallback when one isn't present.

---

<a id="10"></a>
### 10. CSV import truncation error (`StringDataRightTruncation`)

**Symptom:** Uploading ERP/settlement CSVs threw `psycopg2.errors.StringDataRightTruncation: value too long for type character varying(20)`.

**Root cause:** Auto-created `Order` rows built `payment_id` as `f"pay_{order_id}"`. An 18-character `order_id` (e.g. `order_demo_csv_001`) produced a 22-character `payment_id`, over the `VARCHAR(20)` limit.

**Fix:**
1. Truncated `order_id` and `payment_id` to 20 chars in `ingestion.py`.
2. Shortened the sample CSVs (`sample_razorpay_settlements.csv`, `sample_erp_ledger.csv`) to use IDs that fit within the column limit from the start.

---

<a id="11"></a>
### 11. CORS preflight 400 on OPTIONS requests

**Symptom:** POSTs from the React frontend to `/api/recon/run?scope=all` produced `OPTIONS ... 400 Bad Request` in the FastAPI logs.

**Root cause:** Starlette runs middleware in reverse registration order. `SlowAPIMiddleware` was intercepting the OPTIONS preflight before CORS middleware could respond, and dev origins like `http://127.0.0.1:5173` weren't being matched.

**Fix:**
1. Added explicit preflight-handling middleware in `main.py` that returns `200 OK` with the right `Access-Control-Allow-*` headers for `OPTIONS` requests.
2. Added `allow_origin_regex=r"https?://.*"` to `CORSMiddleware`.

---

<a id="12"></a>
### 12. Test suite polluting the live database

**Symptom:** Running `pytest tests/test_csv_importer.py` pushed dashboard settlement counts from 122 to 134 and unmatched breaks from 6 to 17.

**Root cause:** `TestClient(app)` was sharing the live DB session. The suite inserted 12 temp settlement rows (`setl_u_*`) with no matching ERP entries, which reconciliation then flagged as 11 extra breaks.

**Fix:**
1. Added an `autouse=True` fixture in `tests/test_csv_importer.py` to clean up `setl_u_*` / `led_u_*` rows after each run.
2. Re-seeded (`python -m app.seed`) to restore the clean 122-record baseline.

---

<a id="13"></a>
### 13. Pytest/linter can't find the `app` module

**Symptom:** `ModuleNotFoundError: No module named 'app'` when running pytest from the repo root, or in VS Code.

**Root cause:** Test files import `from app.engine...`, but `app` lives in `backend/app`, which isn't on `sys.path` by default from the root.

**Fix:**
1. Set `pythonpath = backend` in `pytest.ini`.
2. Added `tests/conftest.py` to prepend `backend/` to `sys.path` for both pytest and IDE linters.

---

<a id="14"></a>
### 14. Pytest fails on a fresh database (`UndefinedTable`)

**Symptom:** On a clean DB (e.g. a fresh CI Postgres container), 5 of 21 tests failed — webhook tests with `relation "orders"/"settlements" does not exist`, CSV tests with `assert 0 == 2` / `assert 0 == 1`.

**Root cause:** `Base.metadata.create_all(bind=engine)` was only called inside `seed.py`, so nothing created the tables when tests ran against a database that hadn't been seeded first.

**Fix:**
1. Added a session-scoped `autouse=True` fixture `setup_test_database()` in `conftest.py` that calls `create_all`.
2. Also added `create_all` to the FastAPI `lifespan` startup handler in `main.py`, so app startup doesn't depend on seeding either.

---

<a id="15"></a>
### 15. IDE static analysis can't resolve `app.database`

**Symptom:** Pyright/Pylance/Pyrefly flagged `Cannot find module app.database` and `Cannot find module app.models` when opening test files.

**Root cause:** Static type checkers resolve imports before any runtime `sys.path.insert()` logic executes, so they never see the `backend/` path that gets added dynamically.

**Fix:**
1. Moved `app.*` imports inside the `setup_test_database()` fixture body so they're deferred until after the path fix runs.
2. Added `pyrightconfig.json` and `pyproject.toml` with `extraPaths` / `pythonpath` set to `["backend"]` so static analyzers know about it too.

---

<a id="16"></a>
### 16. Docker container name conflicts → connection refused

**Symptom:** `docker compose up -d` failed with `Conflict. The container name "/razorrecon_postgres" is already in use`. Downstream, `/api/recon/run` returned 500 with `connection to server at "localhost", port 5432 failed: Connection refused`.

**Root cause:** Stopped containers from a previous run still held the container names, blocking Compose from creating fresh ones.

**Fix:**
```bash
docker rm -f razorrecon_postgres razorrecon_redis
docker compose up -d
$env:PYTHONIOENCODING="utf-8"; python -m app.seed
```

---

<a id="17"></a>
### 17. Obsolete `version` key in docker-compose.yml

**Symptom:** `the attribute 'version' is obsolete, it will be ignored` warning on every `docker compose` command.

**Root cause:** Compose v2 deprecated the top-level `version:` field.

**Fix:** Removed `version: "3.9"` from both `docker-compose.yml` and `docker-compose.prod.yml`.

---

<a id="18"></a>
### 18. Linter flags the SlowAPI exception handler signature

**Symptom:** Pyrefly flagged `app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)` in `main.py` with `bad-argument-type`.

**Root cause:** Starlette's `add_exception_handler` expects `(Request, Exception) -> Response`, but SlowAPI's handler is typed as `(Request, RateLimitExceeded) -> Response`. Static checkers enforce parameter contravariance here, so the narrower type trips the check.

**Fix:** Added an explicit `# type: ignore[arg-type]` on the registration line with a short comment explaining why (SlowAPI's handler is a valid subtype at runtime; only the static contravariance check objects). No behavior change — this is a type-checker-only false positive.

---

<a id="19"></a>
### 19. Inconsistent product naming across the codebase

**Symptom:** The project name appeared as `RazorRecon & Flow`, `RazorRecon AI`, `RazorRecon-AI`, and `razorrecon-ai` across the HTML title, UI tooltips, FastAPI's `title`, the Makefile, shell scripts, and docs.

**Root cause:** Different features/docs were written at different points using different suffixes.

**Fix:** Standardized every user-facing label to **RazorRecon** across `frontend/index.html`, `backend/app/main.py`, `Sidebar.jsx`, `quickstart.sh`, `Makefile`, and `README.md` — while leaving the lowercase `razorrecon` slug used for DB/cache names untouched.

---

<a id="20"></a>
### 20. Dead space in the analytics chart panel

**Symptom:** The 7-Day Cash Flow card stretched to match the table's height, leaving a large blank area at the top of the widget.

**Root cause:** `CashFlowChart` was set to `height: 100%` with nothing else in the right panel to fill the space.

**Fix:** Fixed the chart height at `280px` and added a second stacked widget below it (`Gateway Volume Distribution` — Cards/Netbanking 68%, UPI Auto-Collect 22%, BNPL/Subscriptions 10%) to use the remaining space.

---

<a id="21"></a>
### 21. Table rows clipped, no pagination

**Symptom:** The settlements table rendered every record in one scrolling list, with the bottom row visually cut in half and no container bounds.

**Root cause:** No client-side pagination or overflow handling in `ReconWorkbench.jsx`.

**Fix:** Added 10-item pagination (`currentPage`, `pageSize = 10`) with a sticky footer showing `Showing 1–10 of 100 records`, `Prev`/`Next` controls, and a `1 / 10` page indicator.

---

<a id="22"></a>
### 22. Badge styling causing visual fatigue

**Symptom:** Every row showed the same bright green `Processed` pill and bright blue `Pass 1` tag, making it hard to spot actual break exceptions like `1 Break`.

**Root cause:** Uniform high-contrast styling was applied to matched rows and exceptions alike.

**Fix:** Muted the normal-case styling — matched rows now show a subtle `● Processed` indicator (`#475569`) and neutral pass tags — so break exceptions in amber/red stand out by contrast instead of competing with everything else.

---

<a id="23"></a>
### 23. Navbar progress bar cramped against the language switcher

**Symptom:** During recon runs, the live progress indicator (`Pass 4 — AI Diagnostics: 96/100 matched`) was squeezed into the top navbar between the search box and status pill.

**Root cause:** The progress element was placed inline in the header's flex row alongside everything else.

**Fix:**
1. Moved the progress bar out of the navbar into a full-width banner (`.header-progress-banner`) below the header.
2. Moved the `EN | HI` language toggle into the profile menu, freeing up room for the primary `Import CSV` / `Run Recon` actions.

---

<a id="24"></a>
### 24. Inconsistent idle state across KPI cards

**Symptom:** Before running a reconciliation, the `Current balance` card showed `₹ 0.00` while the other three showed `—` / `Awaiting Reconciliation`.

**Root cause:** `KPIRow.jsx` was missing the `!hasData` idle check for the balance card specifically.

**Fix:** Added the same `!hasData` check to all four cards so they're consistent before the pipeline has run.

---

<a id="25"></a>
### 25. `hmac.new()` TypeError on every webhook

**Symptom:** Every incoming webhook crashed with `TypeError: new() got an unexpected keyword argument 'key'` (HTTP 500).

**Root cause:** CPython's `hmac.new(key, msg=None, digestmod='')` requires `key` and `msg` to be passed positionally; the code was calling it with keyword arguments.

**Fix:**
```python
expected = hmac.new(
    settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
    raw_body,
    hashlib.sha256,
).hexdigest()
```

---

<a id="26"></a>
### 26. Redis cache missing `id`, UUID serialization failure

**Symptom:** Reconciliation results pulled from Redis were missing `id` (causing React key warnings), and occasionally threw a Pydantic `ValidationError` when `run_id` came back as a raw UUID.

**Root cause:**
1. In `reconcile.py`, results were cached before `db.flush()` ran, so `r.id` was still `None` at cache time.
2. `r.run_id` was stored as a Python `uuid.UUID` object instead of a string, breaking (de)serialization.

**Fix:**
1. Added `db.flush()` right after `db.add_all()` so primary keys are populated before caching.
2. Explicitly cast in the cache payload: `"id": r.id`, `"run_id": str(r.run_id)`.

---

<a id="27"></a>
### 27. SSE error handler firing twice on disconnect

**Symptom:** Network drops during streaming caused duplicate `RECON_ERROR` dispatches, plus warnings from calling `.close()` on an already-closed `EventSource`.

**Root cause:** Both `es.addEventListener('error', ...)` and `es.onerror = ...` were registered and both fired on the same disconnect event.

**Fix:** Added a single named handler with a guard flag in `client.js`:
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

<a id="28"></a>
### 28. Hardcoded 96.0% match rate on the breakdown page

**Symptom:** The Reconciliation Breakdown page always showed `96.0% Match Accuracy`, regardless of the actual run's result (e.g. a run that was really 78% or 100%).

**Root cause:** `ReconBreakdownFullView.jsx` had `96.0%` hardcoded in JSX instead of reading from context.

**Fix:**
```javascript
{stats?.match_rate != null ? `${Number(stats.match_rate).toFixed(1)}%` : '—'}
```

---

<a id="29"></a>
### 29. CSV-generated payment IDs truncated incorrectly

**Symptom:** Settlement CSVs with long `entity_id` values produced `payment_id`s that didn't match the actual transaction IDs, breaking Pass 1 deterministic matching.

**Root cause:** `payment_id` was computed as `str(data.get("entity_id", "") or f"pay_{order_id}")[:20]`. When `entity_id` was missing, `f"pay_{order_id}"` could already exceed 20 characters before the slice was applied, truncating it incorrectly.

**Fix:**
```python
entity_id_raw = str(data.get("entity_id", "") or "").strip()
payment_id = (entity_id_raw if entity_id_raw else f"pay_{order_id}")[:20]
```

---

<a id="30"></a>
### 30. What-If cashflow filter dropping CSV orders with null capture dates

**Symptom:** `POST /api/cashflow/whatif` didn't reflect cash-flow gains for CSV-imported transactions when simulating AI break resolution.

**Root cause:** `what_if_resolve` in `cashflow.py` filtered on `Order.captured_at.isnot(None)`, but CSV-imported orders only had `settled_at` populated, so they were excluded entirely.

**Fix:** Dropped the `captured_at.isnot(None)` filter so captured and partial-refund orders both participate in the 7-day projection regardless of which date field is populated.

---

<a id="31"></a>
### 31. Cron pinger failing on oversized/wrong-method response

**Symptom:** External cron triggers (cron-job.org) hitting `/api/recon/cron` failed with `Failed (output too large)`.

**Root cause:** Two compounding issues:
1. The endpoint was registered as `@router.post("/cron")` only, but third-party cron services default to `GET` requests.
2. `GET /api/recon/cron` therefore returned a `405 Method Not Allowed` with a full HTML/CSS error trace page (>10 KB), which exceeded cron-job.org's 10 KB response limit.

**Fix:**
1. Changed the route to `@router.api_route("/cron", methods=["GET", "POST", "HEAD"])`.
2. Made it return a small JSON response (~75 bytes):
   ```json
   {"status": "ok", "message": "Reconciliation job started", "run_id": "c71a39f6-1234-4567-89ab-cdef01234567"}
   ```
3. Moved the actual reconciliation work to a `BackgroundTasks` job so the response returns immediately.
4. Updated `tests/test_cron_logging.py` to cover both `GET` and `POST` triggers.

---

<a id="32"></a>
### 32. Duplicate CSV rows not counted as skipped

**Symptom:** Re-importing a settlement CSV with duplicate rows returned `rows_skipped == 0` instead of `2`; `test_duplicate_rows_skipped` in `test_csv_importer.py` failed with `assert 0 == 2`.

**Root cause:** In `_import_settlements` (`ingestion.py`), when an existing settlement row was found, the code incremented `imported += 1` instead of `skipped += 1`.

**Fix:**
```python
existing = db.query(Settlement).filter(Settlement.settlement_id == settlement_id).first()
if existing:
    existing.import_source = "csv_import"
    if data.get("gateway"):
        existing.gateway = str(data.get("gateway", "") or "Razorpay Stack")
    skipped += 1
    continue
```

---

<a id="33"></a>
### 33. Production startup crash — missing `gateway` column

**Symptom:** Deploying to production failed during seeding with `psycopg2.errors.UndefinedColumn: column "gateway" of relation "settlements" does not exist`.

**Root cause:** `Base.metadata.create_all(bind=engine)` only creates tables that don't already exist — it doesn't add new columns to tables that were created before `gateway` and `import_source` were added to the model.

**Fix:** Wrote `auto_heal_schema(db_engine)` in `database.py`, using SQLAlchemy's `inspect()` to detect and add missing columns on startup:
```sql
ALTER TABLE settlements ADD COLUMN gateway VARCHAR(50);
ALTER TABLE settlements ADD COLUMN import_source VARCHAR(20) DEFAULT 'seeded';
ALTER TABLE orders ADD COLUMN refund_amount NUMERIC(12, 2) DEFAULT 0;
ALTER TABLE orders ADD COLUMN erp_invoice VARCHAR(30);
```
Wired `auto_heal_schema(engine)` into both the FastAPI `lifespan` startup handler and `seed.py`, so schema drift self-heals on every deploy without manual migrations.