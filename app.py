import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

st.set_page_config(
    page_title="Restaurant Commercial Intelligence",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATA LOADING
# ============================================================
@st.cache_data
def load_data():
    if os.path.exists('data/restaurant_transactions.csv'):
        df_txn = pd.read_csv('data/restaurant_transactions.csv')
        df_labour = pd.read_csv('data/restaurant_labour.csv')
        df_campaigns = pd.read_csv('data/restaurant_campaigns.csv')
        competitor_prices = pd.read_csv('data/competitor_prices.csv')
    else:
        st.error("Data not found. Run: python generate_data.py")
        return None, None, None, None

    df_txn['Revenue'] = df_txn['Quantity'] * df_txn['UnitPrice']
    df_txn['Cost'] = df_txn['Quantity'] * df_txn['UnitCost']
    df_txn['GrossProfit'] = df_txn['Revenue'] - df_txn['Cost']

    return df_txn, df_labour, df_campaigns, competitor_prices


data = load_data()
if data[0] is None:
    st.stop()

df_txn, df_labour, df_campaigns, competitor_prices = data

# ============================================================
# SIDEBAR FILTERS
# ============================================================
st.sidebar.title("🍜 Filters")

loc_filter = st.sidebar.multiselect(
    "Location",
    options=sorted(df_txn['Location'].unique()),
    default=sorted(df_txn['Location'].unique())
)

order_type_filter = st.sidebar.multiselect(
    "Order type",
    options=sorted(df_txn['OrderType'].unique()),
    default=sorted(df_txn['OrderType'].unique())
)

category_filter = st.sidebar.multiselect(
    "Menu category",
    options=sorted(df_txn['Category'].unique()),
    default=sorted(df_txn['Category'].unique())
)

date_range = st.sidebar.date_input(
    "Date range",
    value=(pd.to_datetime(df_txn['Date']).min().date(), pd.to_datetime(df_txn['Date']).max().date()),
    min_value=pd.to_datetime(df_txn['Date']).min().date(),
    max_value=pd.to_datetime(df_txn['Date']).max().date()
)

filtered_txn = df_txn[
    (df_txn['Location'].isin(loc_filter)) &
    (df_txn['OrderType'].isin(order_type_filter)) &
    (df_txn['Category'].isin(category_filter)) &
    (pd.to_datetime(df_txn['Date']).dt.date >= date_range[0]) &
    (pd.to_datetime(df_txn['Date']).dt.date <= date_range[1])
]

# ============================================================
# HEADER
# ============================================================
st.title("Restaurant Commercial Intelligence & Menu Engineering")
st.markdown("Menu profitability, location performance, marketing ROI, and competitor benchmarking.")

# ============================================================
# KPI ROW
# ============================================================
col1, col2, col3, col4, col5 = st.columns(5)

total_revenue = filtered_txn['Revenue'].sum()
total_profit = filtered_txn['GrossProfit'].sum()
total_orders = filtered_txn['OrderID'].nunique()
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
margin_pct = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

col1.metric("Total Revenue", f"£{total_revenue:,.0f}")
col2.metric("Gross Profit", f"£{total_profit:,.0f}")
col3.metric("Total Orders", f"{total_orders:,}")
col4.metric("Avg Order Value", f"£{avg_order_value:.2f}")
col5.metric("Gross Margin", f"{margin_pct:.1f}%")

st.divider()

# ============================================================
# CHARTS ROW 1
# ============================================================
left, right = st.columns(2)

with left:
    st.subheader("Menu Engineering Matrix")
    menu_perf = filtered_txn.groupby('MenuItem').agg({
        'Quantity': 'sum',
        'Revenue': 'sum',
        'GrossProfit': 'sum',
    }).reset_index()
    menu_perf['MenuMixPct'] = (menu_perf['Quantity'] / menu_perf['Quantity'].sum() * 100).round(2)
    menu_perf['AvgMarginPct'] = (menu_perf['GrossProfit'] / menu_perf['Revenue'] * 100).round(1)

    pop_med = menu_perf['MenuMixPct'].median()
    mar_med = menu_perf['AvgMarginPct'].median()

    def quad(row):
        if row['MenuMixPct'] >= pop_med and row['AvgMarginPct'] >= mar_med: return 'Star'
        elif row['MenuMixPct'] >= pop_med and row['AvgMarginPct'] < mar_med: return 'Plough Horse'
        elif row['MenuMixPct'] < pop_med and row['AvgMarginPct'] >= mar_med: return 'Puzzle'
        else: return 'Dog'

    menu_perf['Quadrant'] = menu_perf.apply(quad, axis=1)

    fig, ax = plt.subplots(figsize=(6, 4))
    quad_colors = {'Star': '#2ecc71', 'Plough Horse': '#f39c12', 'Puzzle': '#3498db', 'Dog': '#e74c3c'}
    for q in menu_perf['Quadrant'].unique():
        subset = menu_perf[menu_perf['Quadrant'] == q]
        ax.scatter(subset['MenuMixPct'], subset['AvgMarginPct'], c=quad_colors[q], label=q, s=100, alpha=0.8, edgecolors='white', linewidth=0.5)
    ax.axvline(pop_med, color='gray', linestyle='--', alpha=0.5)
    ax.axhline(mar_med, color='gray', linestyle='--', alpha=0.5)
    ax.set_xlabel('Menu Mix (%)')
    ax.set_ylabel('Margin (%)')
    ax.legend(loc='lower left', fontsize=8)
    ax.grid(alpha=0.3)
    st.pyplot(fig)

with right:
    st.subheader("Revenue by Location (Monthly)")
    daily = filtered_txn.groupby(['Date', 'Location'])['Revenue'].sum().reset_index()
    daily['Month'] = pd.to_datetime(daily['Date']).dt.to_period('M')
    monthly = daily.groupby(['Month', 'Location'])['Revenue'].sum().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(6, 4))
    monthly.plot(ax=ax, marker='o', linewidth=2)
    ax.set_ylabel('Revenue (£)')
    ax.legend(title='Location', fontsize=8)
    ax.grid(alpha=0.3)
    st.pyplot(fig)

# ============================================================
# CHARTS ROW 2
# ============================================================
left2, right2 = st.columns(2)

with left2:
    st.subheader("Demand by Hour & Order Type")
    hourly = filtered_txn.groupby(['Hour', 'OrderType'])['OrderID'].nunique().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(6, 4))
    hourly.plot(kind='bar', stacked=True, ax=ax, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.85)
    ax.set_xlabel('Hour')
    ax.set_ylabel('Orders')
    ax.legend(title='Order Type', fontsize=8)
    ax.tick_params(axis='x', rotation=0)
    ax.grid(axis='y', alpha=0.3)
    st.pyplot(fig)

with right2:
    st.subheader("Marketing Campaign ROAS")
    camp_results = []
    for _, camp in df_campaigns.iterrows():
        start = pd.to_datetime(camp['Start']).date()
        end = pd.to_datetime(camp['End']).date()
        camp_txn = filtered_txn[(pd.to_datetime(filtered_txn['Date']).dt.date >= start) & (pd.to_datetime(filtered_txn['Date']).dt.date <= end)]
        if camp['Target'] == 'Takeaway':
            camp_txn = camp_txn[camp_txn['OrderType'] == 'Takeaway']
        elif camp['Target'] == 'Dine-in':
            camp_txn = camp_txn[camp_txn['OrderType'] == 'Dine-in']
        revenue = camp_txn['Revenue'].sum()
        roas = round(revenue / camp['Spend'], 2) if camp['Spend'] > 0 else 0
        camp_results.append({'Campaign': camp['Campaign'], 'ROAS': roas, 'Spend': camp['Spend']})

    camp_df = pd.DataFrame(camp_results).sort_values('ROAS', ascending=True)
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ['#2ecc71' if r > 15 else '#f39c12' if r > 10 else '#e74c3c' for r in camp_df['ROAS']]
    ax.barh(camp_df['Campaign'], camp_df['ROAS'], color=colors, alpha=0.85)
    ax.set_xlabel('ROAS')
    ax.axvline(x=10, color='gray', linestyle='--', alpha=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.3)
    st.pyplot(fig)

st.divider()

# ============================================================
# COMPETITOR BENCHMARKING
# ============================================================
st.subheader("Competitor Price Benchmarking")

comp_display = competitor_prices[['MenuItem', 'OurPrice', 'Golden Dragon', 'China Garden', 'Wok This Way', 'CompetitorAvg', 'PriceDiffPct']].copy()
comp_display.columns = ['Menu Item', 'Our Price', 'Golden Dragon', 'China Garden', 'Wok This Way', 'Competitor Avg', 'Price Diff %']
st.dataframe(comp_display, use_container_width=True, hide_index=True)

st.divider()

# ============================================================
# LABOUR COST ANALYSIS
# ============================================================
st.subheader("Labour Cost Analysis")

filtered_labour = df_labour[
    (df_labour['Location'].isin(loc_filter)) &
    (pd.to_datetime(df_labour['Date']).dt.date >= date_range[0]) &
    (pd.to_datetime(df_labour['Date']).dt.date <= date_range[1])
]

labour_summary = filtered_labour.groupby(['Location', 'Role']).agg({
    'Hours': 'sum',
    'LabourCost': 'sum'
}).reset_index()

fig, ax = plt.subplots(figsize=(10, 4))
labour_pivot = labour_summary.pivot(index='Role', columns='Location', values='LabourCost').fillna(0)
labour_pivot.plot(kind='bar', ax=ax, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.85)
ax.set_ylabel('Labour Cost (£)')
ax.set_title('Labour Cost by Role & Location')
ax.legend(title='Location')
ax.tick_params(axis='x', rotation=30)
ax.grid(axis='y', alpha=0.3)
st.pyplot(fig)

st.divider()

# ============================================================
# ACTIONABLE INSIGHTS
# ============================================================
st.subheader("Strategic Recommendations")

insights = {
    'Menu Engineering': [
        'Stars: Promote Kung Pao Chicken and Crispy Duck as signature dishes',
        'Plough Horses: Increase price of Sweet & Sour Pork or reduce portion cost',
        'Puzzles: Feature Salt & Pepper Squid in specials to drive trial',
        'Dogs: Consider removing or rebranding low-performing items'
    ],
    'Location Strategy': [
        'Fareham: Flagship location — maintain standards, test new menu items here',
        'Bexley: Underperforming — reduce labour hours on Mon-Wed, focus on weekend promotions',
        'Leamington Spa: Losing money — evaluate lease renewal or convert to delivery-only kitchen'
    ],
    'Marketing Efficiency': [
        'Double down on Spring Festival and Black Friday campaigns (ROAS > 40x)',
        'Reduce Google Ads spend on New Year Healthy Start (ROAS < 10x)',
        'Email/SMS has highest ROI — build customer database for direct marketing'
    ],
    'Operational Efficiency': [
        'Saturday peak: add prep staff 11am-2pm to reduce ticket times',
        'Delivery demand spikes at 7pm — ensure 2 drivers scheduled Fri-Sat',
        'Drinks have 74% margin — train staff on upselling wine and beer'
    ]
}

for category, items in insights.items():
    with st.expander(f"**{category}**"):
        for item in items:
            st.markdown(f"- {item}")

st.caption("Built with Streamlit — Data is synthetic for demonstration purposes")
