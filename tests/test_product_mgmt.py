"""
Automated Test Suite for Product Management & Inventory Controls in RetailIQ (PS03)
Tests:
- Unique Product ID Generation (GET /api/next-product-id)
- Adding New Products (POST /api/products)
- Updating Inventory Stock (PUT /api/inventory)
- Input Validation & Guardrails (duplicate name, negative price/stock, lead time)
- Deterministic Inventory Status (NO_SALES_HISTORY)
- Zero Hallucination AI Copilot Handling for New Products
"""

import os
import sys
import shutil
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analytics import RetailAnalytics
from src.rules import AlertEngine
from src.retrieval import PolicyRetriever
from src.gemini import RetailCopilot
import app as flask_app

class TestProductManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Backup CSV files before running tests
        cls.products_csv = os.path.abspath("data/products.csv")
        cls.inventory_csv = os.path.abspath("data/inventory.csv")
        cls.products_bak = cls.products_csv + ".test_bak"
        cls.inventory_bak = cls.inventory_csv + ".test_bak"

        shutil.copyfile(cls.products_csv, cls.products_bak)
        shutil.copyfile(cls.inventory_csv, cls.inventory_bak)

        cls.client = flask_app.app.test_client()
        cls.analytics = flask_app.analytics
        cls.alert_engine = flask_app.alert_engine
        cls.retriever = flask_app.retriever
        cls.copilot = flask_app.copilot

    @classmethod
    def tearDownClass(cls):
        # Restore original CSV files after tests
        if os.path.exists(cls.products_bak):
            shutil.copyfile(cls.products_bak, cls.products_csv)
            os.remove(cls.products_bak)
        if os.path.exists(cls.inventory_bak):
            shutil.copyfile(cls.inventory_bak, cls.inventory_csv)
            os.remove(cls.inventory_bak)
        cls.analytics.load_data()

    def test_01_get_next_product_id(self):
        """Verify next product ID is generated with 'P' prefix and correct increment."""
        res = self.client.get("/api/next-product-id")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        next_id = data.get("next_product_id")
        self.assertTrue(next_id.startswith("P"))
        num_part = int(next_id[1:])
        self.assertGreaterEqual(num_part, 22)

    def test_02_add_product_validation_missing_name(self):
        """Ensure adding product without name is rejected with 400."""
        payload = {
            "product_name": "",
            "category": "Wearables",
            "selling_price": 99.99,
            "store": "Downtown Flagship",
            "current_stock": 20
        }
        res = self.client.post("/api/products", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("name", data.get("message", "").lower())

    def test_03_add_product_validation_negative_numbers(self):
        """Ensure negative price, stock, or lead time are rejected with 400."""
        # Negative price
        res = self.client.post("/api/products", json={
            "product_name": "Invalid Price Item",
            "category": "Audio",
            "selling_price": -10.0,
            "store": "S001"
        })
        self.assertEqual(res.status_code, 400)

        # Negative stock
        res = self.client.post("/api/products", json={
            "product_name": "Invalid Stock Item",
            "category": "Audio",
            "selling_price": 10.0,
            "current_stock": -5,
            "store": "S001"
        })
        self.assertEqual(res.status_code, 400)

        # Invalid lead time (< 1)
        res = self.client.post("/api/products", json={
            "product_name": "Invalid Lead Item",
            "category": "Audio",
            "selling_price": 10.0,
            "lead_time_days": 0,
            "store": "S001"
        })
        self.assertEqual(res.status_code, 400)

    def test_04_add_product_success(self):
        """Verify successful product registration and inventory provisioning."""
        payload = {
            "product_name": "Smart Watch Pro",
            "category": "Wearables",
            "selling_price": 199.99,
            "store": "Downtown Flagship",
            "current_stock": 50,
            "reorder_level": 20,
            "safety_stock": 10,
            "lead_time_days": 7,
            "supplier": "Apex Tech Electronics"
        }
        res = self.client.post("/api/products", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        new_pid = data.get("product_id")
        self.assertTrue(new_pid.startswith("P"))

        # Verify product exists in analytics catalogue
        matching = self.analytics.products[self.analytics.products["product_name"] == "Smart Watch Pro"]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching.iloc[0]["category"], "Wearables")
        self.assertEqual(float(matching.iloc[0]["selling_price"]), 199.99)

        # Verify inventory provisioned across all stores
        inv_table = self.analytics.get_product_metrics_table()
        smart_watch_inv = [i for i in inv_table if i["product_name"] == "Smart Watch Pro"]
        self.assertEqual(len(smart_watch_inv), 4)

        # Selected store (Downtown Flagship - S001) has 50 stock, other stores have 0
        downtown_row = next(r for r in smart_watch_inv if r["store_id"] == "S001")
        self.assertEqual(downtown_row["current_stock"], 50)
        self.assertEqual(downtown_row["reorder_level"], 20)
        self.assertEqual(downtown_row["safety_stock"], 10)
        self.assertEqual(downtown_row["lead_time_days"], 7)

        other_rows = [r for r in smart_watch_inv if r["store_id"] != "S001"]
        for r in other_rows:
            self.assertEqual(r["current_stock"], 0)

    def test_05_add_duplicate_product_rejected(self):
        """Verify attempting to add the same product name again is rejected."""
        payload = {
            "product_name": "Smart Watch Pro",
            "category": "Wearables",
            "selling_price": 199.99,
            "store": "S001",
            "current_stock": 20
        }
        res = self.client.post("/api/products", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("already exists", data.get("message", "").lower())

    def test_06_inventory_api_status_tag_for_new_product(self):
        """Verify GET /api/inventory assigns NO_SALES_HISTORY tag to newly added product."""
        res = self.client.get("/api/inventory")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        items = data.get("data", [])
        new_items = [i for i in items if i["product_name"] == "Smart Watch Pro"]
        self.assertGreater(len(new_items), 0)
        for item in new_items:
            self.assertEqual(item["status_tag"], "NO_SALES_HISTORY")

    def test_07_update_inventory_stock(self):
        """Verify updating inventory stock level directly via API."""
        payload = {
            "product_name": "Smart Watch Pro",
            "store": "Downtown Flagship",
            "stock": 85
        }
        res = self.client.put("/api/inventory", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("new_stock"), 85)

        # Verify updated in inventory table
        inv_table = self.analytics.get_product_metrics_table(store_id="S001")
        item = next(i for i in inv_table if i["product_name"] == "Smart Watch Pro")
        self.assertEqual(item["current_stock"], 85)

    def test_08_update_inventory_validation(self):
        """Verify update inventory rejects negative stock or invalid product."""
        # Negative stock
        res = self.client.put("/api/inventory", json={
            "product_id": "P001",
            "store_id": "S001",
            "stock": -10
        })
        self.assertEqual(res.status_code, 400)

        # Non-existent product
        res = self.client.put("/api/inventory", json={
            "product_id": "P9999",
            "store_id": "S001",
            "stock": 10
        })
        self.assertEqual(res.status_code, 400)

    def test_09_copilot_stock_query_for_new_product(self):
        """Verify Copilot correctly reports stock on hand for new product without hallucination."""
        ans = self.copilot.ask("Do we have Smart Watch Pro in stock?")
        self.assertTrue(ans.get("grounded", False))
        self.assertEqual(ans["intent"], "SPECIFIC_PRODUCT")
        # Evidence must report exact stock (85)
        self.assertIn("Smart Watch Pro", ans["answer"])
        self.assertIn("85", ans["answer"])
        # Must NOT claim historical units were sold
        self.assertEqual(ans["evidence"].get("total_units_sold", 0), 0)

    def test_10_copilot_performance_query_for_new_product(self):
        """Verify Copilot answers: 'I don't have enough sales history to answer that' for product with 0 sales."""
        ans = self.copilot.ask("How did Smart Watch Pro perform this month?")
        self.assertTrue(ans.get("grounded", False))
        self.assertEqual(ans["intent"], "SPECIFIC_PRODUCT")
        lower_ans = ans["answer"].lower()
        self.assertIn("don't have enough sales history", lower_ans)
        self.assertIn("smart watch pro", lower_ans)
        # Evidence confirms 0 POS transactions
        self.assertEqual(ans["evidence"].get("total_units_sold", 0), 0)

    def test_11_update_product_metadata(self):
        """Verify updating product catalog properties (price, category, lead time, reorder)."""
        res = self.client.put("/api/products/Smart Watch Pro", json={
            "selling_price": 249.99,
            "category": "Electronics",
            "lead_time_days": 10,
            "reorder_level": 25
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))

        prod = self.analytics.find_product_by_name("Smart Watch Pro")
        self.assertEqual(float(prod["selling_price"]), 249.99)
        self.assertEqual(prod["category"], "Electronics")
        self.assertEqual(int(prod["lead_time_days"]), 10)

    def test_12_delete_product(self):
        """Verify permanently deleting a product from catalog and inventory."""
        res = self.client.delete("/api/products/Smart Watch Pro")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))

        # Verify product no longer exists in catalog
        matching = self.analytics.products[self.analytics.products["product_name"] == "Smart Watch Pro"]
        self.assertEqual(len(matching), 0)

        # Verify all store inventory rows for this product are deleted
        inv_table = self.analytics.get_product_metrics_table()
        matching_inv = [i for i in inv_table if i["product_name"] == "Smart Watch Pro"]
        self.assertEqual(len(matching_inv), 0)

if __name__ == "__main__":
    unittest.main()
