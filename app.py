import streamlit as st
import pandas as pd
import calendar
import plotly.express as px

# Page Configuration
st.set_page_config(page_title="Revenue Management - Arlington 22213", layout="wide")

# --- DATA PROCESSING ---
@st.cache_data
def load_and_clean():
    # File map for your uploaded data
    files = {
        2024: 'ECONO - 2024.csv',
        2025: 'ECONO - 2025.csv',
        2026: 'ECONO - 2026.csv'
    }
    
    all_data = []
    for year, file_path in files.items():
        try:
            df = pd.read_csv(file_path)
            # Standardize date format
            df['IDS_DATE'] = pd.to_datetime(df['IDS_DATE'], format='%m/%d/%Y', errors='coerce')
            
            # Clean numeric columns (handling commas, % signs, and currency symbols)
            numeric_cols = ['RoomRev', 'OccPercent', 'ADR', 'RevPAR']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = (df[col].astype(str)
                               .str.replace(',', '', regex=False)
                               .str.replace('%', '', regex=False)
                               .str.replace('$', '', regex=False)
                               .str.strip())
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['Year'] = year
            df['Month'] = df['IDS_DATE'].dt.month
            all_data.append(df)
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")
            
    return pd.concat(all_data) if all_data else pd.DataFrame()

# Load Data
df_all = load_and_clean()

# --- SIDEBAR CONTROLS ---
st.sidebar.image("https://www.choicehotels.com/hotel-logos/brand-logos/econo-lodge.svg", width=120)
st.sidebar.title("📅 RM Controls")

# Selection for month
month_names = list(calendar.month_name)[1:]
selected_month_name = st.sidebar.selectbox("Select Month for Comparison", month_names, index=3) # Default: April
selected_month_idx = list(calendar.month_name).index(selected_month_name)

# Filter Data for the selected month across all years
monthly_df = df_all[df_all['Month'] == selected_month_idx]

# --- KPI CALCULATIONS ---
# 2024 Target Metrics
target_2024 = monthly_df[monthly_df['Year'] == 2024]
t_rev = target_2024['RoomRev'].sum()
t_adr = target_2024['ADR'].mean()
t_occ = target_2024['OccPercent'].mean()

# 2026 Performance Metrics
current_2026 = monthly_df[monthly_df['Year'] == 2026]
c_rev = current_2026['RoomRev'].sum()
c_adr = current_2026['ADR'].mean()
c_occ = current_2026['OccPercent'].mean()

# --- DASHBOARD HEADER ---
st.title(f"Revenue Dashboard: {selected_month_name}")
st.markdown(f"**Location:** Arlington, VA 22213 | **Baseline Target:** 2024 Performance")

# Metric Row
m1, m2, m3 = st.columns(3)
m1.metric("2026 Total Revenue", f"${c_rev:,.0f}", f"{c_rev - t_rev:+,.0f} vs 2024")
m2.metric("2026 Avg ADR", f"${c_adr:.2f}", f"${c_adr - t_adr:+.2f} vs 2024")
m3.metric("2026 Avg Occupancy", f"{c_occ:.1f}%", f"{c_occ - t_occ:+.1f}% vs 2024")

st.divider()

# --- YoY KPI BAR CHARTS ---
st.subheader(f"YoY Comparison ({selected_month_name})")

# Aggregating data for the charts
chart_data = monthly_df.groupby('Year').agg({
    'RoomRev': 'sum',
    'ADR': 'mean',
    'OccPercent': 'mean'
}).reset_index()

c1, c2, c3 = st.columns(3)

with c1:
    fig_rev = px.bar(chart_data, x='Year', y='RoomRev', text_auto='.2s', title="Total Revenue",
                     color='Year', color_discrete_map={2024: '#636EFA', 2025: '#EF553B', 2026: '#00CC96'})
    fig_rev.update_layout(showlegend=False)
    st.plotly_chart(fig_rev, use_container_width=True)

with c2:
    fig_adr = px.bar(chart_data, x='Year', y='ADR', text_auto='.2f', title="Avg Daily Rate (ADR)",
                     color='Year', color_discrete_map={2024: '#636EFA', 2025: '#EF55
