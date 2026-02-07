# catalog_summary_01_data_overview.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =====================================================================
# Configuration Section - Edit these values to customize the component
# =====================================================================

# Component title
COMPONENT_TITLE = "Data Overview"
COMPONENT_TITLE_CN = "數據概覽"

# Metric columns configuration
METRICS = [
    {"label": "Total Products", "field": "count", "format": "{:,}"},
    {"label": "Ads Products", "field": "ads_count", "format": "{:,}"},
    {"label": "Organic Products", "field": "organic_count", "format": "{:,}"}
]

# Chart configurations
DISTRIBUTION_TITLE = "Distribution Analysis"
DISTRIBUTION_TITLE_CN = "廣告與自然流量分佈分析"

PIE_CHART_TITLE = "Organic vs Ads Distribution"
PIE_CHART_TITLE_CN = "廣告 vs 自然流量%分佈"
PIE_CHART_CATEGORY_FIELD = "Organic VS Ads"
PIE_CHART_COLORS = {
    "Ads": "#e74c3c",  # Red for Ads
    "Organic": "#3498db"  # Blue for Organic
}

BAR_CHART_TITLE = "Product Distribution by Page Rank"
BAR_CHART_TITLE_CN = "產品按 Page Rank分佈"
BAR_CHART_RANK_FIELD = "Sales Rank (ALL)"
BAR_CHART_RANK_RANGES = [
    {"max": 10, "label": "#1-10"},
    {"min": 11, "max": 30, "label": "#11-30"},
    {"min": 31, "max": 50, "label": "#31-50"},
    {"min": 51, "max": 100, "label": "#51-100"},
    {"min": 101, "max": 150, "label": "#101-150"},
    {"min": 151, "max": 200, "label": "#151-200"},
    {"min": 201, "max": 300, "label": "#201-300"},
    {"min": 301, "max": float('inf'), "label": "#301+"}
]


# =====================================================================


def display_data_overview(df_combined, df_ads, df_organic):
    """
    Display data overview section with key metrics

    Parameters:
    - df_combined: Combined dataframe with all products
    - df_ads: Dataframe containing only ads products
    - df_organic: Dataframe containing only organic products
    """
    st.subheader(f"{COMPONENT_TITLE}")

    # Prepare metrics data
    metrics_data = {
        "count": len(df_combined),
        "ads_count": len(df_ads) if df_ads is not None and not df_ads.empty else 0,
        "organic_count": len(df_organic) if df_organic is not None and not df_organic.empty else 0
    }

    # Calculate percentages
    ads_percent = (metrics_data["ads_count"] / metrics_data["count"] * 100) if metrics_data["count"] > 0 else 0
    organic_percent = (metrics_data["organic_count"] / metrics_data["count"] * 100) if metrics_data["count"] > 0 else 0

    # Create columns for metrics
    metric_columns = st.columns(len(METRICS))

    # Display metrics
    for i, metric in enumerate(METRICS):
        with metric_columns[i]:
            value = metrics_data.get(metric["field"], 0)
            formatted_value = metric["format"].format(value)

            # Add delta for percentage display
            delta = None
            if metric["field"] == "ads_count":
                delta = f"{ads_percent:.1f}%"
            elif metric["field"] == "organic_count":
                delta = f"{organic_percent:.1f}%"

            st.metric(
                label=metric["label"],
                value=formatted_value,
                # delta=delta,
                help=metric.get("help", "")
            )

    # Add a space between metrics and graphs
    st.markdown("---")

    # Display visualizations directly without expanders
    st.subheader(f"{DISTRIBUTION_TITLE} / {DISTRIBUTION_TITLE_CN}")

    # Create two columns for the charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Create Organic vs Ads Distribution chart
        if PIE_CHART_CATEGORY_FIELD in df_combined.columns:
            create_distribution_pie_chart(df_combined)

    with chart_col2:
        # Create Product Distribution by Rank Range chart
        if BAR_CHART_RANK_FIELD in df_combined.columns:
            rank_distribution = create_rank_distribution(df_combined)
            st.plotly_chart(rank_distribution, use_container_width=True)


def create_distribution_pie_chart(df):
    """Create the distribution pie chart with custom colors"""
    # Count values for pie chart
    value_counts = df[PIE_CHART_CATEGORY_FIELD].value_counts().reset_index()
    value_counts.columns = ['Category', 'Count']

    # Create labels and values lists
    labels = value_counts['Category'].tolist()
    values = value_counts['Count'].tolist()

    # Create colors list - explicitly map each category to a color
    colors = []
    for category in labels:
        colors.append(PIE_CHART_COLORS.get(category, "#999999"))  # Default gray if category not found

    # Create pie chart using go.Pie
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=colors,
        textinfo='percent+label',
        textposition='inside'
    )])

    fig.update_layout(
        title_text=f'{PIE_CHART_TITLE} / {PIE_CHART_TITLE_CN}',
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )

    st.plotly_chart(fig, use_container_width=True)


def create_rank_distribution(df):
    """
    Create a chart showing distribution of products by rank range

    Parameters:
    - df: Dataframe containing products with Sales Rank column

    Returns:
    - Plotly figure object
    """
    # Create rank categories based on configuration
    conditions = []
    values = []

    for range_config in BAR_CHART_RANK_RANGES:
        min_val = range_config.get("min", 0)
        max_val = range_config.get("max", float('inf'))
        label = range_config.get("label", "")

        if min_val == 0:  # First category
            condition = (df[BAR_CHART_RANK_FIELD] <= max_val)
        elif max_val == float('inf'):  # Last category
            condition = (df[BAR_CHART_RANK_FIELD] > min_val)
        else:  # Middle categories
            condition = (df[BAR_CHART_RANK_FIELD] > min_val) & (df[BAR_CHART_RANK_FIELD] <= max_val)

        conditions.append(condition)
        values.append(label)

    # Apply categories
    df_rank = df.copy()
    df_rank['Rank Category'] = np.select(conditions, values, default='Other')

    # Count by rank category
    rank_counts = df_rank['Rank Category'].value_counts().sort_index()

    # Create DataFrame for visualization
    rank_data = pd.DataFrame({
        'Rank Range': rank_counts.index,
        'Count': rank_counts.values
    })

    # Define the correct order for rank categories
    correct_order = ['#1-10', '#11-30', '#31-50', '#51-100', '#101-150', '#151-200', '#201-300', '#301+', 'Other']

    # Reindex the DataFrame to ensure correct order
    rank_data['Rank Range'] = pd.Categorical(rank_data['Rank Range'], categories=correct_order, ordered=True)
    rank_data = rank_data.sort_values('Rank Range')

    # Create bar chart
    fig = px.bar(
        rank_data,
        x='Rank Range',
        y='Count',
        title=f'{BAR_CHART_TITLE} / {BAR_CHART_TITLE_CN}',
        text='Count',
        color='Rank Range',
        color_discrete_sequence=px.colors.qualitative.D3
    )

    fig.update_traces(textposition='outside')

    fig.update_layout(
        xaxis_title='Page Rank',
        yaxis_title='Number of Products',
        height=400,
        showlegend=False
    )

    return fig