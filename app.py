"""
RetailIQ - Retail Sales and Inventory Copilot (TRACK_ID=PS03)
Main Flask application serving the web dashboard, REST APIs, and Grounded AI Copilot.
Runs on http://localhost:8000
"""

import os
import sys
import traceback
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables (.env if present)
load_dotenv()

from src.analytics import RetailAnalytics
from src.rules import AlertEngine
from src.retrieval import PolicyRetriever
from src.gemini import RetailCopilot

app = Flask(__name__, template_folder="templates", static_folder="static")

# Initialize authoritative singletons
try:
    analytics = RetailAnalytics()
    alert_engine = AlertEngine(analytics)
    retriever = PolicyRetriever()
    copilot = RetailCopilot(analytics=analytics, alert_engine=alert_engine, retriever=retriever)
    print("RetailIQ core services initialized successfully.")
except Exception as e:
    print(f"Error initializing RetailIQ core services: {e}", file=sys.stderr)
    traceback.print_exc()

@app.route("/")
def index():
    """Renders the main dashboard and copilot UI."""
    return render_template("index.html")

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_data():
    """
    Returns high-level retail KPIs, sales trends, category shares,
    store performance rankings, and alert counts.
    Supports optional ?store_id=S001 query filter.
    """
    try:
        store_id = request.args.get("store_id")
        if store_id == "ALL" or not store_id:
            store_id = None

        kpis = analytics.get_kpis(store_id=store_id)
        all_alerts = alert_engine.evaluate_all(store_id=store_id)
        
        # Categorize alerts for executive dashboard counters
        alert_summary = {
            "total": len(all_alerts),
            "critical": len([a for a in all_alerts if a["severity"] == "CRITICAL"]),
            "warning": len([a for a in all_alerts if a["severity"] == "WARNING"]),
            "opportunity": len([a for a in all_alerts if a["severity"] == "OPPORTUNITY"]),
            "stockouts": len([a for a in all_alerts if a["rule_id"] == "RULE_1_STOCKOUT"]),
            "overstocks": len([a for a in all_alerts if a["rule_id"] == "RULE_2_OVERSTOCK"]),
            "slow_moving": len([a for a in all_alerts if a["rule_id"] == "RULE_3_SLOW_MOVING"]),
            "spikes": len([a for a in all_alerts if a["rule_id"] == "RULE_4_SALES_SPIKE"]),
            "drops": len([a for a in all_alerts if a["rule_id"] == "RULE_5_SALES_DROP"])
        }
        kpis["products_needing_attention"] = alert_summary["total"]

        sales_trend = analytics.get_sales_timeseries(days=30, store_id=store_id)
        cat_performance = analytics.get_category_performance(store_id=store_id)
        store_performance = analytics.get_store_performance()
        stores_list = analytics.stores.to_dict(orient="records")

        # Top 5 priority alerts for immediate review
        top_alerts = all_alerts[:6]

        has_gemini = bool(os.getenv("GEMINI_API_KEY"))

        return jsonify({
            "status": "success",
            "kpis": kpis,
            "alert_summary": alert_summary,
            "sales_trend": sales_trend,
            "categories": cat_performance,
            "stores": store_performance,
            "store_list": stores_list,
            "top_alerts": top_alerts,
            "system_info": {
                "gemini_api_connected": has_gemini,
                "engine": "Gemini 1.5 Flash + Local RAG" if has_gemini else "Deterministic Grounded Synthesizer",
                "rules_loaded": 5
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/products", methods=["GET"])
def get_products():
    """Returns catalog products with real-time rolling metrics."""
    try:
        store_id = request.args.get("store_id")
        if store_id == "ALL" or not store_id:
            store_id = None
        metrics = analytics.get_product_metrics_table(store_id=store_id)
        return jsonify({"status": "success", "count": len(metrics), "data": metrics})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/next-product-id", methods=["GET"])
def get_next_product_id():
    """Returns the next unique product ID (e.g. P022)."""
    try:
        next_id = analytics.generate_next_product_id()
        return jsonify({"status": "success", "next_product_id": next_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/products", methods=["POST"])
def add_product():
    """Adds a new product and initializes store inventory."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        pid = analytics.add_product(data)
        return jsonify({
            "success": True,
            "message": "Product added successfully",
            "product_id": pid,
            "product_name": data.get("product_name")
        }), 201
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@app.route("/api/products/<product_id>", methods=["PUT", "PATCH"])
def update_product_endpoint(product_id):
    """Updates product catalog metadata (price, name, category, lead time, reorder, safety)."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        analytics.update_product(product_id, data)
        return jsonify({
            "success": True,
            "message": f"Product '{product_id}' updated successfully",
            "product_id": product_id
        }), 200
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@app.route("/api/products/<product_id>", methods=["DELETE"])
def delete_product_endpoint(product_id):
    """Deletes product from catalog and removes inventory records across all stores."""
    try:
        p_name = analytics.delete_product(product_id)
        return jsonify({
            "success": True,
            "message": f"Product '{p_name}' ({product_id}) successfully deleted from catalog and inventory.",
            "product_id": product_id,
            "product_name": p_name
        }), 200
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    """Returns inventory status with days of stock coverage and reorder flags."""
    try:
        store_id = request.args.get("store_id")
        if store_id == "ALL" or not store_id:
            store_id = None
        metrics = analytics.get_product_metrics_table(store_id=store_id)
        
        # Add stock status classification
        for m in metrics:
            days = m["days_of_stock"]
            stock = m["current_stock"]
            safety = m["safety_stock"]
            lead = m["lead_time_days"]
            has_sales = (m.get("total_units_sold", 0) > 0)
            
            if not has_sales:
                m["status_tag"] = "NO_SALES_HISTORY"
            elif days <= lead or days < 5.0 or stock <= safety:
                m["status_tag"] = "CRITICAL_LOW"
            elif days > 60.0 or stock > (3 * m["reorder_level"]):
                m["status_tag"] = "OVERSTOCKED"
            elif m["ads_30d"] < 0.20:
                m["status_tag"] = "SLOW_MOVING"
            else:
                m["status_tag"] = "HEALTHY"

        return jsonify({"status": "success", "count": len(metrics), "data": metrics})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/inventory", methods=["PUT", "PATCH"])
def update_inventory():
    """Updates inventory stock level for a product-store pair."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        product_id = data.get("product_id") or data.get("product_name") or data.get("product")
        store_id = data.get("store_id") or data.get("store")
        stock = data.get("stock")
        if stock is None:
            stock = data.get("new_stock")

        if not product_id:
            return jsonify({"success": False, "message": "Product ID or name is required."}), 400
        if not store_id:
            return jsonify({"success": False, "message": "Store is required."}), 400
        if stock is None:
            return jsonify({"success": False, "message": "Stock value is required."}), 400

        analytics.update_inventory(product_id, store_id, stock)
        return jsonify({
            "success": True,
            "message": "Inventory updated successfully",
            "product_id": product_id,
            "store_id": store_id,
            "new_stock": int(stock)
        }), 200
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@app.route("/api/sales", methods=["GET"])
def get_sales():
    """Returns sales records and timeseries."""
    try:
        days = int(request.args.get("days", 30))
        store_id = request.args.get("store_id")
        if store_id == "ALL" or not store_id:
            store_id = None
        trend = analytics.get_sales_timeseries(days=days, store_id=store_id)
        return jsonify({"status": "success", "data": trend})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Returns all active rule alerts evaluated by the deterministic engine."""
    try:
        store_id = request.args.get("store_id")
        rule_type = request.args.get("rule_type")
        if store_id == "ALL" or not store_id:
            store_id = None

        alerts = alert_engine.evaluate_all(store_id=store_id)

        if rule_type:
            alerts = [a for a in alerts if a["rule_id"] == rule_type]

        return jsonify({
            "status": "success",
            "count": len(alerts),
            "alerts": alerts
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    AI Copilot conversation endpoint.
    Accepts: { "message": "What is running out?", "store_id": "S001" (optional) }
    Returns structured, grounded answer with evidence payload and citations.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        message = data.get("message", "").strip()
        store_id = data.get("store_id")
        if store_id == "ALL" or not store_id:
            store_id = None

        if not message:
            return jsonify({
                "status": "error",
                "message": "Empty query provided."
            }), 400

        result = copilot.ask(message, store_id=store_id)
        return jsonify({
            "status": "success",
            "query": message,
            "answer": result["answer"],
            "evidence": result["evidence"],
            "citations": result["citations"],
            "intent": result.get("intent", "GENERAL"),
            "grounded": result.get("grounded", True)
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Failed to process inquiry: {str(e)}"
        }), 500

@app.route("/api/rules", methods=["GET"])
def get_rules():
    """Returns internal retail business policies from docs/retail_rules.md."""
    try:
        return jsonify({
            "status": "success",
            "sections": [
                {
                    "title": c["title"],
                    "citation": c["citation"],
                    "body": c["body"]
                }
                for c in retriever.chunks
            ]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"\n=======================================================")
    print(f" RetailIQ Copilot running at: http://localhost:{port}")
    print(f" Gemini API: {'Configured (os.getenv)' if os.getenv('GEMINI_API_KEY') else 'Offline/Fallback mode (No key set)'}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
