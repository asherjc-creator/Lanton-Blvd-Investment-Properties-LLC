import streamlit as st
import pandas as pd
import calendar
import plotly.express as px
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Revenue Management - Arlington 22213", layout="wide")

# --- DATA PROCESSING ---
@st.cache_data
def load_and_clean():
    files = {
        2024: 'ECONO - 2024.csv',
        2025: 'ECONO - 2025.csv',
        2026: 'ECONO - 2026.csv'
    }
    
    all_data = []
    for year, file_path in files.items():
        df = pd.read_csv(file_path)
        # Standardize date format
        df['IDS_DATE'] = pd.to_datetime(df['IDS_DATE'], format='%m/%d/%Y', errors='coerce')
        
        # Clean numeric columns (handle strings with commas or % signs)
        for col in ['RoomRev', 'OccPercent', 'ADR', 'RevPAR']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').str.replace('%', '').str.replace('$', '').strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['Year'] = year
        df['Month'] = df['IDS_DATE'].dt.month
        all_data.append(df)
        
    return pd.concat(all_data)

df_all = load_and_clean()

# --- SIDEBAR ---
st.sidebar.image("https://www.choicehotels.com/hotel-logos/brand-logos/econo-lodge.svg", width=120)
st.sidebar.title("📅 RM Controls")

# Selection for month
month_names = list(calendar.month_name)[1:] # All months
selected_month_name = st.sidebar.selectbox("Select Month for Comparison", month_names, index=3) # Default April
selected_month_idx = list(calendar.month_name).index(selected_month_name)

# Filter Data for the selected month across all years
monthly_df = df_all[df_all['Month'] == selected_month_idx]

# --- KPI CALCULATIONS ---
# Target 2024 metrics
target_2024 = monthly_df[monthly_df['Year'] == 2024]
t_rev = target_2024['RoomRev'].sum()
t_adr = target_2024['ADR'].mean()
t_occ = target_2024['OccPercent'].mean()

# Current 2026 metrics
current_2026 = monthly_df[monthly_df['Year'] == 2026]
c_rev = current_2026['RoomRev'].sum()
c_adr = current_2026['ADR'].mean()
c_occ = current_2026['OccPercent'].mean()

# --- DASHBOARD HEADER ---
st.title(f"Revenue Comparison Dashboard: {selected_month_name}")
st.markdown(f"**Arlington, VA 22213** | Comparative Analysis 2024 vs 2025 vs 2026")

col1, col2, col3, col4 = st.columns(4)

def delta_text(curr, target, is_percent=False):
    if target == 0 or pd.isna(target) or pd.isna(curr): return None
    diff = curr - target
    return f"{diff:+.1f}%" if is_percent else f"${diff:+.2f}"

col1.metric("2026 Total Revenue", f"${c_rev:,.0f}", delta_text(c_rev, t_rev) if c_rev > 0 else None)
col2.metric("2026 Avg ADR", f"${c_adr:.2f}", delta_text(c_adr, t_adr) if c_adr > 0 else None)
col3.metric("2026 Avg Occupancy", f"{c_occ:.1f}%", delta_text(c_occ, t_occ, True) if c_occ > 0 else None)

with col4:
    st.info(f"**2024 Target (Baseline)**\n\nRev: ${t_rev:,.0f} | ADR: ${t_adr:.2f}")

st.divider()

# --- KPI CHARTS (BAR CHARTS) ---
st.subheader(f"YoY Performance Metrics - {selected_month_name}")

# Prepare aggregation for charts
chart_data = monthly_df.groupby('Year').agg({
    'RoomRev': 'sum',
    'ADR': 'mean',
    'OccPercent': 'mean'
}).reset_index()

c1, c2, c3 = st.columns(3)

with c1:
    fig_rev = px.bar(chart_data, x='Year', y='RoomRev', 
                     title="Total Room Revenue",
                     color='Year', color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_rev.update_layout(showlegend=False)
    st.plotly_chart(fig_rev, use_container_width=True)

with c2:
    fig_adr = px.bar(chart_data, x='Year', y='ADR', 
                     title="Average Daily Rate (ADR)",
                     color='Year', color_discrete_sequence=px.colors.qualitative.Safe)
    fig_adr.update_layout(showlegend=False)
    st.plotly_chart(fig_adr, use_container_width=True)

with c3:
    fig_occ = px.bar(chart_data, x='Year', y='OccPercent', 
                     title="Average Occupancy %",
                     color='Year', color_discrete_sequence=px.colors.qualitative.Prism)
    fig_occ.update_layout(showlegend=False, yaxis_range=[0,100])
    st.plotly_chart(fig_occ, use_container_width=True)

# --- CALENDAR VIEW ---
st.divider()
st.subheader(f"2026 Daily Yield Calendar: {selected_month_name}")

cal = calendar.monthcalendar(2026, selected_month_idx)
weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
cols = st.columns(7)
for i, day in enumerate(weekdays):
    cols[i].markdown(f"<center><b>{day}</b></center>", unsafe_allow_html=True)

for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write("")
        else:
            day_data = current_2026[current_2026['IDS_DATE'].dt.day == day]
            if not day_data.empty:
                adr = day_data['ADR'].values[0]
                occ = day_data['OccPercent'].values[0]
                # Dynamic color: Blue for high occupancy, Orange for low
                color = "#99ccff" if occ > 80 else "#ffebcc" if occ < 50 else "#cce5ff"
                
                cols[i].markdown(
                    f"""<div style="border:1px solid #ddd; padding:8px; border-radius:5px; background-color:{color}; text-align:center;">
                    <span style="font-size:1.1em; font-weight:bold;">{day}</span><br>
                    <small>ADR: <b>${adr:.0f}</b></small><br>
                    <small>OCC: <b>{occ:.0f}%</b></small>
                    </div>""", unsafe_allow_html=True
                )
            else:
                cols[i].markdown(
                    f"""<div style="border:1px solid #eee; padding:8px; border-radius:5px; color:#aaa; text-align:center;">
                    {day}<br><small>No Data</small>
                    </div>""", unsafe_allow_html=True
                )
