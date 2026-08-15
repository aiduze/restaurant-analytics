"""
generate_data.py
================
Generates synthetic restaurant transaction, labour, and marketing data.
Run first: python generate_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(2026)

N_DAYS = 365
START_DATE = datetime(2025, 6, 1)

locations = ['Fareham', 'Bexley', 'Leamington Spa']
location_weights = [0.45, 0.35, 0.20]

menu_items = {
    'Kung Pao Chicken': {'category': 'Mains', 'cost': 4.50, 'price': 12.95, 'prep_time': 12},
    'Sweet & Sour Pork': {'category': 'Mains', 'cost': 4.20, 'price': 11.95, 'prep_time': 10},
    'Beef Chow Mein': {'category': 'Noodles', 'cost': 3.80, 'price': 10.95, 'prep_time': 8},
    'Prawn Crackers': {'category': 'Starters', 'cost': 0.80, 'price': 3.50, 'prep_time': 2},
    'Spring Rolls (4)': {'category': 'Starters', 'cost': 1.50, 'price': 5.95, 'prep_time': 5},
    'Crispy Duck (Half)': {'category': 'Mains', 'cost': 6.50, 'price': 18.95, 'prep_time': 15},
    'Vegetable Fried Rice': {'category': 'Sides', 'cost': 1.20, 'price': 4.50, 'prep_time': 5},
    'Egg Fried Rice': {'category': 'Sides', 'cost': 1.00, 'price': 3.95, 'prep_time': 4},
    'Special Fried Rice': {'category': 'Mains', 'cost': 3.50, 'price': 11.50, 'prep_time': 10},
    'Crispy Chilli Beef': {'category': 'Mains', 'cost': 4.80, 'price': 13.95, 'prep_time': 12},
    'Salt & Pepper Squid': {'category': 'Starters', 'cost': 3.20, 'price': 8.95, 'prep_time': 8},
    'Sesame Prawn Toast': {'category': 'Starters', 'cost': 2.00, 'price': 6.50, 'prep_time': 6},
    'Tofu & Vegetable Stir-fry': {'category': 'Mains', 'cost': 2.80, 'price': 9.95, 'prep_time': 8},
    'Soft Drinks': {'category': 'Drinks', 'cost': 0.40, 'price': 2.95, 'prep_time': 1},
    'House Wine (Glass)': {'category': 'Drinks', 'cost': 2.50, 'price': 6.95, 'prep_time': 1},
    'Beer (Bottle)': {'category': 'Drinks', 'cost': 1.80, 'price': 5.50, 'prep_time': 1},
}

# Transactions
transactions = []
order_id = 10000

for day_offset in range(N_DAYS):
    date = START_DATE + timedelta(days=day_offset)
    month_factor = 1.4 if date.month == 12 else 1.2 if date.month == 11 else 0.75 if date.month in [1, 2] else 1.1 if date.month in [7, 8] else 1.0
    dow_factor = {0: 0.6, 1: 0.65, 2: 0.75, 3: 0.85, 4: 1.1, 5: 1.4, 6: 1.2}[date.weekday()]

    for loc in locations:
        loc_idx = locations.index(loc)
        base_orders = int(np.random.poisson(80 * location_weights[loc_idx] * month_factor * dow_factor))

        for _ in range(base_orders):
            order_id += 1
            order_type = np.random.choice(['Dine-in', 'Takeaway', 'Delivery'], p=[0.50, 0.30, 0.20])
            n_items = np.random.choice([1, 2, 3, 4, 5, 6], p=[0.10, 0.20, 0.25, 0.20, 0.15, 0.10])

            if np.random.random() < 0.35:
                hour = np.random.choice([12, 13, 14], p=[0.4, 0.4, 0.2])
            else:
                hour = np.random.choice([17, 18, 19, 20, 21], p=[0.1, 0.25, 0.35, 0.20, 0.10])

            party_size = np.random.choice([1, 2, 3, 4, 5, 6], p=[0.15, 0.30, 0.25, 0.15, 0.10, 0.05])
            if order_type != 'Dine-in':
                party_size = 1

            items_ordered = np.random.choice(list(menu_items.keys()), size=n_items, replace=True)

            for item in items_ordered:
                info = menu_items[item]
                qty = np.random.choice([1, 2], p=[0.85, 0.15])
                transactions.append({
                    'OrderID': f'ORD_{order_id}',
                    'Date': date.date(),
                    'Location': loc,
                    'OrderType': order_type,
                    'Hour': hour,
                    'DayOfWeek': date.strftime('%A'),
                    'Month': date.strftime('%B'),
                    'PartySize': party_size,
                    'MenuItem': item,
                    'Category': info['category'],
                    'Quantity': qty,
                    'UnitPrice': info['price'],
                    'UnitCost': info['cost'],
                    'PrepTime': info['prep_time'],
                })

df_txn = pd.DataFrame(transactions)
df_txn['Revenue'] = df_txn['Quantity'] * df_txn['UnitPrice']
df_txn['Cost'] = df_txn['Quantity'] * df_txn['UnitCost']
df_txn['GrossProfit'] = df_txn['Revenue'] - df_txn['Cost']

# Labour data
roles = {'Chef': 14.50, 'Kitchen Porter': 11.50, 'Waiter': 12.00, 'Bar Staff': 12.50, 'Manager': 18.00, 'Delivery Driver': 11.00}
labour_records = []

for day_offset in range(N_DAYS):
    date = START_DATE + timedelta(days=day_offset)
    dow = date.weekday()

    for loc in locations:
        base_hours = {0: 40, 1: 40, 2: 45, 3: 50, 4: 60, 5: 80, 6: 65}[dow]
        loc_multiplier = {'Fareham': 1.0, 'Bexley': 0.85, 'Leamington Spa': 0.60}[loc]
        total_hours = int(base_hours * loc_multiplier)

        for role, wage in roles.items():
            if role == 'Manager':
                hours = 8 if dow in [4, 5, 6] else 6
            elif role == 'Delivery Driver':
                hours = int(total_hours * 0.15) if dow in [4, 5, 6] else int(total_hours * 0.10)
            else:
                pct = {'Chef': 0.25, 'Kitchen Porter': 0.20, 'Waiter': 0.25, 'Bar Staff': 0.15}[role]
                hours = int(total_hours * pct)

            labour_records.append({
                'Date': date.date(),
                'Location': loc,
                'Role': role,
                'Hours': hours,
                'HourlyRate': wage,
                'LabourCost': round(hours * wage, 2),
            })

df_labour = pd.DataFrame(labour_records)

# Competitor prices
competitor_prices = pd.DataFrame({
    'MenuItem': list(menu_items.keys()),
    'OurPrice': [menu_items[k]['price'] for k in menu_items.keys()],
    'Golden Dragon': [round(p + np.random.uniform(-2, 3), 2) for p in [menu_items[k]['price'] for k in menu_items.keys()]],
    'China Garden': [round(p + np.random.uniform(-1.5, 2.5), 2) for p in [menu_items[k]['price'] for k in menu_items.keys()]],
    'Wok This Way': [round(p + np.random.uniform(-1, 4), 2) for p in [menu_items[k]['price'] for k in menu_items.keys()]],
})

# Campaign data
campaigns = [
    {'Campaign': 'Summer Feast Promo', 'Channel': 'Facebook/Instagram', 'Spend': 2500, 'Start': '2025-07-01', 'End': '2025-08-15', 'Target': 'Takeaway'},
    {'Campaign': 'Back to School Lunch', 'Channel': 'Google Ads', 'Spend': 1800, 'Start': '2025-09-01', 'End': '2025-09-30', 'Target': 'Dine-in'},
    {'Campaign': 'Halloween Special', 'Channel': 'Facebook/Instagram', 'Spend': 1500, 'Start': '2025-10-20', 'End': '2025-11-05', 'Target': 'Dine-in'},
    {'Campaign': 'Black Friday Deal', 'Channel': 'Email/SMS', 'Spend': 800, 'Start': '2025-11-20', 'End': '2025-11-30', 'Target': 'All'},
    {'Campaign': 'Christmas Feast', 'Channel': 'Facebook/Instagram', 'Spend': 3500, 'Start': '2025-12-01', 'End': '2025-12-31', 'Target': 'Dine-in'},
    {'Campaign': 'New Year Healthy Start', 'Channel': 'Google Ads', 'Spend': 2000, 'Start': '2026-01-05', 'End': '2026-02-10', 'Target': 'Takeaway'},
    {'Campaign': 'Valentine Dinner', 'Channel': 'Facebook/Instagram', 'Spend': 1200, 'Start': '2026-02-01', 'End': '2026-02-14', 'Target': 'Dine-in'},
    {'Campaign': 'Spring Festival', 'Channel': 'Email/SMS', 'Spend': 1000, 'Start': '2026-03-15', 'End': '2026-04-15', 'Target': 'All'},
    {'Campaign': 'Easter Family Deal', 'Channel': 'Google Ads', 'Spend': 1600, 'Start': '2026-04-01', 'End': '2026-04-20', 'Target': 'Dine-in'},
    {'Campaign': 'May Bank Holiday', 'Channel': 'Facebook/Instagram', 'Spend': 1400, 'Start': '2026-05-01', 'End': '2026-05-10', 'Target': 'All'},
]
df_campaigns = pd.DataFrame(campaigns)

os.makedirs('data', exist_ok=True)
df_txn.to_csv('data/restaurant_transactions.csv', index=False)
df_labour.to_csv('data/restaurant_labour.csv', index=False)
df_campaigns.to_csv('data/restaurant_campaigns.csv', index=False)
competitor_prices.to_csv('data/competitor_prices.csv', index=False)

print(f"Transactions: {len(df_txn):,} line items")
print(f"Labour records: {len(df_labour):,}")
print(f"Campaigns: {len(df_campaigns)}")
print(f"Competitor prices: {len(competitor_prices)} items")
print("All files saved to data/")
