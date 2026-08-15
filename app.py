import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(
    page_title="Restaurant Commercial Intelligence",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATA GENERATION (runs on Streamlit Cloud if data missing)
# ============================================================
@st.cache_data
def generate_and_load_data():
    np.random.seed(2026)
    n = 8000
    states = ['Lagos', 'Kano', 'Rivers', 'Kaduna', 'Oyo', 'FCT Abuja', 'Delta', 'Ogun', 'Anambra', 'Enugu']

    # This is a simplified fallback - the full generate_data.py should be run locally
    # For Streamlit Cloud, we generate minimal data inline

    N_DAYS = 365
    START_DATE = pd.Timestamp('2025-06-01')
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

    # Generate transactions
    transactions = []
    order_id = 10000

    for day_offset in range(N_DAYS):
        date = START_DATE + pd.Timedelta(days=day_offset)
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

    # Generate labour data
    roles = {'Chef': 14.50, 'Kitchen Porter': 11.50, 'Waiter': 12.00, 'Bar Staff': 12.50, 'Manager': 18.00, 'Delivery Driver': 11.00}
    labour_records = []

    for day_offset in range(N_DAYS):
        date = START_DATE + pd.Timedelta(days=day_offset)
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

    # Competitor prices
    competitor_prices = pd.DataFrame({
        'MenuItem': list(menu_items.keys()),
        'OurPrice': [menu_items[k]['price'] for k in menu_items.keys()],
        'Golden Dragon': [round(p + np.random.uniform(-2, 3), 2) for p in [menu_items[k]['price'] for k in menu_items.keys()]],
        'China Garden': [round(p + np.random.uniform(-1.5, 2.5), 2) for p in [menu_items[k]['price'] for k in menu_items.keys()]],
        'Wok This Way': [round(p + np.random.uniform(-1, 4), 2) for p in [menu_items[k]['price'] for k in menu_items.keys()]],
    })
    competitor_prices['CompetitorAvg'] = competitor_prices[['Golden Dragon', 'China Garden', 'Wok This Way']].mean(axis=1).round(2)
    competitor_prices['PriceDiffPct'] = ((competitor_prices['OurPrice'] - competitor_prices['CompetitorAvg']) / competitor_prices['CompetitorAvg'] * 100).round(1)

    return df_txn, df_labour, df_campaigns, competitor_prices


# Try to load from files first, fallback to generation
try:
    df_txn = pd.read_csv('data/restaurant_transactions.csv')
    df_labour = pd.read_csv('data/restaurant_labour.csv')
    df_campaigns = pd.read_csv('data/restaurant_campaigns.csv')
    competitor_prices = pd.read_csv('data/competitor_prices.csv')
    df_txn['Revenue'] = df_txn['Quantity'] * df_txn['UnitPrice']
    df_txn['Cost'] = df_txn['Quantity'] * df_txn['UnitCost']
    df_txn['GrossProfit'] = df_txn['Revenue'] - df_txn['Cost']
except FileNotFoundError:
    df_txn, df_labour, df_campaigns, competitor_prices = generate_and_load_data()

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

    for q in ['Star', 'Plough Horse', 'Puzzle', 'Dog']:
        subset = menu_perf[menu_perf['Quadrant'] == q]
        if len(subset) > 0:
            st.write(f"**{q}** ({len(subset)} items)")
            st.dataframe(subset[['MenuItem', 'MenuMixPct', 'AvgMarginPct']].rename(columns={
                'MenuItem': 'Item', 'MenuMixPct': 'Popularity %', 'AvgMarginPct': 'Margin %'
            }), hide_index=True, use_container_width=True)

    st.caption(f"Median popularity: {pop_med:.1f}% | Median margin: {mar_med:.1f}%")

with right:
    st.subheader("Revenue by Location (Monthly)")
    daily = filtered_txn.groupby(['Date', 'Location'])['Revenue'].sum().reset_index()
    daily['Month'] = pd.to_datetime(daily['Date']).dt.to_period('M').astype(str)
    monthly = daily.groupby(['Month', 'Location'])['Revenue'].sum().unstack(fill_value=0)
    st.line_chart(monthly)

# ============================================================
# CHARTS ROW 2
# ============================================================
left2, right2 = st.columns(2)

with left2:
    st.subheader("Demand by Hour & Order Type")
    hourly = filtered_txn.groupby(['Hour', 'OrderType'])['OrderID'].nunique().unstack(fill_value=0)
    st.bar_chart(hourly)

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
    camp_df = camp_df.set_index('Campaign')
    st.bar_chart(camp_df[['ROAS']])

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

labour_pivot = labour_summary.pivot(index='Role', columns='Location', values='LabourCost').fillna(0)
st.bar_chart(labour_pivot)

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
