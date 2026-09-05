"""
Authoritative Deterministic Analytics Module for RetailIQ
Performs 100% verified numerical calculations using Pandas and NumPy.
Never relies on LLMs for calculations.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

class RetailAnalytics:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.load_data()

    def load_data(self):
        """Loads and prepares datasets into pandas DataFrames."""
        self.products = pd.read_csv(os.path.join(self.data_dir, "products.csv"))
        self.stores = pd.read_csv(os.path.join(self.data_dir, "stores.csv"))
        self.inventory = pd.read_csv(os.path.join(self.data_dir, "inventory.csv"))
        self.sales = pd.read_csv(os.path.join(self.data_dir, "sales.csv"))
        
        # Format dates and sort
        self.sales["date"] = pd.to_datetime(self.sales["date"])
        self.sales = self.sales.sort_values(by=["date", "product_id", "store_id"]).reset_index(drop=True)
        
        # Reference max date in dataset as "today"
        self.max_date = self.sales["date"].max()
        self.min_date = self.sales["date"].min()

    def get_kpis(self, store_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates executive high-level retail KPIs."""
        sales_df = self.sales if not store_id else self.sales[self.sales["store_id"] == store_id]
        inv_df = self.inventory if not store_id else self.inventory[self.inventory["store_id"] == store_id]

        total_revenue = float(sales_df["total_revenue"].sum())
        total_units_sold = int(sales_df["units_sold"].sum())
        total_inventory_units = int(inv_df["current_stock"].sum())
        
        # Calculate inventory valuation: stock * unit_cost
        inv_val = float((inv_df["current_stock"] * inv_df["unit_cost"]).sum())

        # Trailing 30 days revenue
        cutoff_30d = self.max_date - timedelta(days=29)
        recent_sales = sales_df[sales_df["date"] >= cutoff_30d]
        revenue_30d = float(recent_sales["total_revenue"].sum())
        units_30d = int(recent_sales["units_sold"].sum())

        return {
            "total_revenue": round(total_revenue, 2),
            "total_units_sold": total_units_sold,
            "total_inventory_units": total_inventory_units,
            "inventory_valuation": round(inv_val, 2),
            "revenue_30d": round(revenue_30d, 2),
            "units_30d": units_30d,
            "reference_date": self.max_date.strftime("%Y-%m-%d"),
            "data_start_date": self.min_date.strftime("%Y-%m-%d"),
            "total_stores": len(self.stores),
            "total_products": len(self.products)
        }

    def get_sales_timeseries(self, days: int = 30, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns daily sales aggregations for charts."""
        cutoff = self.max_date - timedelta(days=days - 1)
        df = self.sales[self.sales["date"] >= cutoff]
        if store_id:
            df = df[df["store_id"] == store_id]

        daily = df.groupby(df["date"].dt.strftime("%Y-%m-%d")).agg({
            "total_revenue": "sum",
            "units_sold": "sum"
        }).reset_index()

        daily["total_revenue"] = daily["total_revenue"].round(2)
        return daily.to_dict(orient="records")

    def get_category_performance(self, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Calculates sales and inventory metrics by product category."""
        sales_merged = self.sales.merge(self.products, on="product_id")
        if store_id:
            sales_merged = sales_merged[sales_merged["store_id"] == store_id]

        cat_sales = sales_merged.groupby("category").agg({
            "total_revenue": "sum",
            "units_sold": "sum",
            "product_id": "nunique"
        }).reset_index().rename(columns={"product_id": "product_count"})

        total_rev = cat_sales["total_revenue"].sum()
        cat_sales["revenue_share_pct"] = ((cat_sales["total_revenue"] / total_rev) * 100).round(1) if total_rev > 0 else 0
        cat_sales["total_revenue"] = cat_sales["total_revenue"].round(2)

        return cat_sales.sort_values(by="total_revenue", ascending=False).to_dict(orient="records")

    def get_store_performance(self) -> List[Dict[str, Any]]:
        """Calculates store comparative metrics."""
        results = []
        for _, st in self.stores.iterrows():
            sid = st["store_id"]
            sname = st["store_name"]
            sloc = st["location"]

            s_sales = self.sales[self.sales["store_id"] == sid]
            s_inv = self.inventory[self.inventory["store_id"] == sid]

            # 30-day window
            cutoff_30d = self.max_date - timedelta(days=29)
            recent_sales = s_sales[s_sales["date"] >= cutoff_30d]

            tot_rev = float(s_sales["total_revenue"].sum())
            tot_units = int(s_sales["units_sold"].sum())
            rev_30d = float(recent_sales["total_revenue"].sum())
            units_30d = int(recent_sales["units_sold"].sum())
            stock = int(s_inv["current_stock"].sum())
            inv_val = float((s_inv["current_stock"] * s_inv["unit_cost"]).sum())

            results.append({
                "store_id": sid,
                "store_name": sname,
                "location": sloc,
                "total_revenue": round(tot_rev, 2),
                "total_units_sold": tot_units,
                "revenue_30d": round(rev_30d, 2),
                "units_30d": units_30d,
                "current_stock": stock,
                "inventory_valuation": round(inv_val, 2)
            })

        results.sort(key=lambda x: x["total_revenue"], reverse=True)
        return results

    def get_product_metrics_table(self, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Computes detailed rolling ADS, days of stock, and velocity for all product-store pairs.
        Authoritative single source of truth for the Alert Engine and UI tables.
        """
        cutoff_7d = self.max_date - timedelta(days=6)
        cutoff_30d = self.max_date - timedelta(days=29)

        # Merge inventory with product and store details
        inv_full = self.inventory.merge(self.products, on="product_id").merge(self.stores, on="store_id")
        if store_id:
            inv_full = inv_full[inv_full["store_id"] == store_id]

        records = []
        for _, row in inv_full.iterrows():
            pid = row["product_id"]
            sid = row["store_id"]
            stock = int(row["current_stock"])
            reorder = int(row["reorder_level"])
            safety = int(row["safety_stock"])
            lead_time = int(row["lead_time_days"])
            price = float(row["selling_price"])
            cost = float(row["unit_cost"])

            # Filter sales for this combo
            ps_sales = self.sales[(self.sales["product_id"] == pid) & (self.sales["store_id"] == sid)]

            # 7-day sales
            s7 = ps_sales[ps_sales["date"] >= cutoff_7d]
            units_7d = int(s7["units_sold"].sum())
            rev_7d = float(s7["total_revenue"].sum())
            ads_7d = round(units_7d / 7.0, 2)

            # 30-day sales
            s30 = ps_sales[ps_sales["date"] >= cutoff_30d]
            units_30d = int(s30["units_sold"].sum())
            rev_30d = float(s30["total_revenue"].sum())
            ads_30d = round(units_30d / 30.0, 2)

            # All-time sales in window
            total_units = int(ps_sales["units_sold"].sum())
            total_rev = float(ps_sales["total_revenue"].sum())

            # Effective velocity for coverage calculation:
            # We use ADS 7d if available and meaningful; otherwise fallback to ADS 30d
            effective_ads = ads_7d if ads_7d > 0 else ads_30d

            # Days of stock remaining
            if effective_ads > 0:
                days_of_stock = round(stock / effective_ads, 1)
            else:
                days_of_stock = 999.0 if stock > 0 else 0.0

            # Velocity ratio: recent vs baseline
            if ads_30d > 0:
                velocity_ratio = round(ads_7d / ads_30d, 2)
            elif ads_7d > 0:
                velocity_ratio = 9.99 # Infinite spike from 0
            else:
                velocity_ratio = 1.0

            records.append({
                "product_id": pid,
                "product_name": row["product_name"],
                "category": row["category"],
                "store_id": sid,
                "store_name": row["store_name"],
                "selling_price": price,
                "unit_cost": cost,
                "gross_margin_pct": round(((price - cost) / price) * 100, 1) if price > 0 else 0.0,
                "lead_time_days": lead_time,
                "current_stock": stock,
                "reorder_level": reorder,
                "safety_stock": safety,
                "units_sold_7d": units_7d,
                "revenue_7d": round(rev_7d, 2),
                "ads_7d": ads_7d,
                "units_sold_30d": units_30d,
                "revenue_30d": round(rev_30d, 2),
                "ads_30d": ads_30d,
                "effective_ads": effective_ads,
                "days_of_stock": days_of_stock,
                "velocity_ratio": velocity_ratio,
                "total_units_sold": total_units,
                "total_revenue": round(total_rev, 2)
            })

        return records

    def find_product_by_name(self, query: str) -> Optional[Dict[str, Any]]:
        """Fuzzy/substring search for product in catalog."""
        q = query.strip().lower()
        # Direct match first
        for _, p in self.products.iterrows():
            if q == p["product_name"].lower() or q == p["product_id"].lower():
                return p.to_dict()
        # Substring match
        for _, p in self.products.iterrows():
            if q in p["product_name"].lower() or p["product_name"].lower() in q:
                return p.to_dict()
        # Word overlap
        q_words = set(q.split())
        best_match = None
        best_score = 0
        for _, p in self.products.iterrows():
            p_words = set(p["product_name"].lower().split())
            overlap = len(q_words.intersection(p_words))
            if overlap > best_score:
                best_score = overlap
                best_match = p.to_dict()
        if best_score > 0:
            return best_match
        return None

    def get_single_product_performance(self, product_identifier: str, store_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Comprehensive performance profile for a specific product."""
        prod = self.find_product_by_name(product_identifier)
        if not prod:
            return None

        pid = prod["product_id"]
        all_metrics = self.get_product_metrics_table(store_id=store_id)
        prod_metrics = [m for m in all_metrics if m["product_id"] == pid]

        if not prod_metrics:
            return None

        # Aggregate across stores if store_id was not specified
        total_current_stock = sum(m["current_stock"] for m in prod_metrics)
        total_units_7d = sum(m["units_sold_7d"] for m in prod_metrics)
        total_revenue_7d = sum(m["revenue_7d"] for m in prod_metrics)
        total_units_30d = sum(m["units_sold_30d"] for m in prod_metrics)
        total_revenue_30d = sum(m["revenue_30d"] for m in prod_metrics)
        total_units_all = sum(m["total_units_sold"] for m in prod_metrics)
        total_rev_all = sum(m["total_revenue"] for m in prod_metrics)
        
        # Weighted ADS across stores
        avg_ads_7d = round(sum(m["ads_7d"] for m in prod_metrics), 2)
        avg_ads_30d = round(sum(m["ads_30d"] for m in prod_metrics), 2)
        
        overall_coverage = round(total_current_stock / avg_ads_7d, 1) if avg_ads_7d > 0 else (round(total_current_stock / avg_ads_30d, 1) if avg_ads_30d > 0 else 999.0)

        # Monthly performance breakdown (current calendar month in dataset)
        curr_month = self.max_date.month
        curr_year = self.max_date.year
        month_sales = self.sales[(self.sales["product_id"] == pid) & 
                                 (self.sales["date"].dt.month == curr_month) & 
                                 (self.sales["date"].dt.year == curr_year)]
        if store_id:
            month_sales = month_sales[month_sales["store_id"] == store_id]

        month_units = int(month_sales["units_sold"].sum())
        month_rev = float(month_sales["total_revenue"].sum())

        return {
            "product": prod,
            "store_id": store_id,
            "total_current_stock": total_current_stock,
            "avg_ads_7d": avg_ads_7d,
            "avg_ads_30d": avg_ads_30d,
            "overall_days_of_stock": overall_coverage,
            "units_sold_7d": total_units_7d,
            "revenue_7d": round(total_revenue_7d, 2),
            "units_sold_30d": total_units_30d,
            "revenue_30d": round(total_revenue_30d, 2),
            "current_month_name": self.max_date.strftime("%B %Y"),
            "current_month_units": month_units,
            "current_month_revenue": round(month_rev, 2),
            "total_units_sold_all_time": total_units_all,
            "total_revenue_all_time": round(total_rev_all, 2),
            "store_breakdown": prod_metrics
        }

    def generate_next_product_id(self) -> str:
        """Inspects existing products and returns the next unique Product ID (e.g. P022)."""
        existing_ids = self.products["product_id"].astype(str).tolist()
        max_num = 0
        for pid in existing_ids:
            digits = "".join(filter(str.isdigit, pid))
            if digits:
                max_num = max(max_num, int(digits))
        next_id = f"P{max_num + 1:03d}"
        while next_id in existing_ids:
            max_num += 1
            next_id = f"P{max_num:03d}"
        return next_id

    def resolve_store_id(self, store_input: str) -> Optional[str]:
        """Resolves store ID from either store_id or store_name string."""
        s_in = str(store_input).strip().lower()
        for _, s in self.stores.iterrows():
            if s_in == s["store_id"].lower() or s_in == s["store_name"].lower() or s_in in s["store_name"].lower():
                return s["store_id"]
        return None

    def add_product(self, product_dict: Dict[str, Any]) -> str:
        """
        Validates input and safely adds product to data/products.csv and data/inventory.csv.
        Reloads datasets in memory upon success.
        """
        name = str(product_dict.get("product_name", "")).strip()
        if not name:
            raise ValueError("Product name is required.")

        category = str(product_dict.get("category", "")).strip()
        if not category:
            raise ValueError("Category is required.")

        raw_price = product_dict.get("selling_price")
        if raw_price is None:
            raw_price = product_dict.get("unit_price", product_dict.get("price", 0))
        try:
            price = float(raw_price)
        except (ValueError, TypeError):
            raise ValueError("Please enter a valid unit price.")
        if price <= 0:
            raise ValueError("Please enter a valid unit price.")

        raw_stock = product_dict.get("initial_stock")
        if raw_stock is None:
            raw_stock = product_dict.get("current_stock", product_dict.get("stock", 0))
        try:
            initial_stock = int(raw_stock)
        except (ValueError, TypeError):
            raise ValueError("Initial stock must be an integer.")
        if initial_stock < 0:
            raise ValueError("Initial stock cannot be negative.")

        try:
            reorder = int(product_dict.get("reorder_level", 0))
        except (ValueError, TypeError):
            raise ValueError("Reorder level must be an integer.")
        if reorder < 0:
            raise ValueError("Reorder level cannot be negative.")

        try:
            safety = int(product_dict.get("safety_stock", 0))
        except (ValueError, TypeError):
            raise ValueError("Safety stock must be an integer.")
        if safety < 0:
            raise ValueError("Safety stock cannot be negative.")

        try:
            lead = int(product_dict.get("lead_time", product_dict.get("lead_time_days", 4)))
        except (ValueError, TypeError):
            raise ValueError("Lead time must be an integer.")
        if lead <= 0:
            raise ValueError("Lead time must be a positive number.")

        store_input = str(product_dict.get("store", product_dict.get("store_id", ""))).strip()
        store_id = self.resolve_store_id(store_input)
        if not store_id:
            raise ValueError(f"Please select a valid store. '{store_input}' not recognized.")

        # Check for duplicate product name
        existing_names = [n.lower() for n in self.products["product_name"].tolist()]
        if name.lower() in existing_names:
            raise ValueError(f"Product '{name}' already exists in catalog.")

        # Generate unique product ID
        pid = self.generate_next_product_id()
        supplier = str(product_dict.get("supplier", "Supplier Direct")).strip() or "Supplier Direct"
        unit_cost = round(price * 0.55, 2)

        # 1. Update products.csv
        products_path = os.path.join(self.data_dir, "products.csv")
        new_prod_row = pd.DataFrame([{
            "product_id": pid,
            "product_name": name,
            "category": category,
            "selling_price": price,
            "supplier": supplier,
            "lead_time_days": lead
        }])
        new_prod_row.to_csv(products_path, mode="a", header=False, index=False)

        # 2. Update inventory.csv for all stores
        inventory_path = os.path.join(self.data_dir, "inventory.csv")
        inv_rows = []
        for _, st in self.stores.iterrows():
            sid = st["store_id"]
            stk = initial_stock if sid == store_id else 0
            inv_rows.append({
                "product_id": pid,
                "store_id": sid,
                "current_stock": stk,
                "reorder_level": reorder,
                "safety_stock": safety,
                "unit_cost": unit_cost
            })
        df_new_inv = pd.DataFrame(inv_rows)
        df_new_inv.to_csv(inventory_path, mode="a", header=False, index=False)

        # 3. Reload in-memory datasets
        self.load_data()
        return pid

    def update_inventory(self, product_input: str, store_input: str, new_stock: int) -> bool:
        """
        Updates stock level for a product-store pair in data/inventory.csv.
        Reloads datasets in memory upon success.
        """
        p_in = str(product_input).strip()
        # Resolve product ID
        existing_pids = self.products["product_id"].tolist()
        pid = None
        if p_in in existing_pids:
            pid = p_in
        else:
            prod = self.find_product_by_name(p_in)
            if prod:
                pid = prod["product_id"]
            else:
                raise ValueError(f"Product '{product_input}' does not exist.")

        store_id = self.resolve_store_id(store_input)
        if not store_id:
            raise ValueError(f"Store '{store_input}' does not exist.")

        try:
            stock_val = int(new_stock)
        except (ValueError, TypeError):
            raise ValueError("Stock must be an integer.")
        if stock_val < 0:
            raise ValueError("Stock cannot be negative.")

        inventory_path = os.path.join(self.data_dir, "inventory.csv")
        df_inv = pd.read_csv(inventory_path)

        mask = (df_inv["product_id"] == pid) & (df_inv["store_id"] == store_id)
        if not mask.any():
            prod_row = self.products[self.products["product_id"] == pid].iloc[0]
            cost = round(float(prod_row["selling_price"]) * 0.55, 2)
            lead = int(prod_row["lead_time_days"])
            new_row = pd.DataFrame([{
                "product_id": pid,
                "store_id": store_id,
                "current_stock": stock_val,
                "reorder_level": 20,
                "safety_stock": 10,
                "unit_cost": cost
            }])
            df_inv = pd.concat([df_inv, new_row], ignore_index=True)
        else:
            df_inv.loc[mask, "current_stock"] = stock_val

        # Safe atomic write via temporary file
        temp_path = inventory_path + ".tmp"
        df_inv.to_csv(temp_path, index=False)
        os.replace(temp_path, inventory_path)

        # Reload in-memory datasets
        self.load_data()
        return True

    def update_product(self, product_input: str, updates: Dict[str, Any]) -> bool:
        """
        Updates product attributes (selling_price, product_name, category, lead_time_days)
        and optionally reorder_level/safety_stock across inventory.
        """
        p_in = str(product_input).strip()
        existing_pids = self.products["product_id"].tolist()
        pid = None
        if p_in in existing_pids:
            pid = p_in
        else:
            prod = self.find_product_by_name(p_in)
            if prod:
                pid = prod["product_id"]
            else:
                raise ValueError(f"Product '{product_input}' does not exist.")

        products_path = os.path.join(self.data_dir, "products.csv")
        df_prod = pd.read_csv(products_path)

        p_mask = df_prod["product_id"] == pid
        if not p_mask.any():
            raise ValueError(f"Product ID '{pid}' not found in products catalog.")

        if "product_name" in updates and updates["product_name"]:
            df_prod.loc[p_mask, "product_name"] = str(updates["product_name"]).strip()
        if "category" in updates and updates["category"]:
            df_prod.loc[p_mask, "category"] = str(updates["category"]).strip()
        if "selling_price" in updates and updates["selling_price"] is not None:
            price_val = float(updates["selling_price"])
            if price_val <= 0:
                raise ValueError("Price must be greater than 0.")
            df_prod.loc[p_mask, "selling_price"] = price_val
        if "lead_time_days" in updates and updates["lead_time_days"] is not None:
            lead_val = int(updates["lead_time_days"])
            if lead_val < 1:
                raise ValueError("Lead time must be at least 1 day.")
            df_prod.loc[p_mask, "lead_time_days"] = lead_val

        temp_prod = products_path + ".tmp"
        df_prod.to_csv(temp_prod, index=False)
        os.replace(temp_prod, products_path)

        # If reorder_level or safety_stock passed, update inventory
        inv_path = os.path.join(self.data_dir, "inventory.csv")
        df_inv = pd.read_csv(inv_path)
        inv_mask = df_inv["product_id"] == pid
        inv_modified = False

        if "reorder_level" in updates and updates["reorder_level"] is not None:
            r_val = int(updates["reorder_level"])
            if r_val >= 0:
                df_inv.loc[inv_mask, "reorder_level"] = r_val
                inv_modified = True

        if "safety_stock" in updates and updates["safety_stock"] is not None:
            s_val = int(updates["safety_stock"])
            if s_val >= 0:
                df_inv.loc[inv_mask, "safety_stock"] = s_val
                inv_modified = True

        if inv_modified:
            temp_inv = inv_path + ".tmp"
            df_inv.to_csv(temp_inv, index=False)
            os.replace(temp_inv, inv_path)

        self.load_data()
        return True

    def delete_product(self, product_input: str) -> str:
        """
        Deletes a product from data/products.csv and its records from data/inventory.csv.
        Reloads in-memory datasets upon success.
        """
        p_in = str(product_input).strip()
        existing_pids = self.products["product_id"].tolist()
        pid = None
        p_name = None

        if p_in in existing_pids:
            pid = p_in
            row = self.products[self.products["product_id"] == pid].iloc[0]
            p_name = str(row["product_name"])
        else:
            prod = self.find_product_by_name(p_in)
            if prod:
                pid = prod["product_id"]
                p_name = prod["product_name"]
            else:
                raise ValueError(f"Product '{product_input}' does not exist.")

        # Remove from products.csv
        products_path = os.path.join(self.data_dir, "products.csv")
        df_prod = pd.read_csv(products_path)
        df_prod = df_prod[df_prod["product_id"] != pid]
        temp_prod = products_path + ".tmp"
        df_prod.to_csv(temp_prod, index=False)
        os.replace(temp_prod, products_path)

        # Remove from inventory.csv
        inventory_path = os.path.join(self.data_dir, "inventory.csv")
        df_inv = pd.read_csv(inventory_path)
        df_inv = df_inv[df_inv["product_id"] != pid]
        temp_inv = inventory_path + ".tmp"
        df_inv.to_csv(temp_inv, index=False)
        os.replace(temp_inv, inventory_path)

        self.load_data()
        return p_name

