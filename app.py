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
    # Loading uploaded files
    df24 = pd.read_csv('ECONO - 2024.csv')
    df26 = pd.read_csv('ECONO - 2026.csv')
    
    def process(df, year):
        df['IDS_DATE'] = pd.to_datetime(df['IDS_DATE'], format='%m/%d/%Y')
        # Clean currency/percentage strings
        for col in ['RoomRev', 'OccPercent']:
            df[col] = df[col].astype(str).str.replace(',', '').str.replace('%', '').astype(float)
        df['Year'] = year
        return df

    return process(df24, 2024), process(df26, 2026)

df24, df26 = load_and_clean()

# --- SIDEBAR ---
st.sidebar.image("https://www.choicehotels.com/hotel-logos/brand-logos/econo-lodge.svg", width=120)
st.sidebar.title("📅 RM Controls")
month_names = list(calendar.month_name)[4:13] # April to December
selected_month_name = st.sidebar.selectbox("Select Month", month_names)
selected_month = list(calendar.month_name).index(selected_month_name)

# --- CALCULATIONS ---
# 2024 Targets for the selected month
target_month = df24[df24['IDS_DATE'].dt.month == selected_month]
target_adr = target_month['ADR'].mean()
target_occ = target_month['OccPercent'].mean()
target_revpar = target_month['RevPAR'].mean()

# 2026 Performance (Actual or Pacing)
current_month = df26[df26['IDS_DATE'].dt.month == selected_month]
curr_adr = current_month['ADR'].mean() if not current_month.empty else 0
curr_occ = current_month['OccPercent'].mean() if not current_month.empty else 0

# --- DASHBOARD HEADER ---
st.title(f"Revenue Dashboard: {selected_month_name} 2026")
st.markdown(f"**Market:** Arlington, VA 22213 | **Baseline:** 2024 KPIs")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Target ADR", f"${target_adr:.2f}")
col2.metric("Target Occupancy", f"{target_occ:.1f}%")
col3.metric("Target RevPAR", f"${target_revpar:.2f}")

# Recommendation Logic
with col4:
    st.subheader("💡 Pricing Advice")
    if curr_adr == 0:
        st.info(f"Set baseline rate at **${target_adr:.2f}**")
    elif curr_adr < target_adr:
        st.warning("Rate is below 2024 Target. **Increase Pricing.**")
    else:
        st.success("Target ADR achieved. Hold or Push.")

st.divider()

# --- CALENDAR VIEW ---
st.subheader(f"Daily Yield Calendar: {selected_month_name}")

# Create Calendar Grid
cal = calendar.monthcalendar(2026, selected_month)
cols = st.columns(7)
weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Header Row
for i, day in enumerate(weekdays):
    cols[i].markdown(f"**{day}**")

# Calendar Rows
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write("")
        else:
            # Fetch daily data for 2026 if available, else show target
            day_data = current_month[current_month['IDS_DATE'].dt.day == day]
            
            if not day_data.empty:
                adr = day_data['ADR'].values[0]
                occ = day_data['OccPercent'].values[0]
                revp = day_data['RevPAR'].values[0]
                
                # Visual styling based on occupancy
                bg_color = "#e6f3ff" if occ < 50 else "#cce5ff" if occ < 80 else "#99ccff"
                
                cols[i].markdown(
                    f"""<div style="border:1px solid #ddd; padding:5px; border-radius:5px; background-color:{bg_color}; min-height:100px;">
                    <span style="font-weight:bold; font-size:1.2em;">{day}</span><br>
                    <small>ADR: <b>${adr:.0f}</b></small><br>
                    <small>RPAR: <b>${revp:.0f}</b></small><br>
                    <small>OCC: <b>{occ:.0f}%</b></small>
                    </div>""", unsafe_allow_index=True, unsafe_allow_html=True
                )
            else:
                # Placeholder for future dates
                cols[i].markdown(
                    f"""<div style="border:1px solid #eee; padding:5px; border-radius:5px; color:#999; min-height:100px;">
                    <span style="font-weight:bold;">{day}</span><br>
                    <small>Tgt ADR: ${target_adr:.0f}</small><br>
                    <small>Tgt Occ: {target_occ:.0f}%</small>
                    </div>""", unsafe_allow_html=True
                )

# --- ANALYTICS CHART ---
st.divider()
st.subheader("Performance Yield Map")
fig = px.scatter(target_month, x="OccPercent", y="ADR", size="RoomRev", color="RevPAR",
                 title=f"Optimal Yield Curve (Based on {selected_month_name} 2024 Actuals)",
                 labels={"OccPercent": "Occupancy %", "ADR": "Daily Rate ($)"})
st.plotly_chart(fig, use_container_width=True)
