"""
Live HTTP verification script for running RetailIQ server.
"""
import requests

base = "http://127.0.0.1:8000"

print("--- Testing GET / ---")
r_index = requests.get(base + "/")
print("Status:", r_index.status_code, "HTML Length:", len(r_index.text))
assert r_index.status_code == 200
assert "RetailIQ" in r_index.text

print("--- Testing GET /api/dashboard ---")
r_dash = requests.get(base + "/api/dashboard")
print("Status:", r_dash.status_code)
d_dash = r_dash.json()
print("KPIs:", d_dash["kpis"])
assert d_dash["status"] == "success"

print("--- Testing GET /api/products ---")
r_prod = requests.get(base + "/api/products")
print("Status:", r_prod.status_code, "Count:", r_prod.json()["count"])
assert r_prod.status_code == 200

print("--- Testing GET /api/inventory ---")
r_inv = requests.get(base + "/api/inventory")
print("Status:", r_inv.status_code, "Count:", r_inv.json()["count"])
assert r_inv.status_code == 200

print("--- Testing GET /api/sales ---")
r_sales = requests.get(base + "/api/sales?days=30")
print("Status:", r_sales.status_code, "Records:", len(r_sales.json()["data"]))
assert r_sales.status_code == 200

print("--- Testing GET /api/alerts ---")
r_alerts = requests.get(base + "/api/alerts")
print("Status:", r_alerts.status_code, "Alert count:", r_alerts.json()["count"])
assert r_alerts.status_code == 200

print("--- Testing POST /api/chat (Demo 1: Attention) ---")
r_c1 = requests.post(base + "/api/chat", json={"message": "What products need attention today?"})
print("Status:", r_c1.status_code)
ans1 = r_c1.json()["answer"]
assert "SUMMARY" in ans1
print("Demo 1 Answer Snippet:\n", ans1[:200], "\n...")

print("--- Testing POST /api/chat (Demo 2: Wireless Mouse) ---")
r_c2 = requests.post(base + "/api/chat", json={"message": "Why is Wireless Mouse flagged?"})
print("Status:", r_c2.status_code)
ans2 = r_c2.json()["answer"]
assert "Wireless Mouse" in ans2
assert "2.4 days" in ans2
print("Demo 2 Answer Snippet:\n", ans2[:250], "\n...")

print("--- Testing POST /api/chat (Demo 3: Laptop Pro) ---")
r_c3 = requests.post(base + "/api/chat", json={"message": "How did Laptop Pro perform this month?"})
print("Status:", r_c3.status_code)
ans3 = r_c3.json()["answer"]
assert "Laptop Pro" in ans3
print("Demo 3 Answer Snippet:\n", ans3[:250], "\n...")

print("--- Testing POST /api/chat (Demo 4: Reorder) ---")
r_c4 = requests.post(base + "/api/chat", json={"message": "What should I reorder?"})
print("Status:", r_c4.status_code)
ans4 = r_c4.json()["answer"]
assert "reorder" in ans4.lower() or "order" in ans4.lower()
print("Demo 4 Answer Snippet:\n", ans4[:250], "\n...")

print("--- Testing POST /api/chat (Edge Case: 6 months future) ---")
r_c5 = requests.post(base + "/api/chat", json={"message": "What will our sales be exactly 6 months from now?"})
print("Status:", r_c5.status_code)
ans5 = r_c5.json()["answer"]
assert "I don't have enough data to answer that." in ans5
print("Guardrail Answer Snippet:\n", ans5[:200], "\n...")

print("\n=======================================================")
print(">>> ALL LIVE HTTP ENDPOINTS TESTED & VERIFIED 100% OK! <<<")
print("=======================================================\n")
