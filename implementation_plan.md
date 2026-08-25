# RazorRecon — Implementation Plan (v2)

> **LLM-Powered Settlement Reconciliation & Cash-Flow Prescriber**
> Razorpay Buildathon · Track 04: AI Finance Controller

---

## 1. Problem Recap

Razorpay merchants receive daily **net settlements** that lump captured orders, MDR/gateway fees, 18% GST on MDR, refunds, and chargebacks into a single bank credit. Matching these against internal ERP order books across T+1/T+2 cycles is painful (20–40 hrs/week) and leads to breaks, tax errors, and poor cash visibility.

**RazorRecon** is an AI agent that:
1. Auto-reconciles a 100-record synthetic settlement batch (>90% match rate).
2. Explains every mismatch in plain English + Hinglish via LLM.
3. Projects a 7-day forward cash-flow curve and runs "What-If" break-resolution scenarios.

---

## 2. User Review Required

> [!IMPORTANT]
> **LLM Provider**: This plan uses **Llama 3.3 70B Versatile** via **Groq Cloud API** (free tier, ultra-fast ~500 tok/s inference). Requires a `GROQ_API_KEY` stored server-side in `.env`. No API key is ever exposed to the browser.

> [!IMPORTANT]
> **Database**: PostgreSQL + Redis run via Docker Compose. The backend (FastAPI) and frontend (Vite dev server) run directly on your machine for fast iteration. In production, all services would be containerized on Kubernetes (matching Razorpay's EKS deployment).

> [!WARNING]
> **Solo Developer Scope**: This plan is optimized for a single developer over 3–4 days. Optional stretch goals are marked with 🏋️. Skip them if time is tight.

---

## 3. Open Questions

1. **Groq API Key**: Do you already have a Groq Cloud account and API key, or do I need to walk you through setup?
2. **Deployment Target**: Will the demo run locally only, or do you want to deploy (e.g., Railway / Render for backend + Vercel for frontend)?
3. **Razorpay Branding**: How closely should we mirror Razorpay's actual Dashboard UI? Exact font (Muli/Mulish) and colors, or an "inspired by" approach?
4. **Hinglish Depth**: Should the LLM default to English with a toggle for Hinglish, or auto-detect user preference?

---

## 4. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        BROWSER (React + Vite)                        │
│                                                                      │
│  ┌──────────┐ ┌─────────────┐ ┌──────────────┐ ┌────────────────┐   │
│  │  Header   │ │  KPI Cards  │ │ Recon Table  │ │ Cash-Flow Chart│   │
│  └──────────┘ └─────────────┘ └──────┬───────┘ └───────┬────────┘   │
│                                      │                  │            │
│  ┌───────────────────────────────────┐│ ┌───────────────┐            │
│  │     AI Exception Drawer          ││ │  Audit Log    │            │
│  └───────────────────────────────────┘│ └───────────────┘            │
│                                       │                              │
└───────────────────────────────────────┼──────────────────────────────┘
                                        │ REST + SSE
                                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    BACKEND (Python 3.12 + FastAPI)                    │
│                                                                      │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │
│  │ API Routes  │  │  Recon Engine    │  │   LLM Service          │  │
│  │ /api/recon  │──│  4-Pass Pipeline │──│   Groq + Llama 3.3     │  │
│  │ /api/cash   │  │  Deterministic   │  │   Exception Diagnostics│  │
│  │ /api/audit  │  │  + LLM Hybrid    │  │   Cash-Flow Narrative  │  │
│  └──────┬──────┘  └────────┬─────────┘  └────────────────────────┘  │
│         │                  │                                         │
│         ▼                  ▼                                         │
│  ┌─────────────┐  ┌──────────────┐                                  │
│  │  Redis      │  │  PostgreSQL  │                                  │
│  │  Cache +    │  │  Orders      │                                  │
│  │  SSE State  │  │  Settlements │                                  │
│  │             │  │  Recon Runs  │                                  │
│  └─────────────┘  └──────────────┘                                  │
│                                                                      │
│         Docker Compose (postgres:16 + redis:7)                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Why This Mirrors Razorpay's Stack

| Razorpay Production | Our Buildathon Equivalent | Alignment |
|---|---|---|
| Go microservices on EKS | Python FastAPI (single service) | Same containerized microservice pattern; pitch: "In production, the recon engine would be a Go service" |
| MySQL / PostgreSQL | PostgreSQL 16 | Direct match — Razorpay uses both |
| Redis for caching & rate limiting | Redis 7 for recon caching | Direct match |
| Kafka + CDC for event streaming | SSE for live recon progress | Same real-time pattern, hackathon-appropriate |
| Claude Agent SDK (Agent Studio) | Llama 3.3 70B via Groq | Open-source LLM, shows flexibility beyond vendor lock-in |
| Airflow for batch orchestration | On-demand + simulated scheduled recon | Pitch: "In production, this runs as an Airflow DAG" |
| React dashboard | React + Vite SPA | Direct match to Razorpay's web dashboard |
| Docker on Kubernetes (EKS) | Docker Compose locally | Same containerization, simplified for demo |
| Prometheus + Kibana monitoring | `/health` + structured logging | Pitch: "Production deployment adds Prometheus scraping" |

---

## 5. Tech Stack (Final)

| Layer | Choice | Rationale |
|---|---|---|
| **Backend** | Python 3.12 + FastAPI | Razorpay's ML/data stack; async, fast, great LLM ecosystem |
| **ORM** | SQLAlchemy 2.0 + Alembic | Industry standard; mirrors Razorpay's DB access patterns |
| **LLM** | Llama 3.3 70B via Groq Cloud API | Free tier, ~500 tok/s inference, open-source flexibility |
| **LLM SDK** | `groq` Python SDK | Official SDK, OpenAI-compatible interface |
| **Database** | PostgreSQL 16 | Razorpay's production DB choice |
| **Cache** | Redis 7 | Razorpay's production cache; TTL caching for recon results |
| **Data Processing** | pandas + numpy | Quick data manipulation, matches Razorpay's data engineering |
| **Frontend** | Vite 6 + React 19 | Instant HMR, matches Razorpay dashboard tech |
| **Language (FE)** | JavaScript (ES2024) | Fast iteration for hackathon |
| **Styling** | Vanilla CSS + CSS Custom Properties | Razorpay Dashboard-inspired light theme |
| **Charts** | Recharts 2.x | Composable React charts for financial data |
| **Icons** | Lucide React | Lightweight, tree-shakable |
| **State** | React Context + `useReducer` | No external dependency needed |
| **HTTP Client** | `fetch` + `EventSource` (SSE) | Native browser APIs for REST + streaming |
| **Infra** | Docker Compose (Postgres + Redis) | Mirrors Razorpay's containerized infra |
| **Task Queue** | 🏋️ Celery + Redis (stretch) | For async recon jobs in production |

### Why NOT These Alternatives

- **Go backend**: Impressive but doubles the work for a solo developer. Python covers the same ground.
- **Claude / Gemini**: User explicitly chose Llama 3.3 70B via Groq for speed and open-source flexibility.
- **Next.js**: Overkill — no SSR/ISR needed; adds complexity without demo benefit.
- **TailwindCSS**: Not requested; vanilla CSS gives pixel-perfect Razorpay Dashboard fidelity.
- **MongoDB**: Razorpay uses relational DBs (MySQL/PostgreSQL). SQL is the right choice here.

---

## 6. Synthetic Dataset Design

### 6.1 Schema: `orders` Table — Internal ERP Orders (100 records)

```sql
CREATE TABLE orders (
    id              SERIAL PRIMARY KEY,
    order_id        VARCHAR(20) UNIQUE NOT NULL,  -- e.g., "order_RzP8xK2mN3q"
    payment_id      VARCHAR(20) NOT NULL,          -- e.g., "pay_RzP8xK2mN3q"
    amount          DECIMAL(12,2) NOT NULL,         -- Order amount in INR
    currency        VARCHAR(3) DEFAULT 'INR',
    status          VARCHAR(20) NOT NULL,           -- captured | refunded | partial_refund
    method          VARCHAR(20) NOT NULL,           -- upi | card | netbanking | wallet
    created_at      TIMESTAMPTZ NOT NULL,
    captured_at     TIMESTAMPTZ,
    customer_email  VARCHAR(100),
    description     VARCHAR(255),
    refund_amount   DECIMAL(12,2) DEFAULT 0,
    erp_invoice     VARCHAR(30),                    -- e.g., "INV-2026-0842"
    created_in_db   TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.2 Schema: `settlements` Table — Razorpay Gateway Settlements

```sql
CREATE TABLE settlements (
    id              SERIAL PRIMARY KEY,
    entity_id       VARCHAR(20) NOT NULL,           -- Maps to payment_id
    type            VARCHAR(20) NOT NULL,           -- payment | refund | adjustment
    amount          DECIMAL(12,2) NOT NULL,         -- Gross transaction amount
    fee             DECIMAL(12,2) NOT NULL,         -- MDR fee
    tax             DECIMAL(12,2) NOT NULL,         -- 18% GST on MDR
    credit          DECIMAL(12,2) NOT NULL,         -- Net credit = amount - fee - tax
    debit           DECIMAL(12,2) DEFAULT 0,
    settlement_id   VARCHAR(20) NOT NULL,           -- e.g., "setl_RzP9aB3nM4r"
    settlement_utr  VARCHAR(30),                    -- Bank UTR
    settled_at      TIMESTAMPTZ NOT NULL,           -- T+1 or T+2
    order_id        VARCHAR(20) NOT NULL,
    created_in_db   TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.3 Schema: `erp_ledger` Table — Merchant's Internal Ledger

```sql
CREATE TABLE erp_ledger (
    id              SERIAL PRIMARY KEY,
    ledger_id       VARCHAR(20) UNIQUE NOT NULL,    -- e.g., "LED-2026-0842"
    invoice_id      VARCHAR(30) NOT NULL,
    order_id        VARCHAR(20) NOT NULL,
    expected_amount DECIMAL(12,2) NOT NULL,
    recorded_amount DECIMAL(12,2) NOT NULL,         -- May differ (data entry errors)
    payment_method  VARCHAR(20) NOT NULL,
    entry_date      DATE NOT NULL,
    status          VARCHAR(20) NOT NULL,           -- received | pending | disputed
    notes           TEXT DEFAULT '',
    created_in_db   TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.4 Schema: `recon_runs` + `recon_results` Tables — Reconciliation Output

```sql
CREATE TABLE recon_runs (
    id              SERIAL PRIMARY KEY,
    run_id          UUID UNIQUE NOT NULL,
    status          VARCHAR(20) NOT NULL,           -- running | complete | error
    total_records   INT,
    matched_count   INT,
    break_count     INT,
    match_rate      DECIMAL(5,2),
    net_payout      DECIMAL(14,2),
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE TABLE recon_results (
    id              SERIAL PRIMARY KEY,
    run_id          UUID REFERENCES recon_runs(run_id),
    order_id        VARCHAR(20) NOT NULL,
    settlement_id   VARCHAR(20),
    ledger_id       VARCHAR(20),
    pass_number     INT NOT NULL,                   -- 1, 2, 3, or 4
    status          VARCHAR(20) NOT NULL,           -- matched | break | pending
    confidence      DECIMAL(3,2),
    flags           JSONB DEFAULT '[]',             -- ["mdr_variance", "timing_lag"]
    delta           JSONB DEFAULT '{}',             -- {"fee_expected": 99.98, "fee_actual": 102.50}
    root_cause      VARCHAR(50),                    -- For breaks: mdr_variance, missing_erp, etc.
    explanation_en  TEXT,                            -- LLM English explanation
    explanation_hi  TEXT,                            -- LLM Hinglish explanation
    suggested_action TEXT,
    severity        VARCHAR(10),                    -- low | medium | high | critical
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.5 Built-In Edge Cases (Mandatory for "No Cherry-Picking")

| # | Edge Case | How It's Seeded | Count |
|---|---|---|---|
| 1 | **MDR Variance** | `fee` is ±₹0.50–₹5.00 off the expected rate | 8 records |
| 2 | **T+2 Timing Lag** | `settled_at` is T+2 instead of T+1; order appears "missing" on Day 1 | 10 records |
| 3 | **Cross-Midnight Orders** | `created_at` 23:45 IST, `captured_at` 00:02 IST next day → date mismatch | 5 records |
| 4 | **Full Refunds** | Settlement has `type: "refund"` with matching debit; ERP may lack refund entry | 6 records |
| 5 | **Partial Refunds** | `refund_amount` < `amount`; settlement shows adjusted credit | 4 records |
| 6 | **Chargeback Holdbacks** | `type: "adjustment"` with negative credit; no matching ERP entry | 3 records |
| 7 | **Missing ERP Entry** | Order exists in settlements but not in ERP ledger | 4 records |
| 8 | **Duplicate ERP Entry** | Same `order_id` twice in ERP with different amounts | 2 records |
| 9 | **Amount Mismatch** | ERP `recorded_amount` ≠ settlement `amount` (data entry typo) | 5 records |
| 10 | **GST Rounding** | `tax` has ₹0.01 rounding discrepancy vs computed 18% of `fee` | 3 records |
| — | **Clean Matches** | Exact match across all three sources | ~50 records |

**Total: 100 records** → guarantees >90% match rate with clean matches + recoverable edge cases.

---

## 7. Reconciliation Engine — 4-Pass Architecture

The engine processes all 100 records through four sequential passes. Each pass feeds unmatched residuals to the next. **Progress is streamed to the frontend via SSE.**

```
┌─────────────────────────────────────────────────────┐
│                  INPUT (from PostgreSQL)             │
│   orders + settlements + erp_ledger tables           │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  PASS 1: EXACT │   Match on order_id + payment_id
              │  DETERMINISTIC │   + amount (exact ₹ match)
              └───────┬────────┘
                      │ SSE: {"pass":1,"matched":50,"total":100}
                      │ unmatched ↓
              ┌────────────────┐
              │  PASS 2: RULE  │   T+1/T+2 date window, MDR tolerance
              │  BASED         │   ±₹5 fee variance, cross-midnight
              └───────┬────────┘
                      │ SSE: {"pass":2,"matched":75,"total":100}
                      │ unmatched ↓
              ┌────────────────┐
              │  PASS 3: FUZZY │   Amount within ±2%, partial refund
              │  HEURISTIC     │   net-of-refund matching, duplicate
              └───────┬────────┘   detection
                      │ SSE: {"pass":3,"matched":90,"total":100}
                      │ unmatched ↓
              ┌────────────────┐
              │  PASS 4: LLM   │   Llama 3.3 70B analyzes remaining
              │  DIAGNOSTICS   │   breaks with full context
              └───────┬────────┘
                      │ SSE: {"pass":4,"matched":93,"breaks":7,"complete":true}
                      ▼
              ┌────────────────┐
              │  PostgreSQL    │   Results persisted to recon_results
              │  + Redis Cache │   Cached for fast re-reads
              └────────────────┘
```

### 7.1 Pass 1 — Exact Deterministic Match

**File**: `backend/app/engine/pass1_exact.py`

```
Algorithm:
  1. Query all settlements + orders + ERP ledger from PostgreSQL
  2. Build a HashMap: settlement.order_id → settlement record
  3. For each ERP ledger entry:
     a. Lookup by order_id in HashMap
     b. If found AND settlement.amount === erp.expected_amount:
        → MATCH (confidence: 1.0, pass: 1)
     c. Remove matched records from both pools
  4. Return { matched: [...], unmatched_settlements: [...], unmatched_erp: [...] }
  5. SSE emit: pass progress
```

**Expected yield**: ~50 records (the clean matches).

### 7.2 Pass 2 — Rule-Based Contextual Match

**File**: `backend/app/engine/pass2_rules.py`

```
Rules applied to unmatched residuals:

Rule 2A: T+1/T+2 Date Window
  - If settlement.settled_at is within [order.captured_at, order.captured_at + 3 days]:
    → Allow date mismatch, match on order_id + amount

Rule 2B: MDR Fee Tolerance
  - If |settlement.fee - (settlement.amount × expected_mdr_rate)| ≤ ₹5.00:
    → Match with flag "mdr_variance"

Rule 2C: Cross-Midnight Normalization
  - Normalize both dates to IST calendar date (ignore time component)
  - Re-attempt exact match on normalized dates

Rule 2D: GST Rounding Tolerance
  - If |settlement.tax - (settlement.fee × 0.18)| ≤ ₹0.02:
    → Accept with flag "gst_rounding"

Rule 2E: Full Refund Pairing
  - For settlement.type === "refund":
    Match to order where order.status === "refunded"
    AND settlement.debit === order.amount
```

**Expected yield**: ~25 records.

### 7.3 Pass 3 — Fuzzy Heuristic Match

**File**: `backend/app/engine/pass3_fuzzy.py`

```
Heuristics:

H3A: Amount Proximity Match
  - For unmatched pairs sharing same order_id:
    If |settlement.amount - erp.recorded_amount| / settlement.amount ≤ 0.02:
    → Match with flag "amount_mismatch" + delta

H3B: Partial Refund Net Matching
  - Compute: net_expected = order.amount - order.refund_amount
  - If settlement.credit ≈ net_expected (±₹5):
    → Match with flag "partial_refund_adjusted"

H3C: Duplicate Detection
  - Group ERP entries by order_id
  - If count > 1: flag "duplicate_erp_entry", match the first,
    flag second as "duplicate_to_remove"

H3D: Chargeback Identification
  - settlement.type === "adjustment" AND settlement.debit > 0:
    → Tag as "chargeback_holdback", no ERP match expected
```

**Expected yield**: ~15 records.

### 7.4 Pass 4 — LLM Exception Diagnostics (Llama 3.3 70B via Groq)

**File**: `backend/app/engine/pass4_llm.py`

For the remaining ~10 unmatched records, send context to Llama 3.3 via Groq:

```
Prompt Strategy:

SYSTEM: You are a senior fintech reconciliation analyst working with 
Razorpay payment settlements. Analyze each unreconciled break and provide:
1. root_cause: One of [mdr_variance, timing_lag, missing_erp_entry, 
   data_entry_error, chargeback, partial_refund, unknown]
2. explanation_en: 2-3 sentence explanation in professional English
3. explanation_hi: Same explanation in Hinglish (Hindi-English mix)
4. suggested_action: Specific remediation step
5. confidence: 0.0-1.0
6. severity: low | medium | high | critical

USER: Here is the unreconciled record context:
Settlement: {settlement_json}
Closest ERP Match (if any): {erp_json}  
Original Order: {order_json}

Respond in strict JSON format matching the schema above.
```

**Groq Config**:
- Model: `llama-3.3-70b-versatile`
- Temperature: 0.1 (deterministic diagnostics)
- `response_format: { "type": "json_object" }`
- Batch: Send all remaining breaks in one API call
- Fallback: If Groq is unreachable, return template diagnostics (never crash)

### 7.5 Audit Log

Every reconciliation action is stored in `recon_results` with full context:

```json
{
  "run_id": "uuid-...",
  "order_id": "order_RzP8xK2mN3q",
  "pass_number": 2,
  "status": "matched",
  "confidence": 0.92,
  "flags": ["mdr_variance"],
  "delta": { "fee_expected": 99.98, "fee_actual": 102.50, "variance": 2.52 },
  "explanation_en": "MDR fee ₹2.52 higher than expected 2% rate"
}
```

---

## 8. Cash-Flow Prescriber — 7-Day Forward Projection

**File**: `backend/app/engine/cashflow.py`

### 8.1 Model

```
For each day D in [today, today+7]:

  expected_inflow(D) = Σ (order.amount - estimated_mdr - estimated_gst)
                       for orders where:
                         order.status === "captured"
                         AND expected_settlement_date(order) === D

  Where:
    expected_settlement_date(order) =
      order.captured_at + T+1 (weekday) or T+2 (weekend/holiday)
    
    estimated_mdr = order.amount × mdr_rate_by_method(order.method)
    estimated_gst = estimated_mdr × 0.18

  MDR Rates by Method:
    upi:        0.00%  (zero MDR on UPI per RBI mandate)
    card:       2.00%
    netbanking: 1.75%
    wallet:     2.50%
```

### 8.2 What-If Scenario Engine

```
what_if_resolve(break_id):
  1. Load the break's expected_amount from recon_results
  2. Subtract from "disputed/held" bucket
  3. Add to "confirmed_inflow" on the resolution_date
  4. Recompute the 7-day curve
  5. Return delta: { day: D, old_inflow: X, new_inflow: Y, delta: Y-X }
```

### 8.3 LLM Cash-Flow Narrative (🏋️ Stretch Goal)

After computing the numerical forecast, pass it to Llama 3.3 to generate a short executive summary:

```
"You are projected to receive ₹X over the next 7 days. On Day 3 there is a 
risk of shortfall due to unresolved breaks of ₹Y. Resolving the 3 chargeback 
holdbacks would recover ₹Z and smooth your cash position."
```

---

## 9. UI/UX & Aesthetics Blueprint

### 9.1 Design System — Razorpay Dashboard-Inspired (Light Theme)

| Token | Value |
|---|---|
| **Background** | `#f7f8fa` (light gray, Razorpay dashboard bg) |
| **Surface** | `#ffffff` (white cards) |
| **Surface Hover** | `#f0f4f8` |
| **Border** | `#e5e9f0` (subtle gray borders) |
| **Primary Accent** | `#2D81E0` (Razorpay Blue) |
| **Primary Dark** | `#1a5fb4` (hover/active state) |
| **Primary Light** | `#e8f1fc` (subtle blue tint for selected states) |
| **Success** | `#1cb468` (Razorpay-style green) |
| **Warning** | `#e8960c` (amber) |
| **Error** | `#e23744` (Razorpay-style red) |
| **Text Primary** | `#1b1f2a` (near-black) |
| **Text Secondary** | `#6b7280` (gray) |
| **Text Tertiary** | `#9ca3af` (muted) |
| **Font** | Mulish (Razorpay's actual font) — 400, 500, 600, 700 |
| **Monospace Font** | JetBrains Mono — for order IDs, amounts |
| **Border Radius** | 8px (cards), 6px (buttons), 16px (pills) |
| **Shadow** | `0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)` |
| **Shadow Hover** | `0 4px 12px rgba(0,0,0,0.1)` |

### 9.2 Layout — 4 Core Sections

```
┌──────────────────────────────────────────────────────┐
│  🔷 HEADER: Logo + "RazorRecon & Flow" + Language    │
│     Toggle (EN/HI) + Run Reconciliation CTA          │
│     White header with bottom border, clean + minimal │
├──────────────────────────────────────────────────────┤
│  📊 HERO KPI ROW (4 white cards with blue accents)   │
│  ┌──────────┬──────────┬──────────┬──────────┐       │
│  │Total Txns│Match Rate│ Breaks   │Net Payout│       │
│  │   100    │  93%     │   7      │ ₹4.2L    │       │
│  └──────────┴──────────┴──────────┴──────────┘       │
├───────────────────────┬──────────────────────────────┤
│  📋 RECON WORKBENCH   │  📈 CASH-FLOW CHART          │
│  (Left 55%)           │  (Right 45%)                 │
│                       │                              │
│  Tabbed table:        │  7-day area chart with       │
│  • All (100)          │  Razorpay blue gradient      │
│  • Matched (93)       │  • Confirmed inflow (green)  │
│  • Breaks (7)         │  • Disputed/Held (amber)     │
│                       │  • What-If overlay (dashed)  │
│  Each row expandable  │                              │
│  with match details   │  Below: "Resolve Break"      │
│                       │  buttons update chart live    │
├───────────────────────┴──────────────────────────────┤
│  🤖 AI EXCEPTION DRAWER (Bottom / Slide-up Panel)    │
│                                                      │
│  For each break:                                     │
│  ┌────────────────────────────────────────────┐      │
│  │ 🔴 order_RzP... │ Chargeback Holdback      │      │
│  │ EN: "This ₹2,499 payment was disputed..."  │      │
│  │ HI: "Yeh ₹2,499 ka payment dispute mein..."│      │
│  │ Action: "Contact customer / accept loss"    │      │
│  │ [Resolve ✓]  [Escalate ↗]                  │      │
│  └────────────────────────────────────────────┘      │
│                                                      │
│  Full audit log expandable at bottom                 │
└──────────────────────────────────────────────────────┘
```

### 9.3 Animations & Micro-Interactions

| Element | Animation |
|---|---|
| KPI cards on load | `fadeInUp` staggered 100ms each |
| Match rate counter | Animated count-up from 0% → 93% |
| Table row expand | `max-height` transition 300ms ease |
| Cash chart line draw | Recharts `animationDuration={1500}` |
| "Run Recon" button | Blue pulse glow effect while processing, progress bar overlay |
| Break resolution | Row slides out, KPIs + chart update with spring animation |
| Language toggle | Smooth text crossfade |
| AI Drawer | `translateY` slide-up from bottom |
| SSE progress | Live counter update: "Processing... Pass 2 — 75/100 matched" |

---

## 10. API Design

### 10.1 REST Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/recon/run` | Trigger a new reconciliation run. Returns `run_id`. Recon executes async; progress via SSE. |
| `GET` | `/api/recon/stream/{run_id}` | **SSE endpoint** — streams pass-by-pass progress events |
| `GET` | `/api/recon/results/{run_id}` | Full reconciliation results (all 100 records with match/break details) |
| `GET` | `/api/recon/stats/{run_id}` | Aggregated stats: match rate, totals, break count |
| `GET` | `/api/cashflow/{run_id}` | 7-day cash-flow projection data |
| `POST` | `/api/cashflow/whatif` | Body: `{ run_id, break_id }` → Returns updated cash-flow with break resolved |
| `GET` | `/api/audit/{run_id}` | Full audit log for the run |
| `GET` | `/api/audit/{run_id}/export` | Download audit log as JSON file |
| `GET` | `/api/health` | Health check (DB + Redis + Groq connectivity) |

### 10.2 SSE Event Schema

```json
// Progress update (during reconciliation)
{
  "event": "progress",
  "data": {
    "run_id": "uuid-...",
    "pass": 2,
    "pass_name": "Rule-Based Matching",
    "matched_this_pass": 25,
    "total_matched": 75,
    "total_records": 100,
    "elapsed_ms": 1200
  }
}

// Completion
{
  "event": "complete",
  "data": {
    "run_id": "uuid-...",
    "match_rate": 93.0,
    "matched": 93,
    "breaks": 7,
    "net_payout": 421583.47,
    "elapsed_ms": 4500
  }
}

// Error
{
  "event": "error",
  "data": {
    "run_id": "uuid-...",
    "message": "Groq API rate limited. Using template diagnostics for breaks.",
    "fallback": true
  }
}
```

---

## 11. Proposed Changes — File-by-File Breakdown

### 11.0 Project Root

#### [NEW] `docker-compose.yml`
- PostgreSQL 16 service (port 5432, volume-mounted)
- Redis 7 service (port 6379)
- Network: `razorrecon-net`

#### [NEW] `.env.example`
```
# Backend
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://razorrecon:razorrecon@localhost:5432/razorrecon
REDIS_URL=redis://localhost:6379/0

# Frontend
VITE_API_URL=http://localhost:8000
```

#### [NEW] `.gitignore`
- `.env`, `__pycache__/`, `node_modules/`, `.venv/`, `dist/`

---

### 11.1 Backend — Python FastAPI

#### Directory: `backend/`

#### [NEW] `backend/requirements.txt`
```
fastapi==0.115.*
uvicorn[standard]==0.34.*
sqlalchemy==2.0.*
alembic==1.14.*
psycopg2-binary==2.9.*
redis==5.2.*
groq==0.15.*
pandas==2.2.*
numpy==2.1.*
pydantic==2.10.*
sse-starlette==2.2.*
python-dotenv==1.0.*
```

#### [NEW] `backend/app/__init__.py`
- Empty init

#### [NEW] `backend/app/main.py`
- FastAPI app initialization
- CORS middleware (allow Vite dev server origin)
- Include routers: `recon`, `cashflow`, `audit`, `health`
- Startup event: verify DB + Redis connection
- Lifespan handler for clean shutdown

#### [NEW] `backend/app/config.py`
- Pydantic `Settings` class loading from `.env`
- `GROQ_API_KEY`, `DATABASE_URL`, `REDIS_URL`
- MDR rate constants, tolerance thresholds

#### [NEW] `backend/app/database.py`
- SQLAlchemy engine + session factory
- `get_db()` dependency for FastAPI routes

#### [NEW] `backend/app/models.py`
- SQLAlchemy ORM models for all tables (§6.1–6.4)
- `Order`, `Settlement`, `ErpLedger`, `ReconRun`, `ReconResult`

#### [NEW] `backend/app/schemas.py`
- Pydantic request/response schemas
- `ReconRunResponse`, `ReconResultResponse`, `CashFlowResponse`, `WhatIfRequest`, `AuditLogEntry`

#### [NEW] `backend/app/cache.py`
- Redis client initialization
- `cache_results(run_id, data, ttl=300)` — cache recon results for 5 minutes
- `get_cached_results(run_id)` — retrieve from cache before hitting DB
- `invalidate(run_id)` — clear on what-if resolution

---

#### [NEW] `backend/app/routes/recon.py`
- `POST /api/recon/run` — creates `ReconRun`, triggers engine, returns `run_id`
- `GET /api/recon/stream/{run_id}` — SSE endpoint using `sse-starlette`
- `GET /api/recon/results/{run_id}` — fetch from Redis cache or DB
- `GET /api/recon/stats/{run_id}` — aggregated statistics

#### [NEW] `backend/app/routes/cashflow.py`
- `GET /api/cashflow/{run_id}` — 7-day projection
- `POST /api/cashflow/whatif` — resolve a break, return updated projection

#### [NEW] `backend/app/routes/audit.py`
- `GET /api/audit/{run_id}` — full audit log
- `GET /api/audit/{run_id}/export` — JSON file download

#### [NEW] `backend/app/routes/health.py`
- `GET /api/health` — checks DB, Redis, Groq connectivity

---

#### [NEW] `backend/app/engine/reconcile.py`
- Orchestrator: loads data from DB, runs Pass 1 → 2 → 3 → 4 sequentially
- Publishes SSE events after each pass
- Aggregates results, computes stats, persists to `recon_results`
- Caches final results in Redis

#### [NEW] `backend/app/engine/pass1_exact.py`
- HashMap-based exact match on `order_id` + `amount`
- Returns `{ matched, unmatched_settlements, unmatched_erp }`

#### [NEW] `backend/app/engine/pass2_rules.py`
- 5 rule functions (T+1/T+2, MDR tolerance, cross-midnight, GST rounding, full refund)
- Each rule returns match + flags list

#### [NEW] `backend/app/engine/pass3_fuzzy.py`
- Amount proximity (±2%), partial refund net matching, duplicate detection, chargeback ID
- Confidence scoring: `confidence = 1.0 - (delta / amount)`

#### [NEW] `backend/app/engine/pass4_llm.py`
- Groq API integration via `groq` SDK
- Structured JSON output for deterministic parsing
- Bilingual (EN + Hinglish) explanation generation
- Batch prompt: sends all remaining breaks in one API call
- Fallback: template diagnostics if Groq unavailable

#### [NEW] `backend/app/engine/cashflow.py`
- 7-day projection per §8.1 with method-specific MDR rates
- `what_if_resolve(run_id, break_id)` per §8.2
- Returns array of `{ date, confirmed_inflow, disputed_held, projected }`

---

#### [NEW] `backend/app/llm/groq_client.py`
- Initializes Groq client with API key
- `analyze_breaks(breaks)` → returns structured diagnostics
- Rate limit handling with exponential backoff
- Graceful fallback if API key missing or errors

#### [NEW] `backend/app/llm/prompts.py`
- System prompt (reconciliation analyst persona)
- User prompt template with `{settlement}`, `{erp}`, `{order}` placeholders
- JSON schema definition for response validation

---

#### [NEW] `backend/app/seed.py`
- Deterministic data seeder (seeded random via `numpy`)
- Generates 100 orders, settlements, ERP ledger entries with all edge cases from §6.5
- Inserts into PostgreSQL
- Idempotent: clears and re-seeds on each run
- CLI entrypoint: `python -m app.seed`

---

#### [NEW] `backend/alembic.ini` + `backend/alembic/`
- Alembic migration config pointing to `DATABASE_URL`
- Initial migration creating all tables

---

### 11.2 Frontend — React + Vite

#### Directory: `frontend/`

#### [NEW] Project Scaffold
- Initialize with `npx -y create-vite@latest ./ -- --template react`
- Install deps: `recharts`, `lucide-react`

#### [NEW] `frontend/src/index.css`
- CSS reset, custom properties (design tokens from §9.1)
- Google Fonts import (Mulish + JetBrains Mono)
- Utility classes for badges, pills, severity indicators
- Keyframe animations (`fadeInUp`, `pulseGlow`, `countUp`, `slideUp`)
- Responsive breakpoints (desktop-first, collapses to single column at 768px)

#### [NEW] `frontend/src/App.jsx`
- Root component with `ReconciliationProvider` context wrapper
- Layout: Header → KPI Row → Split Workbench → AI Drawer
- Manages global state via context

#### [NEW] `frontend/src/App.css`
- App-level layout grid (CSS Grid for main layout)
- Header styles, responsive adjustments

---

#### [NEW] `frontend/src/api/client.js`
- `triggerRecon()` → POST `/api/recon/run`
- `subscribeToRecon(runId, onEvent)` → SSE via `EventSource`
- `fetchResults(runId)` → GET `/api/recon/results/{run_id}`
- `fetchStats(runId)` → GET `/api/recon/stats/{run_id}`
- `fetchCashFlow(runId)` → GET `/api/cashflow/{run_id}`
- `resolveBreak(runId, breakId)` → POST `/api/cashflow/whatif`
- `fetchAuditLog(runId)` → GET `/api/audit/{run_id}`
- `exportAuditLog(runId)` → triggers download from `/api/audit/{run_id}/export`
- Base URL from `VITE_API_URL` env var

---

#### [NEW] `frontend/src/context/ReconciliationContext.jsx`
- React Context + `useReducer`
- State shape:
  ```
  {
    status: 'idle' | 'running' | 'complete' | 'error',
    runId: null,
    progress: {},          // SSE progress data
    results: [],           // all 100 reconciled records
    stats: {},             // match rate, totals, break count
    cashFlow: [],          // 7-day projection data
    whatIfScenario: null,  // currently selected what-if
    language: 'en',        // 'en' | 'hi'
    selectedBreak: null,   // break selected for AI drawer
    drawerOpen: false,
    activeTab: 'all'       // workbench tab
  }
  ```
- Actions: `RUN_RECON`, `PROGRESS_UPDATE`, `RECON_COMPLETE`, `SET_LANGUAGE`, `SELECT_BREAK`, `RESOLVE_BREAK`, `TOGGLE_DRAWER`, `SET_TAB`

---

#### [NEW] `frontend/src/components/Header.jsx` + `Header.css`
- Logo + app title "RazorRecon & Flow"
- Language toggle (EN ↔ HI) — pill-style switch
- "▶ Run Reconciliation" primary CTA button with Razorpay blue
- Processing state: progress bar overlay + "Pass 2 — 75/100 matched..."

#### [NEW] `frontend/src/components/KPIRow.jsx` + `KPIRow.css`
- 4 cards: Total Transactions, Match Rate %, Total Breaks, Net Payout ₹
- Each card has: icon (Lucide), label, animated value, delta indicator
- White cards with colored top border (blue, green, red, blue)
- Stagger-animate on load

#### [NEW] `frontend/src/components/ReconWorkbench.jsx` + `ReconWorkbench.css`
- Tab bar: "All (100)" | "Matched (93)" | "Breaks (7)"
- Scrollable table with columns: Order ID, Amount, Method, Status, Pass, Confidence
- Expandable rows showing match details, flags, deltas
- Break rows with red left border accent
- "View AI Analysis" button on break rows → opens AI Drawer
- Search/filter input

#### [NEW] `frontend/src/components/CashFlowChart.jsx` + `CashFlowChart.css`
- Recharts `AreaChart` with Razorpay blue gradient fill
- Three data series:
  - Confirmed Inflow (solid green area)
  - Disputed/Held (amber area, stacked)
  - What-If Overlay (dashed blue line)
- Custom tooltip showing exact ₹ amounts
- Animated line drawing on mount

#### [NEW] `frontend/src/components/AIExceptionDrawer.jsx` + `AIExceptionDrawer.css`
- Slide-up panel from bottom (initially collapsed, shows count badge)
- Each break card: severity dot, order ID, root cause tag, EN/HI explanation, suggested action
- "✓ Resolve" and "↗ Escalate" buttons
- Resolve triggers What-If update on cash chart

#### [NEW] `frontend/src/components/AuditLogPanel.jsx` + `AuditLogPanel.css`
- Collapsible panel showing full reconciliation audit trail
- Timeline-style layout with pass indicators
- "Export as JSON" button
- Filterable by pass number, status

---

#### [MODIFY] `frontend/index.html`
- SEO: title "RazorRecon & Flow — AI Settlement Reconciliation"
- Meta description
- Google Fonts preconnect + Mulish + JetBrains Mono
- Favicon

---

## 12. Build Order & Dependency Graph

```
Phase 1: Infrastructure (Day 1 Morning)
  ├─ 1.1  Create project structure (backend/ + frontend/)
  ├─ 1.2  docker-compose.yml (PostgreSQL + Redis)
  ├─ 1.3  .env + .env.example
  ├─ 1.4  backend/app/config.py + database.py
  ├─ 1.5  backend/app/models.py (all SQLAlchemy models)
  ├─ 1.6  Alembic init + initial migration
  └─ 1.7  backend/app/seed.py (generate + insert 100 records)

Phase 2: Backend Engine (Day 1 Afternoon → Day 2 Morning)
  ├─ 2.1  backend/app/engine/pass1_exact.py
  ├─ 2.2  backend/app/engine/pass2_rules.py
  ├─ 2.3  backend/app/engine/pass3_fuzzy.py
  ├─ 2.4  backend/app/llm/prompts.py + groq_client.py
  ├─ 2.5  backend/app/engine/pass4_llm.py (depends on 2.4)
  ├─ 2.6  backend/app/engine/reconcile.py (orchestrator, depends on 2.1–2.5)
  ├─ 2.7  backend/app/engine/cashflow.py
  └─ 2.8  backend/app/cache.py (Redis integration)

Phase 3: API Layer (Day 2 Afternoon)
  ├─ 3.1  backend/app/schemas.py (Pydantic models)
  ├─ 3.2  backend/app/routes/recon.py (REST + SSE)
  ├─ 3.3  backend/app/routes/cashflow.py
  ├─ 3.4  backend/app/routes/audit.py
  ├─ 3.5  backend/app/routes/health.py
  └─ 3.6  backend/app/main.py (assemble routes, CORS, lifespan)

Phase 4: Frontend Foundation (Day 2 Evening → Day 3 Morning)
  ├─ 4.1  Vite scaffold + install deps
  ├─ 4.2  index.html (SEO, fonts, favicon)
  ├─ 4.3  index.css (Razorpay design system, tokens, animations)
  ├─ 4.4  api/client.js (REST + SSE client)
  └─ 4.5  context/ReconciliationContext.jsx

Phase 5: Frontend Components (Day 3)
  ├─ 5.1  Header.jsx + Header.css
  ├─ 5.2  KPIRow.jsx + KPIRow.css
  ├─ 5.3  ReconWorkbench.jsx + ReconWorkbench.css
  ├─ 5.4  CashFlowChart.jsx + CashFlowChart.css
  ├─ 5.5  AIExceptionDrawer.jsx + AIExceptionDrawer.css
  └─ 5.6  AuditLogPanel.jsx + AuditLogPanel.css

Phase 6: Assembly & Integration (Day 3 Evening)
  ├─ 6.1  App.jsx + App.css (compose all components)
  ├─ 6.2  Wire SSE progress → KPI live updates
  ├─ 6.3  Wire What-If resolve → cash chart update
  └─ 6.4  Wire audit export → JSON download

Phase 7: Polish & Verify (Day 4)
  ├─ 7.1  Run full reconciliation, verify >90% match rate
  ├─ 7.2  Test LLM diagnostics (EN + Hinglish)
  ├─ 7.3  Verify What-If cash chart updates
  ├─ 7.4  Responsive check (desktop + tablet)
  ├─ 7.5  Edge case: no API key → graceful fallback
  ├─ 7.6  Edge case: Redis down → fall back to DB reads
  └─ 7.7  Final build + smoke test
```

---

## 13. Running the Project

### Quick Start

```bash
# 1. Start infrastructure
docker compose up -d    # Starts PostgreSQL + Redis

# 2. Backend
cd backend
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt
alembic upgrade head       # Run migrations
python -m app.seed         # Seed 100 records
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
npm run dev                # Vite dev server on :5173
```

### Environment Variables

```bash
# backend/.env
GROQ_API_KEY=gsk_...           # Get from console.groq.com
DATABASE_URL=postgresql://razorrecon:razorrecon@localhost:5432/razorrecon
REDIS_URL=redis://localhost:6379/0

# frontend/.env
VITE_API_URL=http://localhost:8000
```

---

## 14. Verification Plan

### Automated Verification

```bash
# Backend starts without errors
cd backend && uvicorn app.main:app --port 8000

# Health check passes
curl http://localhost:8000/api/health

# Seed data exists
curl http://localhost:8000/api/recon/run -X POST  # Should return run_id

# Frontend builds
cd frontend && npm run build
```

### Manual Verification Checklist

| # | Test | Expected Result |
|---|---|---|
| 1 | Click "Run Reconciliation" | SSE stream shows live progress: Pass 1→2→3→4 |
| 2 | Watch KPI cards | Animated count-up during SSE events |
| 3 | Check Match Rate KPI | Shows ≥90% (target: 93%) |
| 4 | Click "Breaks" tab | Shows 7 break records with red indicators |
| 5 | Expand a break row | Shows pass info, flags, delta values |
| 6 | Click "View AI Analysis" | AI Drawer slides up with Llama 3.3 explanation |
| 7 | Toggle language to HI | Explanations switch to Hinglish |
| 8 | Click "Resolve" on a break | Cash chart updates with What-If overlay |
| 9 | Verify cash chart | 7-day area chart with confirmed + disputed areas |
| 10 | Expand Audit Log | Full timeline of all 100 reconciliation actions |
| 11 | Click "Export as JSON" | Downloads audit log JSON file from backend |
| 12 | Resize to 768px | Responsive single-column layout |
| 13 | Kill Groq API key | Graceful fallback — template diagnostics, no crash |
| 14 | Stop Redis | Falls back to direct DB queries, no crash |

### Judging Criteria Alignment

| Criteria | How We Address It |
|---|---|
| **Problem Taste** | Real pain point: 20-40 hrs/week manual reconciliation → automated in seconds |
| **Build Quality** | Full-stack: FastAPI + PostgreSQL + Redis + React. Mirrors Razorpay's actual architecture |
| **AI Judgment** | LLM only in Pass 4 (appropriate use — not forced); deterministic passes first. Llama 3.3 70B for speed |
| **Failure Recovery** | Graceful LLM fallback, Redis fallback to DB, audit log for every action, handles all edge cases |
| **Scale (50-100+)** | 100 records with 10 distinct edge case types, stored in PostgreSQL |
| **Match Rate >90%** | Engineered dataset guarantees ~93% with 4-pass architecture |
| **Exception Diagnostics** | Bilingual LLM explanations with root cause + suggested action via Groq |
| **Cash-Flow Prescriber** | 7-day projection with real-time What-If resolution |
| **No Cherry-Picking** | MDR variance, cross-midnight, chargebacks, duplicates all handled |
| **Razorpay Stack Alignment** | Python/PostgreSQL/Redis/Docker — mirrors their actual production infra |
| **Live Demo Impact** | SSE streaming shows reconciliation happening in real-time |

### Pitch Talking Points

> "We've built a mini-version of Razorpay's own internal architecture — Python microservices backed by PostgreSQL and Redis, containerized with Docker, with an AI agent powered by Llama 3.3 70B for ultra-fast inference. The 4-pass reconciliation engine handles all the messy edge cases deterministically first, then calls in the LLM only for the truly ambiguous breaks — exactly the kind of hybrid AI approach that scales in production."
