import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page Config
st.set_page_config(page_title="Econo Lodge Metro - Revenue Dashboard", layout="wide")

# --- DATA LOADING & CLEANING ---
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
        df['IDS_DATE'] = pd.to_datetime(df['IDS_DATE'], format='%m/%d/%Y')
        # Clean currency and percentages
        df['RoomRev'] = df['RoomRev'].astype(str).str.replace(',', '').astype(float)
        df['OccPercent'] = df['OccPercent'].astype(str).str.replace('%', '').astype(float)
        df['Year'] = year
        df['Month'] = df['IDS_DATE'].dt.month
        df['Month_Name'] = df['IDS_DATE'].dt.strftime('%b')
        all_data.append(df)
    return pd.concat(all_data)

df_all = load_data()

# --- SIDEBAR CONTROLS ---
st.sidebar.image("https://www.choicehotels.com/hotel-logos/brand-logos/econo-lodge.svg", width=150)
st.sidebar.title("Revenue Control Center")
selected_year = st.sidebar.selectbox("Select Analysis Year", [2026, 2025, 2024])
months = df_all['Month_Name'].unique()
selected_month = st.sidebar.selectbox("Select Month", months)

# Filter Data
current_data = df_all[(df_all['Year'] == selected_year) & (df_all['Month_Name'] == selected_month)]
target_year_data = df_all[(df_all['Year'] == 2024) & (df_all['Month_Name'] == selected_month)]

# --- HEADER METRICS ---
st.title(f"📊 {selected_year} Performance vs. 2024 Target")
st.markdown(f"**Viewing:** {selected_month} {selected_year} | **Benchmark Year:** 2024")

col1, col2, col3, col4 = st.columns(4)

def get_metrics(data):
    rev = data['RoomRev'].sum()
    adr = data['ADR'].mean()
    occ = data['OccPercent'].mean()
    return rev, adr, occ

curr_rev, curr_adr, curr_occ = get_metrics(current_data)
targ_rev, targ_adr, targ_occ = get_metrics(target_year_data)

with col1:
    st.metric("Total Revenue", f"${curr_rev:,.2f}", f"{((curr_rev/targ_rev)-1)*100:.1f}% vs 2024")
with col2:
    st.metric("Avg ADR", f"${curr_adr:.2f}", f"${curr_adr - targ_adr:.2f} vs 2024")
with col3:
    st.metric("Avg Occupancy", f"{curr_occ:.1f}%", f"{curr_occ - targ_occ:.1f}% vs 2024")
with col4:
    st.metric("Target Revenue (2024)", f"${targ_rev:,.2f}")

st.divider()

# --- VISUALIZATIONS ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("Daily Revenue: Current vs Target")
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Scatter(x=list(range(1, 32)), y=target_year_data['RoomRev'], name='2024 Target', fill='tozeroy', line_color='gray', opacity=0.3))
    fig_rev.add_trace(go.Scatter(x=list(range(1, 32)), y=current_data['RoomRev'], name=f'{selected_year} Actual', line_color='#00CC96'))
    fig_rev.update_layout(xaxis_title="Day of Month", yaxis_title="Revenue ($)", hovermode="x unified")
    st.plotly_chart(fig_rev, use_container_width=True)

with c2:
    st.subheader("Yield Strategy: ADR vs Occupancy")
    # Monthly Aggregates for all years to show trends
    monthly_stats = df_all.groupby(['Year', 'Month_Name', 'Month']).agg({'ADR':'mean', 'OccPercent':'mean', 'RoomRev':'sum'}).reset_index().sort_values('Month')
    fig_bubble = px.scatter(monthly_stats, x="OccPercent", y="ADR", size="RoomRev", color="Year",
                            hover_name="Month_Name", text="Month_Name", size_max=40,
                            color_continuous_scale=px.colors.sequential.Viridis)
    st.plotly_chart(fig_bubble, use_container_width=True)

# --- REVENUE MANAGEMENT GUIDANCE ---
st.subheader("🎯 Monthly Strategic Guidance")
gap = targ_rev - curr_rev
if gap > 0:
    st.error(f"Gap to 2024 Target: **${gap:,.2f}**. Focus on increasing {'Occupancy' if curr_occ < targ_occ else 'ADR'}.")
else:
    st.success(f"Beating 2024 Target by **${abs(gap):,.2f}**! Opportunity to push ADR.")

st.dataframe(df_all[df_all['Year'] == selected_year].groupby('Month_Name')[['RoomRev', 'ADR', 'OccPercent']].sum().sort_index(), use_container_width=True)
