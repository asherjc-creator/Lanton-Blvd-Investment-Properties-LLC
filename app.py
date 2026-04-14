import streamlit as st
import pandas as pd
import calendar
import plotly.express as px

# Page Setup
st.set_page_config(page_title="Arlington 22213 Revenue Dashboard", layout="wide")

@st.cache_data
def load_data():
    files = {2024: 'ECONO - 2024.csv', 2025: 'ECONO - 2025.csv', 2026: 'ECONO - 2026.csv'}
    combined = []
    for year, path in files.items():
        try:
            df = pd.read_csv(path)
            df['IDS_DATE'] = pd.to_datetime(df['IDS_DATE'], format='%m/%d/%Y', errors='coerce')
            # Clean numeric columns properly using the .str accessor
            for col in ['RoomRev', 'OccPercent', 'ADR', 'RevPAR']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[$,%]', '', regex=True), errors='coerce')
            df['Year'] = year
            df['Month'] = df['IDS_DATE'].dt.month
            combined.append(df)
        except Exception as e:
            st.error(f"Error loading {path}: {e}")
    return pd.concat(combined) if combined else pd.DataFrame()

df_all = load_data()

# --- SIDEBAR ---
st.sidebar.title("🏨 Econo Lodge Metro")
st.sidebar.subheader("Arlington, VA 22213")
month_names = list(calendar.month_name)[1:]
selected_month_name = st.sidebar.selectbox("Select Month", month_names, index=3) # April
selected_month_idx = list(calendar.month_name).index(selected_month_name)

# Filter Logic
monthly_df = df_all[df_all['Month'] == selected_month_idx]
target_24 = monthly_df[monthly_df['Year'] == 2024]
current_26 = monthly_df[monthly_df['Year'] == 2026]

# Aggregates
t_rev, t_adr, t_occ = target_24['RoomRev'].sum(), target_24['ADR'].mean(), target_24['OccPercent'].mean()
c_rev, c_adr, c_occ = current_26['RoomRev'].sum(), current_26['ADR'].mean(), current_26['OccPercent'].mean()

# --- MAIN DASHBOARD ---
st.title(f"Revenue Management: {selected_month_name} 2026")
st.markdown("Targeting **2024 KPI Benchmarks**")

# Metrics
m1, m2, m3 = st.columns(3)
m1.metric("2026 Revenue", f"${c_rev:,.0f}", f"{c_rev - t_rev:+,.0f} vs 2024")
m2.metric("2026 ADR", f"${c_adr:.2f}", f"${c_adr - t_adr:+.2f} vs 2024")
m3.metric("2026 Occupancy", f"{c_occ:.1f}%", f"{c_occ - t_occ:+.1f}% vs 2024")

st.divider()

# --- BAR CHARTS ---
st.subheader("Year-Over-Year Comparison")
chart_data = monthly_df.groupby('Year').agg({'RoomRev':'sum', 'ADR':'mean', 'OccPercent':'mean'}).reset_index()
c1, c2, c3 = st.columns(3)

# Define color map for consistency
color_map = {2024: '#636EFA', 2025: '#EF553B', 2026: '#00CC96'}

with c1:
    fig1 = px.bar(chart_data, x='Year', y='RoomRev', title="Total Revenue", color='Year', color_discrete_map=color_map)
    st.plotly_chart(fig1, use_container_width=True)
with c2:
    fig2 = px.bar(chart_data, x='Year', y='ADR', title="Avg ADR", color='Year', color_discrete_map=color_map)
    st.plotly_chart(fig2, use_container_width=True)
with c3:
    fig3 = px.bar(chart_data, x='Year', y='OccPercent', title="Avg Occ %", color='Year', color_discrete_map=color_map)
    st.plotly_chart(fig3, use_container_width=True)

# --- CALENDAR ---
st.divider()
st.subheader(f"2026 Calendar & Pricing Recommendation")
st.info(f"Target: ADR ${t_adr:.2f} | Occ {t_occ:.1f}%")

cal = calendar.monthcalendar(2026, selected_month_idx)
cols = st.columns(7)
for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
    cols[i].markdown(f"<center><b>{d}</b></center>", unsafe_allow_html=True)

for week in cal:
    day_cols = st.columns(7)
    for i, day in enumerate(week):
        if day != 0:
            day_data = current_26[current_26['IDS_DATE'].dt.day == day]
            if not day_data.empty:
                adr, occ = day_data['ADR'].iloc[0], day_data['OccPercent'].iloc[0]
                bg = "#d1fae5" if occ >= t_occ else "#ffedd5"
                day_cols[i].markdown(f"""<div style="border:1px solid #ddd; padding:10px; border-radius:8px; background-color:{bg}; text-align:center;">
                    <b>{day}</b><br><small>${adr:.0f} ADR<br>{occ:.0f}% OCC</small></div>""", unsafe_allow_html=True)
            else:
                day_cols[i].markdown(f"""<div style="border:1px solid #eee; padding:10px; border-radius:8px; text-align:center; color:#999;">
                    {day}<br><small>Tgt:<br>${t_adr:.0f}</small></div>""", unsafe_allow_html=True)
