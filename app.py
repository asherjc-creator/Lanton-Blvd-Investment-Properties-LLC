import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Hotel Rate Code Analytics", page_icon="🏨", layout="wide")
st.title("🏨 Rate Code Performance Dashboard")
st.markdown("Interactive analysis of room nights, revenue, and ADR (2024–2026 YTD)")

# ------------------------------
# Direct Choice Brand Codes
# ------------------------------
BRAND_CODES = {
    "GNT", "LSTATE", "S3A", "SAAA", "SAARP", "SAPR1", "SAPR1M", "SAPR1Y",
    "SAPR2", "SAPR2M", "SAPR2Y", "SBAR", "SC10", "SC12", "SC15", "SC5",
    "SCC12", "SCPM", "SCPO1", "SCPO2", "SCR", "SGM", "SGML", "SGRP0",
    "SGRP1", "SGRP2", "SGRP3", "SPC", "SPPS", "SSC", "SSO", "STD",
    "S3A1", "SAARP1", "PKPR1", "PKPR2", "PKPR3", "PKPRX"
}

# ------------------------------
# Data Loading
# ------------------------------
@st.cache_data
def load_data():
    data_frames = {}
    try:
        df_2024 = pd.read_excel("Rate code 2024.xlsx", sheet_name="Rate code 2024")
        df_2024.columns = df_2024.columns.str.replace("﻿", "").str.strip()
        df_2024['Year'] = 2024
        data_frames['2024'] = df_2024
    except Exception as e:
        st.error(f"Error loading 2024: {e}")
        return None

    try:
        df_2025 = pd.read_excel("Rate code 2025.xlsx", sheet_name="Rate code 2025")
        df_2025.columns = df_2025.columns.str.replace("﻿", "").str.strip()
        df_2025['Year'] = 2025
        data_frames['2025'] = df_2025
    except Exception as e:
        st.error(f"Error loading 2025: {e}")
        return None

    try:
        df_2026 = pd.read_csv("Rate code 2026.csv")
        df_2026.columns = df_2026.columns.str.replace("﻿", "").str.strip()
        df_2026['Year'] = 2026
        data_frames['2026'] = df_2026
    except Exception as e:
        st.error(f"Error loading 2026: {e}")
        return None

    combined = pd.concat(data_frames.values(), ignore_index=True)
    combined['Daily AVG'] = combined['Daily AVG'].replace([np.inf, -np.inf], np.nan)
    return combined, data_frames

result = load_data()
if result is None:
    st.stop()
combined_df, yearly_dfs = result

# ------------------------------
# Sidebar Filters
# ------------------------------
st.sidebar.header("Filters")
selected_years = st.sidebar.multiselect(
    "Select Years",
    options=sorted(combined_df['Year'].unique()),
    default=sorted(combined_df['Year'].unique())
)
min_rev = st.sidebar.slider(
    "Minimum Room Revenue ($)",
    min_value=0,
    max_value=int(combined_df['Room Revenue'].max()),
    value=1000
)
brand_only = st.sidebar.checkbox("🎯 Show only Direct Choice Brand Codes", value=False)

# Apply filters
filtered_df = combined_df[
    (combined_df['Year'].isin(selected_years)) &
    (combined_df['Room Revenue'] >= min_rev)
]

if brand_only:
    filtered_df = filtered_df[filtered_df['IDS_RATE_CODE'].isin(BRAND_CODES)]

# ------------------------------
# KPI Cards
# ------------------------------
st.header("📊 Key Performance Indicators")

if not brand_only and not filtered_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("All Rate Codes")
        for year in selected_years:
            ydf = filtered_df[filtered_df['Year'] == year]
            rev = ydf['Room Revenue'].sum()
            nights = ydf['Room Nights'].sum()
            adr = rev / nights if nights else 0
            st.metric(f"**{year}**", f"${rev:,.0f}", f"{nights:,.0f} nights | ADR ${adr:.2f}")
    with col2:
        st.subheader("Direct Choice Brand Codes")
        brand_df = combined_df[
            (combined_df['Year'].isin(selected_years)) &
            (combined_df['IDS_RATE_CODE'].isin(BRAND_CODES))
        ]
        for year in selected_years:
            ydf = brand_df[brand_df['Year'] == year]
            rev = ydf['Room Revenue'].sum()
            nights = ydf['Room Nights'].sum()
            adr = rev / nights if nights else 0
            st.metric(f"**{year}**", f"${rev:,.0f}", f"{nights:,.0f} nights | ADR ${adr:.2f}")
else:
    cols = st.columns(len(selected_years))
    for i, year in enumerate(selected_years):
        ydf = filtered_df[filtered_df['Year'] == year]
        rev = ydf['Room Revenue'].sum()
        nights = ydf['Room Nights'].sum()
        adr = rev / nights if nights else 0
        with cols[i]:
            st.metric(f"**{year}**", f"${rev:,.0f}", f"{nights:,.0f} nights | ADR ${adr:.2f}")

# ------------------------------
# Chart 1: Top 10 Revenue by Year (Bar Chart)
# ------------------------------
st.header("🏆 Top 10 Rate Codes by Revenue")
if not filtered_df.empty:
    top_data = []
    for year in selected_years:
        top = filtered_df[filtered_df['Year'] == year].nlargest(10, 'Room Revenue')[
            ['IDS_RATE_CODE', 'Room Revenue', 'Year']
        ]
        top_data.append(top)
    plot_df = pd.concat(top_data)
    fig1 = px.bar(
        plot_df,
        x='Room Revenue',
        y='IDS_RATE_CODE',
        color='Year',
        orientation='h',
        title='Top 10 Rate Codes by Revenue',
        labels={'Room Revenue': 'Revenue ($)', 'IDS_RATE_CODE': 'Rate Code'},
        barmode='group'
    )
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")

# ------------------------------
# Chart 2: ADR Trend Lines
# ------------------------------
st.header("📈 ADR Evolution – Top Volume Codes")
if not filtered_df.empty:
    top_volume = filtered_df.groupby('IDS_RATE_CODE')['Room Nights'].sum().nlargest(5).index.tolist()
    trend_df = filtered_df[filtered_df['IDS_RATE_CODE'].isin(top_volume)]
    fig2 = px.line(
        trend_df,
        x='Year',
        y='Daily AVG',
        color='IDS_RATE_CODE',
        markers=True,
        title='ADR Trends for Top 5 Volume Codes',
        labels={'Daily AVG': 'ADR ($)', 'Year': 'Year'}
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("No data available for ADR trends.")

# ------------------------------
# Chart 3: Revenue Share by Segment (Pie)
# ------------------------------
st.header("🥧 Revenue Share by Segment")

def map_segment(code):
    code = str(code).upper()
    if code in ['SBOOK', 'LEXP']:
        return 'OTA'
    if code == 'RACK':
        return 'Rack'
    if code.startswith(('SCPM', 'SRTL', 'SCR', 'SCC')):
        return 'Corporate'
    if code.startswith(('LPROMO', 'LOPQ', 'SAPR', 'SOPM', 'SP')):
        return 'Promo/Package'
    if code == 'GROUP~':
        return 'Group'
    return 'Other'

if not filtered_df.empty:
    filtered_df['Segment'] = filtered_df['IDS_RATE_CODE'].apply(map_segment)
    seg_data = filtered_df.groupby(['Year', 'Segment'])['Room Revenue'].sum().reset_index()
    fig3 = px.pie(
        seg_data,
        values='Room Revenue',
        names='Segment',
        facet_col='Year',
        title='Revenue Share by Segment',
        hole=0.3
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("No data available for segment analysis.")

# ------------------------------
# Chart 4: Heatmap (Presence)
# ------------------------------
st.header("🔥 Rate Code Presence Heatmap")
if not filtered_df.empty:
    presence = filtered_df.pivot_table(
        index='IDS_RATE_CODE',
        columns='Year',
        values='Room Revenue',
        aggfunc='sum',
        fill_value=0
    )
    presence = (presence > 0).astype(int)
    # Sort by total revenue
    total_rev = filtered_df.groupby('IDS_RATE_CODE')['Room Revenue'].sum().sort_values(ascending=False)
    presence = presence.loc[total_rev.head(30).index]
    fig4 = px.imshow(
        presence,
        text_auto=True,
        aspect='auto',
        color_continuous_scale='RdYlGn',
        title='Rate Code Presence by Year (Top 30 by Total Revenue)'
    )
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.warning("No data for heatmap.")

# ------------------------------
# Chart 5: Pareto Analysis
# ------------------------------
st.header("📐 Pareto Analysis – Revenue Concentration")
if not filtered_df.empty:
    year_choice = st.selectbox("Select Year for Pareto Chart", selected_years)
    pareto = filtered_df[filtered_df['Year'] == year_choice].sort_values('Room Revenue', ascending=False)
    pareto['Cumulative %'] = 100 * pareto['Room Revenue'].cumsum() / pareto['Room Revenue'].sum()
    pareto['Rank'] = range(1, len(pareto) + 1)

    fig5 = make_subplots(specs=[[{"secondary_y": True}]])
    fig5.add_trace(
        go.Bar(x=pareto['Rank'], y=pareto['Room Revenue'], name='Revenue', marker_color='steelblue'),
        secondary_y=False
    )
    fig5.add_trace(
        go.Scatter(
            x=pareto['Rank'],
            y=pareto['Cumulative %'],
            name='Cumulative %',
            mode='lines+markers',
            line=dict(color='darkorange')
        ),
        secondary_y=True
    )
    fig5.add_hline(y=80, line_dash="dash", line_color="red", secondary_y=True)
    fig5.update_layout(
        title=f'Pareto Chart – {year_choice}',
        xaxis_title='Rate Code Rank',
        hovermode='x unified'
    )
    fig5.update_yaxes(title_text="Revenue ($)", secondary_y=False)
    fig5.update_yaxes(title_text="Cumulative %", secondary_y=True)
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.warning("No data for Pareto chart.")

# ------------------------------
# Raw Data Explorer & Download
# ------------------------------
with st.expander("🔍 View / Download Filtered Data"):
    st.dataframe(filtered_df.sort_values(['Year', 'Room Revenue'], ascending=[True, False]))
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_rate_codes.csv",
        mime="text/csv"
    )
