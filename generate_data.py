"""
Synthetic Retail Data Generator for RetailIQ (NexusTiQ Hackathon PS6)
Generates realistic multi-store data covering:
- products.csv
- stores.csv
- inventory.csv
- sales.csv (90 days of daily sales)
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Set fixed seed for 100% reproducible and verifiable data
random.seed(42)
np.random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 1. Stores
stores_data = [
    {"store_id": "S001", "store_name": "Downtown Flagship", "location": "Downtown Financial District"},
    {"store_id": "S002", "store_name": "Westside Mall", "location": "Westside Retail Plaza"},
    {"store_id": "S003", "store_name": "Suburban Center", "location": "North Suburbs Commercial Park"},
    {"store_id": "S004", "store_name": "Metro Express", "location": "Midtown Transit Terminal"},
]
df_stores = pd.DataFrame(stores_data)
df_stores.to_csv(os.path.join(DATA_DIR, "stores.csv"), index=False)
print(f"Created stores.csv with {len(df_stores)} stores")

# 2. Products
products_data = [
    # Electronics
    {"product_id": "P001", "product_name": "Laptop Pro", "category": "Electronics", "selling_price": 1200.00, "supplier": "TechCorp Global", "lead_time_days": 7},
    {"product_id": "P002", "product_name": "Wireless Mouse", "category": "Electronics", "selling_price": 25.00, "supplier": "Peripherals Direct", "lead_time_days": 4},
    {"product_id": "P003", "product_name": "Noise-Canceling Headphones", "category": "Electronics", "selling_price": 180.00, "supplier": "AudioTech Inc", "lead_time_days": 5},
    {"product_id": "P004", "product_name": "Smart 4K TV 55-inch", "category": "Electronics", "selling_price": 650.00, "supplier": "VisionElectronics", "lead_time_days": 10},
    {"product_id": "P005", "product_name": "USB-C Fast Charging Hub", "category": "Electronics", "selling_price": 35.00, "supplier": "Peripherals Direct", "lead_time_days": 3},
    
    # Grocery
    {"product_id": "P006", "product_name": "Artisan Sourdough", "category": "Grocery", "selling_price": 6.50, "supplier": "Local Bakeries Co", "lead_time_days": 2},
    {"product_id": "P007", "product_name": "Organic Whole Milk (1 Gallon)", "category": "Grocery", "selling_price": 4.80, "supplier": "Green Pastures Dairy", "lead_time_days": 2},
    {"product_id": "P008", "product_name": "Premium Arabica Coffee Beans (1kg)", "category": "Grocery", "selling_price": 18.50, "supplier": "Roastmasters Intl", "lead_time_days": 4},
    {"product_id": "P009", "product_name": "Greek Organic Yogurt (32oz)", "category": "Grocery", "selling_price": 5.20, "supplier": "Green Pastures Dairy", "lead_time_days": 2},
    {"product_id": "P010", "product_name": "Extra Virgin Olive Oil (1L)", "category": "Grocery", "selling_price": 14.00, "supplier": "Mediterranean Harvest", "lead_time_days": 6},

    # Home & Kitchen
    {"product_id": "P011", "product_name": "Ceramic Cookware Set (10-Piece)", "category": "Home", "selling_price": 150.00, "supplier": "HomeChef Essentials", "lead_time_days": 8},
    {"product_id": "P012", "product_name": "Ergonomic Desk Lamp", "category": "Home", "selling_price": 45.00, "supplier": "Lumina Designs", "lead_time_days": 5},
    {"product_id": "P013", "product_name": "Microfiber Bed Sheet Set (Queen)", "category": "Home", "selling_price": 38.00, "supplier": "CozyLiving Textiles", "lead_time_days": 6},
    {"product_id": "P014", "product_name": "Stainless Steel Water Bottle (32oz)", "category": "Home", "selling_price": 22.00, "supplier": "HydroSteel Brands", "lead_time_days": 4},

    # Fashion
    {"product_id": "P015", "product_name": "Vintage Leather Jacket", "category": "Fashion", "selling_price": 220.00, "supplier": "Heritage Apparel", "lead_time_days": 12},
    {"product_id": "P016", "product_name": "Slim Fit Stretch Denim", "category": "Fashion", "selling_price": 60.00, "supplier": "DenimWorks Co", "lead_time_days": 7},
    {"product_id": "P017", "product_name": "Classic Oxford Cotton Shirt", "category": "Fashion", "selling_price": 48.00, "supplier": "DenimWorks Co", "lead_time_days": 6},
    {"product_id": "P018", "product_name": "Athletic Breathable Running Shoes", "category": "Fashion", "selling_price": 95.00, "supplier": "Stride Athletic", "lead_time_days": 8},

    # Personal Care
    {"product_id": "P019", "product_name": "Electric Toothbrush Pro", "category": "Personal Care", "selling_price": 75.00, "supplier": "DentalCare Systems", "lead_time_days": 5},
    {"product_id": "P020", "product_name": "Botanical Nourishing Shampoo (500ml)", "category": "Personal Care", "selling_price": 16.00, "supplier": "Naturals Beauty", "lead_time_days": 3},
    {"product_id": "P021", "product_name": "Hydrating Peptide Face Cream", "category": "Personal Care", "selling_price": 32.00, "supplier": "Naturals Beauty", "lead_time_days": 4},
]
df_products = pd.DataFrame(products_data)
df_products.to_csv(os.path.join(DATA_DIR, "products.csv"), index=False)
print(f"Created products.csv with {len(df_products)} products")

# 3. Inventory & Daily Sales
# Target reference date: 2026-09-05 (90 days of history: 2026-06-08 to 2026-09-05)
end_date = datetime(2026, 9, 5)
start_date = end_date - timedelta(days=89)
date_range = [start_date + timedelta(days=i) for i in range(90)]

sales_rows = []
inventory_rows = []

# Configure unit costs as ~50-60% of selling price
unit_costs = {
    p["product_id"]: round(p["selling_price"] * random.uniform(0.50, 0.65), 2)
    for p in products_data
}

for prod in products_data:
    pid = prod["product_id"]
    pname = prod["product_name"]
    price = prod["selling_price"]
    cost = unit_costs[pid]
    
    for st in stores_data:
        sid = st["store_id"]
        
        # Determine baseline daily sales for this product-store combo
        if pid == "P001": # Laptop Pro
            # Sells 1-3 per day at flagship/mall, 0-2 at suburban/metro
            base_mean = 2.0 if sid in ["S001", "S002"] else 1.2
            curr_stock = 14 if sid == "S001" else (10 if sid == "S002" else 8)
            reorder = 15
            safety = 8
        elif pid == "P002": # Wireless Mouse
            if sid == "S001": # Downtown Flagship (Exact demo requirement: stock=12, ADS=5.0, days=2.4)
                base_mean = 5.0
                curr_stock = 12
                reorder = 25
                safety = 15
            else:
                base_mean = 3.5
                curr_stock = 35
                reorder = 20
                safety = 10
        elif pid == "P011": # Ceramic Cookware Set (Overstocked demo)
            base_mean = 0.8
            curr_stock = 140 if sid in ["S001", "S002"] else 95 # > 60 days cover, > 3x reorder
            reorder = 20
            safety = 10
        elif pid == "P015": # Vintage Leather Jacket (Slow moving demo)
            base_mean = 0.08 # very slow, less than 0.2/day
            curr_stock = 18
            reorder = 8
            safety = 4
        elif pid == "P019": # Electric Toothbrush (Sales spike demo at S001)
            base_mean = 1.5
            curr_stock = 16
            reorder = 20
            safety = 10
        elif pid == "P006": # Artisan Sourdough (Sales drop demo at S003)
            base_mean = 8.0
            curr_stock = 25
            reorder = 20
            safety = 10
        elif pid == "P004": # Smart TV
            base_mean = 0.6
            curr_stock = 8
            reorder = 6
            safety = 3
        elif pid == "P007": # Organic Milk
            base_mean = 12.0
            curr_stock = 28
            reorder = 30
            safety = 15
        elif pid == "P008": # Coffee Beans
            base_mean = 4.5
            curr_stock = 45
            reorder = 30
            safety = 15
        else: # Generic regular velocity
            base_mean = random.uniform(1.0, 4.0)
            curr_stock = int(base_mean * random.uniform(10, 20))
            reorder = int(base_mean * 7) + 5
            safety = int(base_mean * 3) + 2
            
        # Record Inventory
        inventory_rows.append({
            "product_id": pid,
            "store_id": sid,
            "current_stock": curr_stock,
            "reorder_level": reorder,
            "safety_stock": safety,
            "unit_cost": cost
        })
        
        # Generate 90 days of sales
        for day_idx, d in enumerate(date_range):
            is_recent_7d = (day_idx >= 83) # Last 7 days
            
            # Special case behaviors for demos
            if pid == "P002" and sid == "S001":
                # Exactly 5 units per day average in last 7 days!
                units = 5 if is_recent_7d else random.choice([4, 5, 4, 5, 3, 5, 4])
            elif pid == "P019" and sid == "S001" and is_recent_7d:
                # Sales spike: baseline was 1.5, recent is 6 to 8 units/day (spike ratio >= 2.5x)
                units = random.choice([6, 7, 7, 6, 8, 7, 8])
            elif pid == "P006" and sid == "S003" and is_recent_7d:
                # Sales drop: baseline was 8.0, recent is 1 or 2 units/day (drop ratio ~0.2x)
                units = random.choice([1, 2, 1, 1, 2, 1, 2])
            elif pid == "P015" and sid == "S002":
                # Slow moving: sells 1 unit every 15-20 days, mostly 0
                units = 1 if (day_idx % 18 == 0) else 0
            else:
                # Poisson-like variation around base_mean
                # Add slight weekend boost for days 5 & 6
                weekend_factor = 1.25 if d.weekday() in [5, 6] else 1.0
                daily_rate = base_mean * weekend_factor
                units = max(0, int(np.random.poisson(daily_rate)))
            
            # Add to sales records if units > 0
            # Some slow products may have days with 0 units, which we can either record or omit.
            # Retail POS records transactions, but daily sales table can include 0 or just days with sales.
            # Let's record all days or positive days. Storing days with sales or 0 gives total visibility.
            revenue = round(units * price, 2)
            sales_rows.append({
                "date": d.strftime("%Y-%m-%d"),
                "product_id": pid,
                "store_id": sid,
                "units_sold": units,
                "unit_price": price,
                "total_revenue": revenue
            })

df_inventory = pd.DataFrame(inventory_rows)
df_inventory.to_csv(os.path.join(DATA_DIR, "inventory.csv"), index=False)
print(f"Created inventory.csv with {len(df_inventory)} records")

df_sales = pd.DataFrame(sales_rows)
df_sales.to_csv(os.path.join(DATA_DIR, "sales.csv"), index=False)
print(f"Created sales.csv with {len(df_sales)} daily transaction records")
print(f"Date range: {df_sales['date'].min()} to {df_sales['date'].max()}")
print(f"Total revenue generated: ${df_sales['total_revenue'].sum():,.2f}")
print("Data generation complete!")
