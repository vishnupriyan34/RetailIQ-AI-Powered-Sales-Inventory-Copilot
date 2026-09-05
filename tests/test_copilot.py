"""
Automated Test Suite for RetailIQ (PS03)
Validates normal and difficult/edge cases across:
- Deterministic Analytics Calculations
- Alert & Rule Engine (Rules 1-5)
- Grounded AI Copilot
- Hallucination Guardrails & Unknown Query Handling
- API Endpoints
"""

import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analytics import RetailAnalytics
from src.rules import AlertEngine
from src.retrieval import PolicyRetriever
from src.gemini import RetailCopilot
import app as flask_app

class TestRetailCopilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analytics = RetailAnalytics()
        cls.alert_engine = AlertEngine(cls.analytics)
        cls.retriever = PolicyRetriever()
        cls.copilot = RetailCopilot(cls.analytics, cls.alert_engine, cls.retriever)
        cls.client = flask_app.app.test_client()

    # =========================================================================
    # NORMAL CASES
    # =========================================================================

    def test_normal_kpi_calculation(self):
        """Verify high-level KPIs are calculated deterministically."""
        kpis = self.analytics.get_kpis()
        self.assertGreater(kpis["total_revenue"], 1_000_000.0)
        self.assertGreater(kpis["total_units_sold"], 10_000)
        self.assertGreater(kpis["total_inventory_units"], 1_000)
        self.assertGreater(kpis["inventory_valuation"], 50_000.0)

    def test_product_sales_lookup(self):
        """Verify product performance lookup returns verified numbers."""
        perf = self.analytics.get_single_product_performance("Laptop Pro")
        self.assertIsNotNone(perf)
        self.assertEqual(perf["product"]["product_name"], "Laptop Pro")
        self.assertGreater(perf["current_month_revenue"], 0)
        self.assertGreater(perf["revenue_30d"], 0)
        self.assertGreater(perf["total_current_stock"], 0)

    def test_store_sales_lookup(self):
        """Verify store performance rankings are calculated and sorted."""
        stores = self.analytics.get_store_performance()
        self.assertEqual(len(stores), 4)
        self.assertGreater(stores[0]["total_revenue"], stores[-1]["total_revenue"])

    def test_low_stock_detection_wireless_mouse(self):
        """
        Verify Rule 1 triggers accurately for Wireless Mouse at Downtown Flagship:
        Current stock: 12, ADS: ~5.0, Coverage: 2.4 days (< 5 days and <= lead time 4 days).
        """
        alerts = self.alert_engine.evaluate_all(store_id="S001")
        mouse_alert = next((a for a in alerts if a["product_id"] == "P002" and a["rule_id"] == "RULE_1_STOCKOUT"), None)
        self.assertIsNotNone(mouse_alert)
        self.assertEqual(mouse_alert["severity"], "CRITICAL")
        self.assertEqual(mouse_alert["actual_numbers"]["current_stock"], 12)
        self.assertAlmostEqual(mouse_alert["actual_numbers"]["days_of_stock"], 2.4, delta=0.2)
        self.assertEqual(mouse_alert["actual_numbers"]["lead_time_days"], 4)

    def test_overstock_detection(self):
        """Verify Rule 2 triggers for Ceramic Cookware Set (>60 days coverage)."""
        alerts = self.alert_engine.evaluate_all()
        overstock_alert = next((a for a in alerts if a["product_id"] == "P011" and a["rule_id"] == "RULE_2_OVERSTOCK"), None)
        self.assertIsNotNone(overstock_alert)
        self.assertGreater(overstock_alert["actual_numbers"]["days_of_stock"], 60.0)

    def test_slow_moving_detection(self):
        """Verify Rule 3 triggers for Vintage Leather Jacket (ADS < 0.20)."""
        alerts = self.alert_engine.evaluate_all()
        slow_alert = next((a for a in alerts if a["product_id"] == "P015" and a["rule_id"] == "RULE_3_SLOW_MOVING"), None)
        self.assertIsNotNone(slow_alert)
        self.assertLess(slow_alert["actual_numbers"]["ads_30d"], 0.20)

    def test_sales_spike_detection(self):
        """Verify Rule 4 triggers for Electric Toothbrush Pro at S001 (ADS 7d >= 2x ADS 30d)."""
        alerts = self.alert_engine.evaluate_all(store_id="S001")
        spike_alert = next((a for a in alerts if a["product_id"] == "P019" and a["rule_id"] == "RULE_4_SALES_SPIKE"), None)
        self.assertIsNotNone(spike_alert)
        self.assertGreaterEqual(spike_alert["actual_numbers"]["velocity_ratio"], 2.0)

    def test_sales_drop_detection(self):
        """Verify Rule 5 triggers for Artisan Sourdough at S003 (velocity drop <= 0.4x)."""
        alerts = self.alert_engine.evaluate_all(store_id="S003")
        drop_alert = next((a for a in alerts if a["product_id"] == "P006" and a["rule_id"] == "RULE_5_SALES_DROP"), None)
        self.assertIsNotNone(drop_alert)
        self.assertLessEqual(drop_alert["actual_numbers"]["velocity_ratio"], 0.40)

    # =========================================================================
    # DIFFICULT & EDGE CASES
    # =========================================================================

    def test_difficult_unknown_future_question(self):
        """
        User asks for speculative prediction 6 months from now.
        Must safely return: 'I don't have enough data to answer that.'
        """
        res = self.copilot.ask("What will our sales be exactly 6 months from now?")
        self.assertIn("I don't have enough data to answer that", res["answer"])
        self.assertIn("90-day", res["answer"])
        self.assertTrue(res["grounded"])

    def test_difficult_non_catalog_product(self):
        """
        User asks for an uncataloged item (iPhone 16).
        Must safely return: 'I don't have enough data to answer that.'
        """
        res = self.copilot.ask("How is iPhone 16 doing?")
        self.assertIn("I don't have enough data to answer that", res["answer"])
        self.assertIn("not found in the active product catalog", res["answer"])

    def test_difficult_empty_and_whitespace_query(self):
        """Query with empty string or spaces must not crash."""
        res = self.copilot.ask("   ")
        self.assertIn("Please provide a question", res["answer"])

    def test_difficult_gemini_unavailable_fallback(self):
        """
        Even without GEMINI_API_KEY, the copilot must generate a structured answer
        with SUMMARY, EVIDENCE, RULE CITED, RECOMMENDATION, and ASSUMPTIONS.
        """
        res = self.copilot.ask("Why is Wireless Mouse flagged?")
        answer = res["answer"]
        self.assertIn("### SUMMARY", answer)
        self.assertIn("### EVIDENCE", answer)
        self.assertIn("### RULE CITED", answer)
        self.assertIn("### RECOMMENDATION", answer)
        self.assertIn("### ASSUMPTIONS", answer)
        self.assertIn("12 units", answer)
        self.assertIn("2.4 days", answer)

    # =========================================================================
    # REST API ENDPOINTS
    # =========================================================================

    def test_api_dashboard(self):
        resp = self.client.get("/api/dashboard")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("kpis", data)
        self.assertIn("sales_trend", data)

    def test_api_products(self):
        resp = self.client.get("/api/products")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 84) # 21 products * 4 stores

    def test_api_inventory(self):
        resp = self.client.get("/api/inventory")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")

    def test_api_alerts(self):
        resp = self.client.get("/api/alerts")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["count"], 0)

    def test_api_chat(self):
        resp = self.client.post("/api/chat", json={"message": "What should I reorder?"})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("### SUMMARY", data["answer"])
        self.assertIn("### EVIDENCE", data["answer"])

if __name__ == "__main__":
    unittest.main()
