import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Revenue Command Center", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    files = {
        2024: 'ECONO - 2024.csv',
        2025: 'ECONO - 2025.csv',
        2026: 'ECONO - 2026.csv'
    }
    all_data = []
    for year, file in files.items():
        df = pd.read_csv(file)
        df['IDS_DATE'] = pd.to_datetime(df['IDS_DATE'])
        df['RoomRev'] = df['RoomRev'].astype(str).str.replace(',', '').astype(float)
        df['OccPercent'] = df['OccPercent'].astype(str).str.replace('%', '').astype(float)

        # REQUIRED: add Rooms Sold if missing
        if 'RoomsSold' not in df.columns:
            df['RoomsSold'] = (df['OccPercent'] / 100) * 100  # replace 100 with actual room count

        df['Year'] = year
        df['Month'] = df['IDS_DATE'].dt.month
        df['Month_Name'] = df['IDS_DATE'].dt.strftime('%b')
        df['DOW'] = df['IDS_DATE'].dt.day_name()

        all_data.append(df)

    return pd.concat(all_data)

df_all = load_data()

# --- SIDEBAR ---
st.sidebar.title("Revenue Control Center")

selected_year = st.sidebar.selectbox("Year", [2026, 2025, 2024])
months = df_all.sort_values('Month')['Month_Name'].unique()
selected_month = st.sidebar.selectbox("Month", months)

selected_dow = st.sidebar.multiselect(
    "Day of Week Filter",
    df_all['DOW'].unique(),
    default=df_all['DOW'].unique()
)

# --- FILTER DATA ---
data = df_all[
    (df_all['Year'] == selected_year) &
    (df_all['Month_Name'] == selected_month) &
    (df_all['DOW'].isin(selected_dow))
]

target = df_all[
    (df_all['Year'] == 2024) &
    (df_all['Month_Name'] == selected_month)
]

# --- METRICS ---
def get_metrics(df):
    revenue = df['RoomRev'].sum()
    rooms = df['RoomsSold'].sum()
    adr = revenue / rooms if rooms > 0 else 0
    occ = df['OccPercent'].mean()
    revpar = adr * (occ / 100)
    return revenue, adr, occ, revpar

curr_rev, curr_adr, curr_occ, curr_revpar = get_metrics(data)
targ_rev, targ_adr, targ_occ, targ_revpar = get_metrics(target)

st.title(f"📊 {selected_month} {selected_year} Performance")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Revenue", f"${curr_rev:,.0f}", f"{(curr_rev/targ_rev-1)*100:.1f}% vs 2024")
c2.metric("ADR", f"${curr_adr:.2f}", f"{curr_adr - targ_adr:.2f}")
c3.metric("Occupancy", f"{curr_occ:.1f}%", f"{curr_occ - targ_occ:.1f}%")
c4.metric("RevPAR", f"${curr_revpar:.2f}", f"{curr_revpar - targ_revpar:.2f}")

st.divider()

# --- DAILY TREND ---
st.subheader("📈 Daily Revenue vs Target")

data = data.sort_values('IDS_DATE')
target = target.sort_values('IDS_DATE')

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=target['IDS_DATE'].dt.day,
    y=target['RoomRev'],
    name="2024 Target",
    fill='tozeroy',
    opacity=0.3
))

fig.add_trace(go.Scatter(
    x=data['IDS_DATE'].dt.day,
    y=data['RoomRev'],
    name=f"{selected_year} Actual",
    line=dict(color="#00CC96")
))

st.plotly_chart(fig, use_container_width=True)

# --- PICKUP (PACE) ---
st.subheader("📅 Booking Pace (Pickup)")

pickup = df_all[df_all['Year'].isin([2024, selected_year])].copy()

# Create Day column PROPERLY on the same dataframe
pickup['Day'] = pickup['IDS_DATE'].dt.day

# Aggregate daily revenue
pickup = pickup.groupby(['Year', 'Day'], as_index=False)['RoomRev'].sum()

# Sort before cumulative sum
pickup = pickup.sort_values(['Year', 'Day'])

# Calculate cumulative revenue (pace)
pickup['CumulativeRev'] = pickup.groupby('Year')['RoomRev'].cumsum()

# Plot
fig2 = px.line(
    pickup,
    x='Day',
    y='CumulativeRev',
    color='Year',
    title="Cumulative Revenue Pace"
)

st.plotly_chart(fig2, use_container_width=True)

# --- STRATEGY ENGINE ---
st.subheader("🎯 Revenue Strategy Engine")

if curr_occ < 60:
    st.error("Low occupancy → Open discounts, push OTA channels.")
elif curr_occ < targ_occ:
    st.warning("Behind occupancy → Tactical promotions recommended.")
elif curr_adr < targ_adr:
    st.warning("ADR under target → Reduce discounting.")
else:
    st.success("Strong performance → Push rate increases.")

# --- MONTHLY SUMMARY ---
st.subheader("📋 Monthly Summary")

summary = df_all[df_all['Year'] == selected_year].groupby('Month_Name').agg({
    'RoomRev': 'sum',
    'OccPercent': 'mean'
})

st.dataframe(summary, use_container_width=True)
