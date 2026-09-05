"""
Authoritative Deterministic Rule & Alert Engine for RetailIQ
Evaluates the 5 mandatory retail rules and generates comprehensive evidence packages.
Never relies on LLMs to decide whether an alert is triggered.
"""

from typing import List, Dict, Any, Optional
import math
import numpy as np
from src.analytics import RetailAnalytics

class AlertEngine:
    def __init__(self, analytics: RetailAnalytics):
        self.analytics = analytics
        
        # Documented business policy thresholds
        self.STOCKOUT_DAYS_THRESHOLD = 5.0 # Days of stock
        self.OVERSTOCK_DAYS_THRESHOLD = 60.0 # Days of stock
        self.OVERSTOCK_REORDER_MULTIPLIER = 3.0 # Times reorder level
        self.SLOW_MOVING_ADS_THRESHOLD = 0.20 # Units/day over 30 days
        self.SPIKE_RATIO_THRESHOLD = 2.0 # 7-day ADS / 30-day ADS >= 2.0
        self.SPIKE_MIN_UNITS = 5 # Minimum units in 7 days to trigger spike
        self.DROP_RATIO_THRESHOLD = 0.40 # 7-day ADS / 30-day ADS <= 0.40
        self.DROP_MIN_BASELINE_ADS = 1.0 # Baseline ADS must be >= 1.0 to count drop

    def evaluate_all(self, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Runs all 5 rules across all product-store records.
        Returns a list of structured alert objects.
        """
        metrics = self.analytics.get_product_metrics_table(store_id=store_id)
        alerts = []

        for m in metrics:
            # Evaluate Rule 1: Stock-Out
            alert1 = self._check_stockout(m)
            if alert1:
                alerts.append(alert1)

            # Evaluate Rule 2: Overstock
            alert2 = self._check_overstock(m)
            if alert2:
                alerts.append(alert2)

            # Evaluate Rule 3: Slow Moving
            alert3 = self._check_slow_moving(m)
            if alert3:
                alerts.append(alert3)

            # Evaluate Rule 4: Sales Spike
            alert4 = self._check_sales_spike(m)
            if alert4:
                alerts.append(alert4)

            # Evaluate Rule 5: Sales Drop
            alert5 = self._check_sales_drop(m)
            if alert5:
                alerts.append(alert5)

        # Sort by severity: CRITICAL first, then WARNING, then ATTENTION / OPPORTUNITY
        severity_order = {"CRITICAL": 0, "WARNING": 1, "OPPORTUNITY": 2, "ATTENTION": 3, "INFO": 4}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 99))
        return alerts

    def _check_stockout(self, m: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        stock = m["current_stock"]
        ads = m["effective_ads"]
        days = m["days_of_stock"]
        lead = m["lead_time_days"]
        safety = m["safety_stock"]
        reorder = m["reorder_level"]

        # Only trigger if product has demand or is below safety stock
        if ads <= 0 and stock > 0:
            return None

        is_critical_lead_time = (days <= lead)
        is_threshold_breached = (days < self.STOCKOUT_DAYS_THRESHOLD)
        is_below_safety = (stock <= safety)

        if is_critical_lead_time or is_threshold_breached or is_below_safety:
            severity = "CRITICAL" if is_critical_lead_time else "WARNING"
            
            # Reorder calculation: (target 21 days * ads) + safety - current_stock
            target_days = 21
            rec_reorder_qty = max(0, int(np.ceil((target_days * ads) + safety - stock)))

            reason_parts = []
            if is_critical_lead_time:
                reason_parts.append(f"Estimated stock coverage ({days} days) is less than supplier lead time ({lead} days). An immediate stock-out is guaranteed unless replenished.")
            elif is_threshold_breached:
                reason_parts.append(f"Projected stock coverage ({days} days) is below the configured threshold of {self.STOCKOUT_DAYS_THRESHOLD} days.")
            if is_below_safety:
                reason_parts.append(f"Current inventory ({stock} units) is at or below safety stock ({safety} units).")

            reason = " ".join(reason_parts)
            evidence = (
                f"Current stock: {stock} units; 7-day sales: {m['units_sold_7d']} units (ADS: {m['ads_7d']}/day); "
                f"30-day sales: {m['units_sold_30d']} units (ADS: {m['ads_30d']}/day); "
                f"Supplier lead time: {lead} days; Reorder level: {reorder} units; Safety stock: {safety} units."
            )
            recommendation = (
                f"Initiate purchase order immediately for at least {rec_reorder_qty} units from {m.get('supplier', 'supplier')} "
                f"to restore buffer to 21 days of expected demand."
            )
            assumptions = f"Stock coverage projected at current rolling velocity of {ads} units/day. Lead time is assumed fixed at {lead} calendar days."

            return {
                "alert_id": f"ALT-SO-{m['product_id']}-{m['store_id']}",
                "rule_id": "RULE_1_STOCKOUT",
                "rule_triggered": "Rule 1 - Likely Stock-Out",
                "rule_number": 1,
                "severity": severity,
                "product_id": m["product_id"],
                "product_name": m["product_name"],
                "category": m["category"],
                "store_id": m["store_id"],
                "store_name": m["store_name"],
                "actual_numbers": {
                    "current_stock": stock,
                    "average_daily_sales_7d": m["ads_7d"],
                    "average_daily_sales_30d": m["ads_30d"],
                    "days_of_stock": days,
                    "reorder_level": reorder,
                    "safety_stock": safety,
                    "lead_time_days": lead,
                    "recommended_reorder_units": rec_reorder_qty
                },
                "reason": reason,
                "evidence": evidence,
                "recommendation": recommendation,
                "assumptions": assumptions
            }
        return None

    def _check_overstock(self, m: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        stock = m["current_stock"]
        ads = m["effective_ads"]
        days = m["days_of_stock"]
        reorder = m["reorder_level"]
        cost = m["unit_cost"]

        if stock <= 0 or ads <= 0:
            return None

        is_high_days = (days > self.OVERSTOCK_DAYS_THRESHOLD)
        is_high_reorder = (stock > (self.OVERSTOCK_REORDER_MULTIPLIER * reorder))

        if is_high_days or is_high_reorder:
            excess_units = max(0, int(stock - (reorder * 1.5)))
            tied_capital = round(excess_units * cost, 2)
            
            reason = (
                f"Current stock of {stock} units represents {days} days of forward supply, "
                f"greatly exceeding the operational overstock threshold of {self.OVERSTOCK_DAYS_THRESHOLD} days "
                f"(and {round(stock / max(1, reorder), 1)}x the reorder level)."
            )
            evidence = (
                f"Current stock: {stock} units; Average daily sales: {ads} units/day; "
                f"Coverage: {days} days; Reorder level: {reorder} units; "
                f"Tied up working capital in excess stock: ${tied_capital:,.2f}."
            )
            recommendation = (
                f"Freeze future purchase orders for {m['product_name']}. Consider initiating a 15% promotional discount "
                f"or cross-store transfer to accelerate depletion and liberate ${tied_capital:,.2f} in working capital."
            )
            assumptions = "Expected depletion rate assumes constant daily demand without promotional markdown intervention."

            return {
                "alert_id": f"ALT-OS-{m['product_id']}-{m['store_id']}",
                "rule_id": "RULE_2_OVERSTOCK",
                "rule_triggered": "Rule 2 - Overstock",
                "rule_number": 2,
                "severity": "WARNING",
                "product_id": m["product_id"],
                "product_name": m["product_name"],
                "category": m["category"],
                "store_id": m["store_id"],
                "store_name": m["store_name"],
                "actual_numbers": {
                    "current_stock": stock,
                    "average_daily_sales": ads,
                    "days_of_stock": days,
                    "reorder_level": reorder,
                    "excess_units": excess_units,
                    "tied_up_capital": tied_capital
                },
                "reason": reason,
                "evidence": evidence,
                "recommendation": recommendation,
                "assumptions": assumptions
            }
        return None

    def _check_slow_moving(self, m: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        stock = m["current_stock"]
        ads_30d = m["ads_30d"]
        units_30d = m["units_sold_30d"]
        cost = m["unit_cost"]

        # If holding stock, has sales history, and sells less than 0.20 units/day over 30 days
        if stock > 0 and m.get("total_units_sold", 0) > 0 and ads_30d < self.SLOW_MOVING_ADS_THRESHOLD:
            inventory_val = round(stock * cost, 2)
            reason = (
                f"Velocity is extremely sluggish with only {units_30d} units sold in the last 30 days "
                f"(ADS of {ads_30d} units/day, below threshold of {self.SLOW_MOVING_ADS_THRESHOLD})."
            )
            evidence = (
                f"Stock on hand: {stock} units; 30-day sales: {units_30d} units; "
                f"30-day ADS: {ads_30d}; Total inventory value locked: ${inventory_val:,.2f}."
            )
            recommendation = (
                f"Review product merchandising and placement. Implement a clearance bundle or end-cap promotional placement "
                f"to liquidate stagnant inventory."
            )
            assumptions = "Assumes product was continuously merchandised on floor throughout the 30-day window."

            return {
                "alert_id": f"ALT-SM-{m['product_id']}-{m['store_id']}",
                "rule_id": "RULE_3_SLOW_MOVING",
                "rule_triggered": "Rule 3 - Slow Moving",
                "rule_number": 3,
                "severity": "ATTENTION",
                "product_id": m["product_id"],
                "product_name": m["product_name"],
                "category": m["category"],
                "store_id": m["store_id"],
                "store_name": m["store_name"],
                "actual_numbers": {
                    "current_stock": stock,
                    "units_sold_30d": units_30d,
                    "ads_30d": ads_30d,
                    "inventory_valuation": inventory_val
                },
                "reason": reason,
                "evidence": evidence,
                "recommendation": recommendation,
                "assumptions": assumptions
            }
        return None

    def _check_sales_spike(self, m: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ads_7d = m["ads_7d"]
        ads_30d = m["ads_30d"]
        units_7d = m["units_sold_7d"]
        ratio = m["velocity_ratio"]

        # Trigger if 7-day velocity >= 2.0x 30-day baseline AND minimum 5 units sold
        if ratio >= self.SPIKE_RATIO_THRESHOLD and units_7d >= self.SPIKE_MIN_UNITS:
            spike_pct = round((ratio - 1.0) * 100, 1)
            reason = (
                f"Recent 7-day sales velocity ({ads_7d} units/day) surged by {spike_pct}% "
                f"compared to the 30-day baseline ({ads_30d} units/day)."
            )
            evidence = (
                f"7-day units sold: {units_7d} (ADS: {ads_7d}/day); "
                f"30-day baseline ADS: {ads_30d}/day; Surge ratio: {ratio}x baseline; "
                f"Remaining stock: {m['current_stock']} units ({m['days_of_stock']} days cover)."
            )
            recommendation = (
                f"Investigate cause of surge (marketing campaign, viral demand). Recalculate reorder triggers "
                f"immediately to prevent stock depletion under sustained high velocity."
            )
            assumptions = "Assumes demand surge represents genuine customer sell-through rather than a one-time institutional return or anomaly."

            return {
                "alert_id": f"ALT-SPK-{m['product_id']}-{m['store_id']}",
                "rule_id": "RULE_4_SALES_SPIKE",
                "rule_triggered": "Rule 4 - Sales Spike",
                "rule_number": 4,
                "severity": "OPPORTUNITY",
                "product_id": m["product_id"],
                "product_name": m["product_name"],
                "category": m["category"],
                "store_id": m["store_id"],
                "store_name": m["store_name"],
                "actual_numbers": {
                    "ads_7d": ads_7d,
                    "ads_30d": ads_30d,
                    "units_sold_7d": units_7d,
                    "velocity_ratio": ratio,
                    "current_stock": m["current_stock"],
                    "days_of_stock": m["days_of_stock"]
                },
                "reason": reason,
                "evidence": evidence,
                "recommendation": recommendation,
                "assumptions": assumptions
            }
        return None

    def _check_sales_drop(self, m: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ads_7d = m["ads_7d"]
        ads_30d = m["ads_30d"]
        units_7d = m["units_sold_7d"]
        ratio = m["velocity_ratio"]

        # Trigger if 7-day velocity <= 0.40x baseline AND baseline was >= 1.0 unit/day
        if ads_30d >= self.DROP_MIN_BASELINE_ADS and ratio <= self.DROP_RATIO_THRESHOLD:
            drop_pct = round((1.0 - ratio) * 100, 1)
            reason = (
                f"Sales velocity contracted by {drop_pct}% over the last 7 days "
                f"({ads_7d} units/day vs baseline {ads_30d} units/day)."
            )
            evidence = (
                f"7-day units sold: {units_7d} (ADS: {ads_7d}/day); "
                f"30-day baseline ADS: {ads_30d}/day; Drop ratio: {ratio}x baseline; "
                f"Stock on hand: {m['current_stock']} units."
            )
            recommendation = (
                f"Perform physical store audit immediately: verify shelf tag pricing, check on-shelf availability, "
                f"and ensure stock is not hidden in backroom or damaged."
            )
            assumptions = "Assumes product was in-stock and actively merchandised on store shelf."

            return {
                "alert_id": f"ALT-DRP-{m['product_id']}-{m['store_id']}",
                "rule_id": "RULE_5_SALES_DROP",
                "rule_triggered": "Rule 5 - Sales Drop",
                "rule_number": 5,
                "severity": "WARNING",
                "product_id": m["product_id"],
                "product_name": m["product_name"],
                "category": m["category"],
                "store_id": m["store_id"],
                "store_name": m["store_name"],
                "actual_numbers": {
                    "ads_7d": ads_7d,
                    "ads_30d": ads_30d,
                    "units_sold_7d": units_7d,
                    "velocity_ratio": ratio,
                    "current_stock": m["current_stock"]
                },
                "reason": reason,
                "evidence": evidence,
                "recommendation": recommendation,
                "assumptions": assumptions
            }
        return None
