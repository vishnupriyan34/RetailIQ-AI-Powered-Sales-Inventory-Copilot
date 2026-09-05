TRACK_ID=PS03
# RetailIQ — Retail Sales and Inventory Copilot

RetailIQ is an enterprise-grade retail decision-support copilot and executive analytics platform built for store managers operating multi-location retail networks. It combines deterministic Python calculations with Google Gemini AI for grounded natural language reasoning, explanation, and local policy retrieval (RAG).

The system enforces a **Zero Hallucination Guarantee**: all financial metrics, Average Daily Sales (ADS), stock coverage days, and alert conditions are computed authoritatively by Python using Pandas and NumPy. Gemini is utilized solely to explain, contextualize, and reason over verified evidence packages.

---

## 1. Problem Being Solved

Store managers running multi-store retail operations face fragmented data across point-of-sale systems and stockrooms. Critical inventory risks often go unnoticed until it is too late:
- **Stock-Outs**: Fast-moving items run out of stock before replacement purchase orders can arrive, resulting in lost revenue and customer churn.
- **Overstock**: Excess merchandise accumulates, tying up working capital and incurring holding/markdown costs.
- **Velocity Anomalies**: Sudden sales spikes (which risk immediate depletion) and severe sales drops (which indicate on-shelf merchandising or pricing failures) remain hidden in raw transaction logs.
- **Hallucination in AI**: Standard LLM chatbots invent numbers and extrapolate speculative sales forecasts that mislead managers.

RetailIQ solves this by pairing an authoritative deterministic analytics and rule engine with a grounded Generative AI Copilot that always cites verified system numbers and operational policy guidelines.

---

## 2. Key Features

- **Executive Analytics Dashboard**:
  - Top KPI cards: Total Revenue, Units Sold, Current Inventory, and Products Needing Attention.
  - Interactive Chart.js visualizations: 30-day Daily Sales Revenue trend and Category Revenue Share donut.
  - Multi-Store Filter: Seamlessly view consolidated enterprise performance or drill down to individual stores (*Downtown Flagship*, *Westside Mall*, *Suburban Center*, *Metro Express*).
- **Deterministic Alert & Rule Engine**:
  - **Rule 1 — Likely Stock-Out**: Identifies products whose forward days of stock is below the 5.0-day threshold or less than supplier lead time.
  - **Rule 2 — Overstock**: Identifies inventory holding over 60 days of forward supply or more than 3x the reorder point.
  - **Rule 3 — Slow Moving**: Flags products holding inventory but selling fewer than 0.20 units/day over a 30-day baseline.
  - **Rule 4 — Sales Spike**: Flags sudden demand surges where 7-day velocity is $\ge 2.0\times$ the 30-day baseline.
  - **Rule 5 — Sales Drop**: Flags demand drops where 7-day velocity is $\le 0.40\times$ the baseline.
  - Every alert contains product, store, exact numerical values, rule triggered, reason, evidence, assumptions, and actionable recommendation.
- **Grounded AI Copilot**:
  - Natural language interface directly on the dashboard with quick suggested question chips.
  - Retrieves authoritative structured metrics and relevant policies before responding.
  - Answers in a standardized structure: **SUMMARY**, **VERIFIED EVIDENCE**, **RULE / POLICY CITED**, **ANALYSIS**, **RECOMMENDATION**, and **ASSUMPTIONS & DATA SOURCES**.
  - Includes an interactive **Inspect Evidence JSON** drawer for auditing underlying calculations.
- **Strict Hallucination Guardrails**:
  - If a user asks questions beyond the 90-day historical data (e.g. *"What will our sales be exactly 6 months from now?"* or uncataloged items like *"iPhone 16"*), the copilot transparently states: *"I don't have enough data to answer that."*
- **High-Resilience Dual Execution**:
  - Powered by Google Gemini (`gemini-1.5-flash` or `gemini-2.5-flash`).
  - If `GEMINI_API_KEY` is not provided or the network is offline, the copilot automatically falls back to an authoritative deterministic synthesis engine, guaranteeing that the application never crashes during judging.

---

## 3. Architecture & Data Flow

```
[Store Manager / Judge]
        │
        ▼
[Web Dashboard & AI Chat UI]  (localhost:8000)
        │
        ▼
[Flask REST API Server (app.py)]
        │
        ├──► [Authoritative Analytics Engine (src/analytics.py)]
        │         ├── products.csv (Catalog across 5 categories)
        │         ├── stores.csv (4 store locations)
        │         ├── inventory.csv (Stock balances, lead times, safety stocks)
        │         └── sales.csv (90 days of daily POS transactions)
        │
        ├──► [Alert & Rule Engine (src/rules.py)]
        │         └── Evaluates Rules 1 to 5 deterministically
        │
        ├──► [Local Policy RAG (src/retrieval.py)]
        │         └── docs/retail_rules.md (Embeddings / TF-IDF similarity)
        │
        └──► [Grounded Copilot (src/gemini.py)]
                  ├── Query Understanding & Entity Matching
                  ├── Guardrail Boundary Verification
                  ├── Evidence Package Assembly
                  └── Grounded Response Generation (Gemini or Fallback)
```

---

## 4. Technology Stack

- **Backend**: Python 3.11+ / Python 3.13
- **Web Framework**: Flask
- **Data Processing**: Pandas, NumPy
- **Generative AI & LLM**: Google Gemini API (`gemini-1.5-flash` / `gemini-2.5-flash`)
- **Embeddings & Policy Retrieval**: Gemini Embeddings (`models/gemini-embedding-001`) with instant local TF-IDF vector fallback (100% local, zero external vector DBs)
- **Frontend**: Responsive HTML5, Modern Dark-Slate CSS3, Vanilla ES6 JavaScript, Chart.js

---

## 5. Synthetic Retail Dataset

The system includes realistic synthetic retail data in `data/`:
- `data/products.csv`: 21 products across Electronics, Grocery, Home, Fashion, and Personal Care (includes *Laptop Pro*, *Wireless Mouse*, *Artisan Sourdough*, *Ceramic Cookware Set*, *Electric Toothbrush Pro*, *Vintage Leather Jacket*, etc.).
- `data/stores.csv`: 4 retail branches:
  - `S001`: Downtown Flagship (Financial District)
  - `S002`: Westside Mall (Retail Plaza)
  - `S003`: Suburban Center (North Suburbs)
  - `S004`: Metro Express (Midtown Transit)
- `data/inventory.csv`: 84 store-product inventory records specifying `current_stock`, `reorder_level`, `safety_stock`, and `unit_cost`.
  - *Wireless Mouse at Downtown Flagship*: Configured with `current_stock=12`, `reorder_level=25`, `safety_stock=15`, 7-day ADS = 5.0 units/day $\rightarrow$ **Estimated Stock Coverage: 2.4 days** (Triggering Rule 1 Critical Stock-Out).
- `data/sales.csv`: 7,560 daily transaction records spanning 90 days (from June to September 2026) totaling over $1.66M in revenue.

---

## 6. How Gemini & Deterministic Logic Are Separated

| Capability | Module Responsible | Methodology |
| :--- | :--- | :--- |
| **Sales Calculations** | `src/analytics.py` | Deterministic Pandas aggregations |
| **Average Daily Sales (ADS)** | `src/analytics.py` | Rolling 7-day and 30-day velocity formulas |
| **Stock Coverage Days** | `src/analytics.py` | $\text{Current Stock} / \text{ADS}$ |
| **Alert Detection (Rules 1–5)** | `src/rules.py` | Deterministic threshold conditionals |
| **Recommended Reorder Units** | `src/rules.py` | $(\text{Target Days} \times \text{ADS}) + \text{Safety Stock} - \text{Current Stock}$ |
| **Evidence Assembly** | `src/gemini.py` | Python JSON dictionary packaging |
| **Query Understanding** | `src/gemini.py` | Intent parsing & entity resolution |
| **Policy Retrieval** | `src/retrieval.py` | Local RAG on `docs/retail_rules.md` |
| **Natural Language Explanation** | `src/gemini.py` | Gemini 1.5 Flash grounded on verified evidence |
| **Boundary Guardrail** | `src/gemini.py` | Explicit *"I don't have enough data to answer that."* |

---

## 7. How to Run the Application

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: (Optional) Set the Gemini API Key
To enable live Gemini 1.5 Flash generation, set the environment variable:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-gemini-api-key-here"
```

**Windows (CMD):**
```cmd
set GEMINI_API_KEY=your-gemini-api-key-here
```

**Linux / macOS:**
```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

*(Note: If `GEMINI_API_KEY` is not set, RetailIQ will automatically run in Authoritative Grounded Synthesizer mode. The dashboard, analytics, alerts, and copilot remain 100% functional!)*

### Step 3: Start the Application
```bash
python app.py
```

Open your browser at:
**[http://localhost:8000](http://localhost:8000)**

- Single terminal process.
- No separate frontend build command required.
- Starts in under 2 seconds.

---

## 8. Demo Walkthrough (2–3 Minutes)

Use these 4 core demo questions (available as one-click chips in the Copilot UI):

### Demo 1: "What products need attention today?"
- **Manager Intent**: Immediate operational triage across all 4 stores.
- **Copilot Output**: Shows prioritized critical stock-outs (Wireless Mouse at Downtown Flagship, Laptop Pro allocations), sales drops (Artisan Sourdough), and sales surges (Electric Toothbrush).
- **Notice**: Cites exact numbers and rules from `docs/retail_rules.md`.

### Demo 2: "Why is Wireless Mouse flagged?"
- **Manager Intent**: Root-cause inquiry on a specific SKU.
- **Copilot Output**:
  - Current stock: **12 units**
  - 7-Day Average Daily Sales: **5.0 units/day**
  - Estimated Stock Coverage: **2.4 days**
  - Reorder Level: **25 units** (Safety stock: 15 units)
  - Lead Time: **4 days**
  - **Reason**: 2.4 days of coverage is less than the 4-day lead time $\rightarrow$ stock-out is guaranteed before arrival. Recommends ordering 108 units.

### Demo 3: "How did Laptop Pro perform this month?"
- **Manager Intent**: Product monthly sales and inventory health review.
- **Copilot Output**: Reports exact monthly revenue ($50,400.00, 42 units in September 2026), trailing 30-day revenue ($249,600.00), ADS, selling price ($1,200.00), and total units in stock across stores.

### Demo 4: "What should I reorder?"
- **Manager Intent**: Purchasing and replenishment recommendations.
- **Copilot Output**: Tabulates prioritized items with calculated order quantities based on supplier lead times and safety stock targets.

### Demo 5 (Edge / Guardrail Case): "What will our sales be exactly 6 months from now?"
- **Manager Intent**: Test hallucination prevention.
- **Copilot Output**: Clearly responds: *"I don't have enough data to answer that."* Explains that available historical data covers 90 days and does not support speculative long-range forecasts without macro indicators.

---

## 9. Running Automated Tests

Run the comprehensive test suite validating all normal and difficult cases:
```bash
python tests/test_copilot.py
```
Expected output:
```text
Ran 17 tests in 1.44s
OK
```

---

## 10. Repository Structure

```
RetailIQ/
├── app.py                     # Main Flask server entry point (port 8000)
├── generate_data.py           # Reproducible synthetic retail data generator
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation (first line TRACK_ID=PS03)
│
├── data/
│   ├── products.csv           # 21 products across 5 retail categories
│   ├── stores.csv             # 4 store branches
│   ├── sales.csv              # 7,560 daily POS transaction records (90 days)
│   ├── inventory.csv          # 84 inventory levels, reorder points, lead times
│   └── policy_embeddings.json # Local embeddings cache
│
├── src/
│   ├── analytics.py           # Authoritative deterministic metrics (Pandas)
│   ├── rules.py               # Deterministic rule engine (Rules 1 to 5)
│   ├── retrieval.py           # Local policy RAG (retail_rules.md)
│   ├── gemini.py              # Grounded AI Copilot & fallback synthesizer
│   └── prompts.py             # System prompts and grounding directives
│
├── docs/
│   └── retail_rules.md        # Retail business rules, policies & thresholds
│
├── templates/
│   └── index.html             # Executive analytics dashboard & chat UI
│
├── static/
│   ├── css/
│   │   └── styles.css         # Modern dark-slate UI styles
│   └── js/
│       └── app.js             # Client dashboard logic, Chart.js, Copilot
│
└── tests/
    └── test_copilot.py        # 17 automated tests (normal & edge cases)
```
