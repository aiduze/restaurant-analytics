"""
restaurant_analysis.py
======================
End-to-end restaurant commercial intelligence pipeline.

Run after generate_data.py:
    python restaurant_analysis.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load data
df_txn = pd.read_csv('data/restaurant_transactions.csv')
df_labour = pd.read_csv('data/restaurant_labour.csv')
df_campaigns = pd.read_csv('data/restaurant_campaigns.csv')
competitor_prices = pd.read_csv('data/competitor_prices.csv')

# Feature engineering
df_txn['Revenue'] = df_txn['Quantity'] * df_txn['UnitPrice']
df_txn['Cost'] = df_txn['Quantity'] * df_txn['UnitCost']
df_txn['GrossProfit'] = df_txn['Revenue'] - df_txn['Cost']
df_txn['MarginPct'] = (df_txn['GrossProfit'] / df_txn['Revenue'] * 100).round(1)

# Menu engineering
menu_perf = df_txn.groupby('MenuItem').agg({
    'Quantity': 'sum',
    'Revenue': 'sum',
    'Cost': 'sum',
    'GrossProfit': 'sum',
}).reset_index()
menu_perf['MenuMixPct'] = (menu_perf['Quantity'] / menu_perf['Quantity'].sum() * 100).round(2)
menu_perf['AvgMarginPct'] = (menu_perf['GrossProfit'] / menu_perf['Revenue'] * 100).round(1)
menu_perf['ContributionMargin'] = (menu_perf['GrossProfit'] / menu_perf['Quantity']).round(2)

popularity_median = menu_perf['MenuMixPct'].median()
margin_median = menu_perf['AvgMarginPct'].median()

def quadrant(row):
    if row['MenuMixPct'] >= popularity_median and row['AvgMarginPct'] >= margin_median:
        return 'Star'
    elif row['MenuMixPct'] >= popularity_median and row['AvgMarginPct'] < margin_median:
        return 'Plough Horse'
    elif row['MenuMixPct'] < popularity_median and row['AvgMarginPct'] >= margin_median:
        return 'Puzzle'
    else:
        return 'Dog'

menu_perf['Quadrant'] = menu_perf.apply(quadrant, axis=1)

# Location performance
daily_perf = df_txn.groupby(['Date', 'Location']).agg({
    'Revenue': 'sum',
    'GrossProfit': 'sum',
    'OrderID': 'nunique',
}).reset_index()
daily_perf.columns = ['Date', 'Location', 'Revenue', 'GrossProfit', 'Orders']
daily_perf['AvgOrderValue'] = (daily_perf['Revenue'] / daily_perf['Orders']).round(2)

daily_labour = df_labour.groupby(['Date', 'Location'])['LabourCost'].sum().reset_index()
daily_perf = daily_perf.merge(daily_labour, on=['Date', 'Location'], how='left')
daily_perf['LabourCost'] = daily_perf['LabourCost'].fillna(0)
daily_perf['NetProfit'] = (daily_perf['GrossProfit'] - daily_perf['LabourCost']).round(2)
daily_perf['LabourCostPct'] = (daily_perf['LabourCost'] / daily_perf['Revenue'] * 100).round(1)
daily_perf['NetMarginPct'] = (daily_perf['NetProfit'] / daily_perf['Revenue'] * 100).round(1)

# Campaign performance
campaign_results = []
for _, camp in df_campaigns.iterrows():
    start = pd.to_datetime(camp['Start']).date()
    end = pd.to_datetime(camp['End']).date()
    camp_txn = df_txn[(df_txn['Date'] >= str(start)) & (df_txn['Date'] <= str(end))]

    if camp['Target'] == 'Takeaway':
        camp_txn = camp_txn[camp_txn['OrderType'] == 'Takeaway']
    elif camp['Target'] == 'Dine-in':
        camp_txn = camp_txn[camp_txn['OrderType'] == 'Dine-in']

    revenue = camp_txn['Revenue'].sum()
    orders = camp_txn['OrderID'].nunique()
    profit = camp_txn['GrossProfit'].sum()

    campaign_results.append({
        'Campaign': camp['Campaign'],
        'Channel': camp['Channel'],
        'Spend': camp['Spend'],
        'Revenue': revenue,
        'Orders': orders,
        'Profit': profit,
        'ROAS': round(revenue / camp['Spend'], 2),
        'ROI': round((revenue - camp['Spend']) / camp['Spend'] * 100, 1),
        'Target': camp['Target'],
    })

campaign_perf = pd.DataFrame(campaign_results)

# Competitor benchmarking
competitor_prices['CompetitorAvg'] = competitor_prices[['Golden Dragon', 'China Garden', 'Wok This Way']].mean(axis=1).round(2)
competitor_prices['PriceDiffPct'] = ((competitor_prices['OurPrice'] - competitor_prices['CompetitorAvg']) / competitor_prices['CompetitorAvg'] * 100).round(1)

# Export charts
os.makedirs('outputs', exist_ok=True)

fig, axes = plt.subplots(3, 3, figsize=(18, 15))
fig.suptitle('Restaurant Commercial Intelligence & Menu Engineering', fontsize=16, fontweight='bold', y=1.02)

ax = axes[0, 0]
quad_colors = {'Star': '#2ecc71', 'Plough Horse': '#f39c12', 'Puzzle': '#3498db', 'Dog': '#e74c3c'}
for quad in menu_perf['Quadrant'].unique():
    subset = menu_perf[menu_perf['Quadrant'] == quad]
    ax.scatter(subset['MenuMixPct'], subset['AvgMarginPct'], c=quad_colors[quad], label=quad, s=120, alpha=0.8, edgecolors='white', linewidth=0.5)
    for _, row in subset.iterrows():
        ax.annotate(row['MenuItem'][:15], (row['MenuMixPct'], row['AvgMarginPct']), fontsize=7, ha='center', va='bottom')
ax.axvline(popularity_median, color='gray', linestyle='--', alpha=0.5)
ax.axhline(margin_median, color='gray', linestyle='--', alpha=0.5)
ax.set_xlabel('Menu Mix (%)')
ax.set_ylabel('Margin (%)')
ax.set_title('Menu Engineering Matrix', fontweight='bold')
ax.legend(loc='lower left', fontsize=8)
ax.grid(alpha=0.3)

ax = axes[0, 1]
daily_perf['Month'] = pd.to_datetime(daily_perf['Date']).dt.to_period('M')
monthly_rev = daily_perf.groupby(['Month', 'Location'])['Revenue'].sum().unstack()
monthly_rev.plot(ax=ax, marker='o', linewidth=2)
ax.set_title('Monthly Revenue by Location', fontweight='bold')
ax.set_ylabel('Revenue (£)')
ax.legend(title='Location')
ax.grid(alpha=0.3)

ax = axes[0, 2]
loc_margin = daily_perf.groupby('Location')['NetMarginPct'].mean()
colors_loc = ['#2ecc71' if m > 0 else '#e74c3c' for m in loc_margin.values]
bars = ax.bar(loc_margin.index, loc_margin.values, color=colors_loc, alpha=0.85, edgecolor='white', linewidth=0.5)
ax.set_ylabel('Net Margin (%)')
ax.set_title('Location Profitability', fontweight='bold')
ax.axhline(y=0, color='black', linewidth=0.8)
for bar, val in zip(bars, loc_margin.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1 if val > 0 else bar.get_height() - 3,
            f"{val:.1f}%", ha='center', va='bottom' if val > 0 else 'top', fontweight='bold', fontsize=10)
ax.tick_params(axis='x', rotation=15)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.3)

ax = axes[1, 0]
hourly_orders = df_txn.groupby(['Hour', 'OrderType'])['OrderID'].nunique().unstack(fill_value=0)
hourly_orders.plot(kind='bar', stacked=True, ax=ax, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.85)
ax.set_xlabel('Hour of Day')
ax.set_ylabel('Orders')
ax.set_title('Demand by Hour & Order Type', fontweight='bold')
ax.legend(title='Order Type')
ax.tick_params(axis='x', rotation=0)
ax.grid(axis='y', alpha=0.3)

ax = axes[1, 1]
camp_sorted = campaign_perf.sort_values('ROAS', ascending=True)
colors_camp = ['#2ecc71' if r > 15 else '#f39c12' if r > 10 else '#e74c3c' for r in camp_sorted['ROAS']]
bars = ax.barh(camp_sorted['Campaign'], camp_sorted['ROAS'], color=colors_camp, alpha=0.85)
ax.set_xlabel('ROAS (Revenue / Spend)')
ax.set_title('Marketing Campaign ROAS', fontweight='bold')
ax.axvline(x=10, color='gray', linestyle='--', alpha=0.5)
for bar, val in zip(bars, camp_sorted['ROAS']):
    ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, f"{val:.1f}x", ha='left', va='center', fontsize=8, fontweight='bold')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='x', alpha=0.3)

ax = axes[1, 2]
comp_sample = competitor_prices.head(8).copy()
x = np.arange(len(comp_sample))
width = 0.2
ax.bar(x - width*1.5, comp_sample['OurPrice'], width, label='Kiang Nan', color='#e74c3c', alpha=0.85)
ax.bar(x - width*0.5, comp_sample['Golden Dragon'], width, label='Golden Dragon', color='#3498db', alpha=0.7)
ax.bar(x + width*0.5, comp_sample['China Garden'], width, label='China Garden', color='#2ecc71', alpha=0.7)
ax.bar(x + width*1.5, comp_sample['Wok This Way'], width, label='Wok This Way', color='#f39c12', alpha=0.7)
ax.set_xticks(x)
ax.set_xticklabels([i[:12] for i in comp_sample['MenuItem']], rotation=45, ha='right', fontsize=8)
ax.set_ylabel('Price (£)')
ax.set_title('Competitor Price Benchmarking', fontweight='bold')
ax.legend(fontsize=8)
ax.grid(axis='y', alpha=0.3)

ax = axes[2, 0]
loc_costs = daily_perf.groupby('Location').agg({'Revenue': 'sum', 'LabourCost': 'sum'}).reset_index()
x = np.arange(len(loc_costs))
width = 0.35
ax.bar(x - width/2, loc_costs['Revenue']/1000, width, label='Revenue', color='#2ecc71', alpha=0.85)
ax.bar(x + width/2, loc_costs['LabourCost']/1000, width, label='Labour Cost', color='#e74c3c', alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(loc_costs['Location'])
ax.set_ylabel('Amount (£ Thousands)')
ax.set_title('Revenue vs Labour Cost', fontweight='bold')
ax.legend()
ax.grid(axis='y', alpha=0.3)

ax = axes[2, 1]
dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dow_perf = df_txn.groupby('DayOfWeek')['Revenue'].sum().reindex(dow_order)
bars = ax.bar(dow_perf.index, dow_perf.values/1000, color='#9b59b6', alpha=0.85, edgecolor='white', linewidth=0.5)
ax.set_ylabel('Revenue (£ Thousands)')
ax.set_title('Revenue by Day of Week', fontweight='bold')
ax.tick_params(axis='x', rotation=30)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.3)

ax = axes[2, 2]
cat_perf = df_txn.groupby('Category').agg({'Revenue': 'sum', 'GrossProfit': 'sum'}).reset_index()
cat_perf['MarginPct'] = (cat_perf['GrossProfit'] / cat_perf['Revenue'] * 100).round(1)
bars = ax.bar(cat_perf['Category'], cat_perf['Revenue']/1000, color='#1abc9c', alpha=0.85, edgecolor='white', linewidth=0.5)
ax2 = ax.twinx()
ax2.plot(cat_perf['Category'], cat_perf['MarginPct'], 'o-', color='#e74c3c', linewidth=2, markersize=8, label='Margin %')
ax.set_ylabel('Revenue (£ Thousands)', color='#1abc9c')
ax2.set_ylabel('Margin (%)', color='#e74c3c')
ax.set_title('Category Revenue & Margin', fontweight='bold')
ax.tick_params(axis='x', rotation=30)
ax2.legend(loc='upper right')
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/kiangnan_01_commercial_intelligence.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: outputs/kiangnan_01_commercial_intelligence.png")

print("\n=== ANALYSIS COMPLETE ===")
print(f"Menu items analyzed: {len(menu_perf)}")
print(f"Locations: {daily_perf['Location'].nunique()}")
print(f"Campaigns evaluated: {len(campaign_perf)}")
