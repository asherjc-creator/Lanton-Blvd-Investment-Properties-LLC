import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ------------------------------
# 1. Page Configuration
# ------------------------------
st.set_page_config(
    page_title="Hotel Rate Code Analytics 2024-2026",
    page_icon="🏨",
    layout="wide"
)

st.title("🏨 Rate Code Performance Dashboard")
st.markdown("Analysis of room nights, revenue, and ADR across 2024, 2025, and 2026 YTD.")

# ------------------------------
# 2. Data Loading Function
# ------------------------------
@st.cache_data
def load_data():
    """Load and combine data from Excel/CSV files."""
    data_frames = {}
    
    # Load 2024 Excel
    try:
        df_2024 = pd.read_excel("Rate code 2024.xlsx", sheet_name="Rate code 2024")
        # Clean column names (remove BOM and extra spaces)
        df_2024.columns = df_2024.columns.str.replace("﻿", "").str.strip()
        df_2024['Year'] = 2024
        data_frames['2024'] = df_2024
    except Exception as e:
        st.error(f"Error loading 2024 data: {e}")
        return None

    # Load 2025 Excel
    try:
        df_2025 = pd.read_excel("Rate code 2025.xlsx", sheet_name="Rate code 2025")
        df_2025.columns = df_2025.columns.str.replace("﻿", "").str.strip()
        df_2025['Year'] = 2025
        data_frames['2025'] = df_2025
    except Exception as e:
        st.error(f"Error loading 2025 data: {e}")
        return None

    # Load 2026 CSV
    try:
        df_2026 = pd.read_csv("Rate code 2026.csv")
        df_2026.columns = df_2026.columns.str.replace("﻿", "").str.strip()
        df_2026['Year'] = 2026
        data_frames['2026'] = df_2026
    except Exception as e:
        st.error(f"Error loading 2026 data: {e}")
        return None

    # Combine all years
    combined_df = pd.concat(data_frames.values(), ignore_index=True)
    
    # Handle NO SHOW with infinite ADR (set to NaN for calculations)
    combined_df['Daily AVG'] = combined_df['Daily AVG'].replace([np.inf, -np.inf], np.nan)
    
    return combined_df, data_frames

# ------------------------------
# 3. Main App
# ------------------------------
def main():
    # Load data
    with st.spinner("Loading data..."):
        result = load_data()
        if result is None:
            st.stop()
        combined_df, yearly_dfs = result

    # Sidebar filters
    st.sidebar.header("Filters")
    available_years = sorted(combined_df['Year'].unique())
    selected_years = st.sidebar.multiselect(
        "Select Years",
        options=available_years,
        default=available_years
    )
    
    min_revenue = st.sidebar.slider(
        "Minimum Total Revenue ($)",
        min_value=0,
        max_value=int(combined_df['Room Revenue'].max()),
        value=1000
    )

    # Filter data
    filtered_df = combined_df[
        (combined_df['Year'].isin(selected_years)) &
        (combined_df['Room Revenue'] >= min_revenue)
    ]

    # ------------------------------
    # KPI Cards
    # ------------------------------
    st.header("📊 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    for i, year in enumerate(selected_years):
        year_data = filtered_df[filtered_df['Year'] == year]
        total_revenue = year_data['Room Revenue'].sum()
        total_nights = year_data['Room Nights'].sum()
        avg_adr = total_revenue / total_nights if total_nights > 0 else 0
        unique_codes = year_data['IDS_RATE_CODE'].nunique()
        
        with [col1, col2, col3, col4][i % 4]:
            st.metric(
                label=f"**{year}**",
                value=f"${total_revenue:,.0f}",
                delta=f"{total_nights:,.0f} nights | ADR ${avg_adr:.2f}"
            )

    # ------------------------------
    # Chart 1: Top 10 Revenue Codes by Year
    # ------------------------------
    st.header("🏆 Top 10 Rate Codes by Room Revenue")
    
    # Prepare data for grouped bar chart
    top_codes_by_year = {}
    for year in selected_years:
        year_df = filtered_df[filtered_df['Year'] == year].copy()
        top10 = year_df.nlargest(10, 'Room Revenue')[
            ['IDS_RATE_CODE', 'Room Revenue']
        ]
        top_codes_by_year[year] = top10
    
    # Combine for plotting
    plot_data = pd.concat([
        df.assign(Year=year) for year, df in top_codes_by_year.items()
    ])
    
    fig1, ax1 = plt.subplots(figsize=(14, 8))
    sns.barplot(
        data=plot_data,
        x='Room Revenue',
        y='IDS_RATE_CODE',
        hue='Year',
        palette='viridis',
        ax=ax1
    )
    ax1.set_title('Top 10 Rate Codes by Revenue (Across Selected Years)', fontsize=16)
    ax1.set_xlabel('Room Revenue ($)', fontsize=12)
    ax1.set_ylabel('Rate Code', fontsize=12)
    ax1.legend(title='Year')
    plt.tight_layout()
    st.pyplot(fig1)

    # ------------------------------
    # Chart 2: ADR Trend for Top Volume Codes
    # ------------------------------
    st.header("📈 ADR Evolution – Top Volume Drivers")
    
    # Identify top 5 codes by total nights across all selected years
    total_nights_by_code = filtered_df.groupby('IDS_RATE_CODE')['Room Nights'].sum().nlargest(5).index.tolist()
    trend_data = filtered_df[filtered_df['IDS_RATE_CODE'].isin(total_nights_by_code)]
    
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    sns.lineplot(
        data=trend_data,
        x='Year',
        y='Daily AVG',
        hue='IDS_RATE_CODE',
        marker='o',
        linewidth=2.5,
        ax=ax2
    )
    ax2.set_title('ADR Trends for Top 5 Volume Rate Codes', fontsize=16)
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('Average Daily Rate ($)', fontsize=12)
    ax2.legend(title='Rate Code', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    st.pyplot(fig2)

    # ------------------------------
    # Chart 3: Revenue Share by Segment
    # ------------------------------
    st.header("🥧 Revenue Share by Rate Code Segment")
    
    # Define segment mapping (customize as needed)
    def map_segment(code):
        code = str(code).upper()
        if code in ['SBOOK', 'LEXP']:
            return 'OTA'
        elif code == 'RACK':
            return 'Rack'
        elif code.startswith(('SCPM', 'SRTL', 'SCR', 'SCC')):
            return 'Corporate'
        elif code.startswith(('LPROMO', 'LOPQ', 'SAPR', 'SOPM', 'SP')):
            return 'Promo/Package'
        elif code == 'GROUP~':
            return 'Group'
        else:
            return 'Other'
    
    filtered_df['Segment'] = filtered_df['IDS_RATE_CODE'].apply(map_segment)
    
    # Create pie charts for each year side-by-side
    years_for_pie = selected_years if len(selected_years) <= 3 else selected_years[:3]
    fig3, axes = plt.subplots(1, len(years_for_pie), figsize=(6*len(years_for_pie), 6))
    if len(years_for_pie) == 1:
        axes = [axes]
    
    for ax, year in zip(axes, years_for_pie):
        year_segment = filtered_df[filtered_df['Year'] == year].groupby('Segment')['Room Revenue'].sum()
        ax.pie(
            year_segment.values,
            labels=year_segment.index,
            autopct='%1.1f%%',
            startangle=90,
            colors=sns.color_palette('pastel')
        )
        ax.set_title(f'{year} Revenue Share', fontsize=14)
    
    plt.tight_layout()
    st.pyplot(fig3)

    # ------------------------------
    # Chart 4: Heatmap of Rate Code Presence
    # ------------------------------
    st.header("🔥 Rate Code Longevity Heatmap")
    
    # Create presence matrix (1 if revenue > 0)
    presence_df = filtered_df.pivot_table(
        index='IDS_RATE_CODE',
        columns='Year',
        values='Room Revenue',
        aggfunc='sum',
        fill_value=0
    )
    presence_matrix = (presence_df > 0).astype(int)
    
    # Sort by total revenue
    total_rev_by_code = filtered_df.groupby('IDS_RATE_CODE')['Room Revenue'].sum().sort_values(ascending=False)
    presence_matrix = presence_matrix.loc[total_rev_by_code.index]
    
    # Limit to top 30 codes for readability
    top_n = 30
    if len(presence_matrix) > top_n:
        presence_matrix = presence_matrix.head(top_n)
    
    fig4, ax4 = plt.subplots(figsize=(10, 12))
    sns.heatmap(
        presence_matrix,
        annot=True,
        fmt='d',
        cmap='RdYlGn',
        cbar_kws={'label': 'Present (1) / Absent (0)'},
        linewidths=0.5,
        ax=ax4
    )
    ax4.set_title('Rate Code Presence by Year (Top 30 by Total Revenue)', fontsize=16)
    ax4.set_xlabel('Year', fontsize=12)
    ax4.set_ylabel('Rate Code', fontsize=12)
    plt.tight_layout()
    st.pyplot(fig4)

    # ------------------------------
    # Chart 5: Pareto Analysis (Cumulative Revenue)
    # ------------------------------
    st.header("📐 Pareto Analysis – Revenue Concentration")
    
    year_choice = st.selectbox("Select Year for Pareto Chart", selected_years, index=0)
    pareto_df = filtered_df[filtered_df['Year'] == year_choice].copy()
    pareto_df = pareto_df.sort_values('Room Revenue', ascending=False)
    pareto_df['Cumulative Revenue'] = pareto_df['Room Revenue'].cumsum()
    pareto_df['Cumulative %'] = 100 * pareto_df['Cumulative Revenue'] / pareto_df['Room Revenue'].sum()
    pareto_df['Code Rank'] = range(1, len(pareto_df) + 1)
    
    fig5, ax5 = plt.subplots(figsize=(12, 6))
    # Bar chart
    bars = ax5.bar(
        pareto_df['Code Rank'],
        pareto_df['Room Revenue'],
        color='steelblue',
        label='Revenue per Code'
    )
    ax5.set_xlabel('Rate Code Rank (by Revenue)', fontsize=12)
    ax5.set_ylabel('Room Revenue ($)', fontsize=12)
    ax5.set_title(f'Pareto Chart – {year_choice} Revenue Distribution', fontsize=16)
    
    # Line chart on secondary axis
    ax5b = ax5.twinx()
    ax5b.plot(
        pareto_df['Code Rank'],
        pareto_df['Cumulative %'],
        color='darkorange',
        marker='o',
        linewidth=2,
        label='Cumulative %'
    )
    ax5b.set_ylabel('Cumulative % of Total Revenue', fontsize=12)
    ax5b.set_ylim(0, 100)
    
    # Add reference line at 80%
    ax5b.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='80% threshold')
    
    # Combine legends
    lines1, labels1 = ax5.get_legend_handles_labels()
    lines2, labels2 = ax5b.get_legend_handles_labels()
    ax5.legend(lines1 + lines2, labels1 + labels2, loc='center right')
    
    plt.tight_layout()
    st.pyplot(fig5)

    # ------------------------------
    # Raw Data Explorer (Optional)
    # ------------------------------
    with st.expander("🔍 View Raw Data"):
        st.dataframe(filtered_df.sort_values(['Year', 'Room Revenue'], ascending=[True, False]))

    # ------------------------------
    # Download Filtered Data
    # ------------------------------
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name='filtered_rate_code_data.csv',
        mime='text/csv'
    )

if __name__ == "__main__":
    main()