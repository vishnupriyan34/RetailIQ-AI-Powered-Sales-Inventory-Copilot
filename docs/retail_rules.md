# Retail Business Rules, Policies, and Inventory Definitions

## 1. Inventory Metric Definitions

### 1.1 Current Stock (Stock on Hand)
The physical quantity of sellable units currently available in a specific store location. Excludes damaged, expired, or in-transit goods unless explicitly verified and checked into inventory.

### 1.2 Safety Stock
The minimum buffer of inventory maintained at a retail store to protect against stock-outs caused by unexpected demand surges or supplier shipment delays.
- Formula: Safety Stock = Lead Time Days * Buffer Factor

### 1.3 Reorder Level (Reorder Point)
The threshold inventory level that automatically triggers a replenishment purchase order. When current stock reaches or drops below this level, replenishment is required.
- Formula: Reorder Level = (Average Daily Sales * Lead Time Days) + Safety Stock

### 1.4 Average Daily Sales (ADS)
The rate at which a product sells per calendar day over a defined rolling evaluation window:
- **ADS (7-Day)**: Reflects immediate, short-term sales velocity and recent demand shifts.
- **ADS (30-Day)**: Serves as the established historical baseline demand rate.

### 1.5 Days of Stock Remaining (Stock Coverage)
The estimated number of days until inventory will deplete to zero if current sales velocity continues at the same rate.
- Formula: Days of Stock = Current Stock / Average Daily Sales
- If Average Daily Sales is 0 and Current Stock > 0, coverage is considered infinite (stagnant/surplus).

### 1.6 Stock Turnover Ratio
Measures how many times inventory is sold and replaced over an annualized or monthly period.
- Formula: Turnover = Total Units Sold / Average Stock Level

---

## 2. Rule 1 — Likely Stock-Out Policy

### 2.1 Criteria & Thresholds
A product-store combination is flagged as **LIKELY STOCK-OUT** if:
1. **Critical Condition**: Days of Stock <= Lead Time Days, meaning inventory will deplete before a replenishment shipment can arrive.
2. **Warning Condition**: Days of Stock < 5.0 days OR Current Stock <= Safety Stock.

### 2.2 Business Impact
Stock-outs directly cause lost gross margin, reduce customer satisfaction, harm store loyalty, and risk basket abandonment in multi-item shopping trips.

### 2.3 Required Reorder Quantity Formula
When a stock-out alert triggers, the recommended order quantity is calculated as:
Reorder Quantity = (Target Coverage Days * ADS) + Safety Stock - Current Stock
(Where Target Coverage Days defaults to 21 days for general merchandise and 14 days for perishable grocery).

---

## 3. Rule 2 — Overstock Policy

### 3.1 Criteria & Thresholds
A product-store combination is flagged as **OVERSTOCK** if:
1. Days of Stock > 60.0 days (excluding planned seasonal ramp-ups).
2. OR Current Stock > 3.0 * Reorder Level.

### 3.2 Business Impact
Excess inventory ties up working capital, increases carrying and warehouse costs, increases shrinkage/theft risk, takes up prime shelf display area, and causes markdown losses.

### 3.3 Recommended Action
- Immediately pause or cancel pending purchase orders with suppliers.
- Implement promotional pricing (e.g. 15% to 25% discount) to accelerate velocity.
- Rebalance inventory by initiating store-to-store transfers to locations with lower stock coverage.

---

## 4. Rule 3 — Slow-Moving Product Policy

### 4.1 Criteria & Thresholds
A product is flagged as **SLOW MOVING** if:
1. Current Stock > 0 (holding positive inventory).
2. Trailing 30-day ADS < 0.20 units/day (equivalent to selling fewer than 6 units over an entire month).

### 4.2 Remediation
Review product placement, inspect product presentation, evaluate competitive pricing, bundle with fast-moving complementary items, or schedule phased clearance liquidation.

---

## 5. Rule 4 — Sales Spike Policy

### 5.1 Criteria & Thresholds
A product is flagged for an abnormal **SALES SPIKE** if:
1. ADS (7-Day) / ADS (30-Day) >= 2.0 (a 100% or higher surge above historical baseline).
2. Units Sold in the last 7 days >= 5 units (prevents false positives from small numbers, e.g. selling 2 units after 1 unit).

### 5.2 Action Plan
Investigate driver (local marketing, seasonal surge, viral trend, competitor outage). Immediately recalculate days of stock coverage and advance replenishment orders to avoid an unexpected stock-out.

---

## 6. Rule 5 — Sales Drop Policy

### 6.1 Criteria & Thresholds
A product is flagged for an abnormal **SALES DROP** if:
1. ADS (7-Day) / ADS (30-Day) <= 0.40 (a 60% or greater decline compared to historical baseline).
2. Historical Baseline ADS (30-Day) >= 1.0 unit/day (ensures the drop is statistically meaningful on a high-volume product).

### 6.2 Action Plan
Conduct physical store audit: check if item is missing from shelf, improperly priced, hidden in backroom, damaged, or impacted by new competitor promotions.

---

## 7. Business Assumptions & System Boundaries

### 7.1 Authoritative Scope of System Data
- All inventory positions and point-of-sale sales data are authoritative, recorded at store level across the trailing 90 days.
- Calculations are deterministic and calculated in Python without speculative approximation.

### 7.2 Strict Hallucination Guardrails
- The copilot must NEVER invent revenue numbers, inventory levels, or future predictions.
- If a user asks a question outside the scope of recorded retail data (such as exact financial forecasts 6 months into the future, external competitor pricing, weather data, or non-catalog items), the copilot MUST clearly answer:
  "I don't have enough data to answer that."
- The copilot must explain why the available data cannot answer the question rather than guessing.
