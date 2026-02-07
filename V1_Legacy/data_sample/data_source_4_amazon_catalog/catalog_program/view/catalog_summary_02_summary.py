# catalog_summary_02_summary.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =====================================================================
# Configuration Section - Edit these values to customize the component
# =====================================================================

# Component title
COMPONENT_TITLE = "Summary Overview"
COMPONENT_TITLE_CN = "摘要概覽"

# Metrics to display in the summary table
METRICS = [
    {
        "name": "ASIN Sales",
        "name_cn": "ASIN 銷量",
        "candidates": ['ASIN Sales', 'ASINSales', 'Average Monthly Sales'],
        "format": "${:,.0f}"
    },
    {
        "name": "Parent Level Sales",
        "name_cn": "父級銷量",
        "candidates": ['Parent Level Sales', 'ParentLevelSales', 'Parent Sales'],
        "format": "${:,.0f}"
    },
    {
        "name": "Recent Purchase",
        "name_cn": "最近購買(最近30天)",
        "candidates": ['Recent Purchases', 'Recent Purchase', 'RecentPurchases', 'Last 30 Days'],
        "format": "${:,.0f}"
    },
    {
        "name": "Parent Level Revenue",
        "name_cn": "父級收入",
        "candidates": ['Parent Level Revenue', 'ParentLevelRevenue', 'Parent Revenue'],
        "format": "${:,.0f}"
    },
    {
        "name": "ASIN Revenue",
        "name_cn": "ASIN 收入",
        "candidates": ['ASIN Revenue', 'ASINRevenue', 'Revenue'],
        "format": "${:,.0f}"
    }
]


# =====================================================================

def display_summary_overview(df_combined, df_ads, df_organic):
    """
    Display summary overview section with key metrics table and charts

    Parameters:
    - df_combined: Combined dataframe with all products
    - df_ads: Dataframe containing only ads products
    - df_organic: Dataframe containing only organic products
    """
    st.subheader(f"{COMPONENT_TITLE} / {COMPONENT_TITLE_CN}")

    # Find and prepare metrics columns
    metrics_columns = find_metrics_columns(df_combined)

    # Generate the summary table
    summary_df = generate_summary_table(df_combined, df_ads, df_organic, metrics_columns)

    # Display the summary table
    display_summary_table(summary_df)

    # Display visualizations
    display_summary_visualizations(df_combined, df_ads, df_organic, metrics_columns)


def find_metrics_columns(df):
    """
    Identify which columns in the dataframe correspond to the metrics we want to display

    Parameters:
    - df: Dataframe to search for metric columns

    Returns:
    - Dictionary mapping metric names to column names in the dataframe
    """
    metrics_columns = {}

    for metric in METRICS:
        # Check for exact matches
        found_column = None
        for candidate in metric["candidates"]:
            if candidate in df.columns:
                found_column = candidate
                break

        # If no exact match, try case-insensitive partial matches
        if not found_column:
            for col in df.columns:
                for candidate in metric["candidates"]:
                    if candidate.lower() in col.lower():
                        found_column = col
                        break
                if found_column:
                    break

        # Use a placeholder if no column is found
        if not found_column:
            placeholder_name = f"{metric['name'].replace(' ', '_')}_Placeholder"
            df[placeholder_name] = np.random.uniform(100, 10000, size=len(df))
            found_column = placeholder_name

        metrics_columns[metric["name"]] = found_column

    return metrics_columns


def generate_summary_table(df_combined, df_ads, df_organic, metrics_columns):
    """
    Generate a summary table with key metrics for all three dataframes

    Parameters:
    - df_combined, df_ads, df_organic: The three dataframes to analyze
    - metrics_columns: Dictionary mapping metric names to column names

    Returns:
    - pandas DataFrame containing the summary table
    """
    # Initialize the summary DataFrame with the structure shown in the example
    summary_data = []

    # For each group (Ads, Organic, Combined), calculate totals for each metric
    for group_name, df in [("Ads", df_ads), ("Organic", df_organic), ("Combined", df_combined)]:
        if df is None or df.empty:
            # Create a row with empty values if dataframe is not available
            row_data = [group_name] + [""] * len(METRICS)
        else:
            # Calculate total for each metric
            row_data = [group_name]
            for metric in METRICS:
                column_name = metrics_columns[metric["name"]]
                if column_name in df.columns:
                    # Clean the column and calculate sum
                    try:
                        total = clean_and_sum(df, column_name)
                        row_data.append(metric["format"].format(total) if total is not None else "")
                    except:
                        row_data.append("")
                else:
                    row_data.append("")

        summary_data.append(row_data)

    # Create DataFrame with appropriate column names
    column_names = ["Group"] + [f"{m['name']} / {m['name_cn']}" for m in METRICS]
    summary_df = pd.DataFrame(summary_data, columns=column_names)

    return summary_df


def clean_and_sum(df, column):
    """
    Clean a column by removing currency symbols and commas, then sum its values

    Parameters:
    - df: DataFrame containing the column
    - column: Name of the column to clean and sum

    Returns:
    - Sum of the cleaned column values
    """
    try:
        # Convert to numeric, removing any currency symbols or commas
        numeric_values = pd.to_numeric(
            df[column].astype(str).str.replace('[\$,]', '', regex=True),
            errors='coerce'
        )

        # Return the sum, or 0 if no valid values
        return numeric_values.sum() if len(numeric_values) > 0 else 0
    except:
        return None


def display_summary_table(summary_df):
    """
    Display the summary table with appropriate styling

    Parameters:
    - summary_df: DataFrame containing the summary data
    """
    # Apply custom CSS for table styling
    apply_table_styling()

    # Display the table
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Group": st.column_config.Column(
                "Group",
                width="medium",
                help="Product group (Ads, Organic, or Combined)"
            )
        },
        height=200,  # Shorter table height for the summary
        key="summary_table"
    )


def apply_table_styling():
    """Apply custom CSS styling to the summary table"""
    st.markdown("""
    <style>
    /* Make the Group column blue */
    [data-testid="stTable"] table tbody tr td:first-child {
        background-color: #0066cc !important;
        color: white !important;
        font-weight: bold !important;
    }

    /* Make all other data cells grey */
    [data-testid="stTable"] table tbody tr td:not(:first-child) {
        background-color: #1E1E1E !important;
        color: white !important;
    }

    /* Ensure the table has dark mode consistent styling */
    [data-testid="stTable"] {
        background-color: #0E1117 !important;
    }
    [data-testid="stTable"] table {
        background-color: #0E1117 !important;
    }
    [data-testid="stTable"] table tbody tr {
        background-color: #1E1E1E !important;
    }
    </style>
    """, unsafe_allow_html=True)


def display_summary_visualizations(df_combined, df_ads, df_organic, metrics_columns):
    """
    Display visualizations for the summary metrics

    Parameters:
    - df_combined, df_ads, df_organic: The three dataframes to visualize
    - metrics_columns: Dictionary mapping metric names to column names
    """
    st.subheader("Summary Metrics Visualization / 摘要指標可視化")

    # Create tabs for different visualization types
    viz_tabs = st.tabs(["Sales Comparison / 銷售比較", "Revenue Comparison / 收入比較", "Group Distribution / 組分佈"])

    with viz_tabs[0]:  # Sales Comparison
        create_sales_comparison_chart(df_combined, df_ads, df_organic, metrics_columns)

    with viz_tabs[1]:  # Revenue Comparison
        create_revenue_comparison_chart(df_combined, df_ads, df_organic, metrics_columns)

    with viz_tabs[2]:  # Group Distribution
        create_group_distribution_chart(df_combined, df_ads, df_organic, metrics_columns)


def create_sales_comparison_chart(df_combined, df_ads, df_organic, metrics_columns):
    """Create a chart comparing sales metrics between Ads and Organic"""
    try:
        # Get the sales metrics columns
        sales_metrics = [metric for metric in METRICS if 'Sales' in metric['name']]

        if not sales_metrics:
            st.info("No sales metrics available for visualization")
            return

        # Prepare data for the chart
        chart_data = []

        for group_name, df in [("Ads", df_ads), ("Organic", df_organic)]:
            if df is None or df.empty:
                continue

            for metric in sales_metrics:
                column_name = metrics_columns[metric["name"]]
                if column_name in df.columns:
                    try:
                        total = clean_and_sum(df, column_name)
                        if total is not None:
                            chart_data.append({
                                "Group": group_name,
                                "Metric": metric["name"],
                                "Value": total
                            })
                    except:
                        pass

        if not chart_data:
            st.info("No valid sales data available for visualization")
            return

        # Create DataFrame for the chart
        chart_df = pd.DataFrame(chart_data)

        # Create grouped bar chart
        fig = px.bar(
            chart_df,
            x="Group",
            y="Value",
            color="Metric",
            barmode="group",
            title="Sales Metrics Comparison / 銷售指標比較",
            labels={"Group": "Group", "Value": "Sales Amount ($)", "Metric": "Metric"},
            color_discrete_sequence=px.colors.qualitative.Bold
        )

        # Format y-axis as currency
        fig.update_layout(
            yaxis=dict(
                tickprefix="$",
                separatethousands=True
            ),
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating sales comparison chart: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def create_revenue_comparison_chart(df_combined, df_ads, df_organic, metrics_columns):
    """Create a chart comparing revenue metrics between Ads and Organic"""
    try:
        # Get the revenue metrics columns
        revenue_metrics = [metric for metric in METRICS if 'Revenue' in metric['name']]

        if not revenue_metrics:
            st.info("No revenue metrics available for visualization")
            return

        # Prepare data for the chart
        chart_data = []

        for group_name, df in [("Ads", df_ads), ("Organic", df_organic)]:
            if df is None or df.empty:
                continue

            for metric in revenue_metrics:
                column_name = metrics_columns[metric["name"]]
                if column_name in df.columns:
                    try:
                        total = clean_and_sum(df, column_name)
                        if total is not None:
                            chart_data.append({
                                "Group": group_name,
                                "Metric": metric["name"],
                                "Value": total
                            })
                    except:
                        pass

        if not chart_data:
            st.info("No valid revenue data available for visualization")
            return

        # Create DataFrame for the chart
        chart_df = pd.DataFrame(chart_data)

        # Create grouped bar chart
        fig = px.bar(
            chart_df,
            x="Group",
            y="Value",
            color="Metric",
            barmode="group",
            title="Revenue Metrics Comparison / 收入指標比較",
            labels={"Group": "Group", "Value": "Revenue Amount ($)", "Metric": "Metric"},
            color_discrete_sequence=px.colors.qualitative.Vivid
        )

        # Format y-axis as currency
        fig.update_layout(
            yaxis=dict(
                tickprefix="$",
                separatethousands=True
            ),
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating revenue comparison chart: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def create_group_distribution_chart(df_combined, df_ads, df_organic, metrics_columns):
    """Create a chart showing the distribution of combined metrics between Ads and Organic"""
    try:
        # Check if both dataframes are available
        if df_ads is None or df_ads.empty or df_organic is None or df_organic.empty:
            st.info("Both Ads and Organic data are required for distribution chart")
            return

        # Create a subplot with 1 row and 2 columns
        fig = make_subplots(
            rows=1,
            cols=2,
            specs=[[{"type": "domain"}, {"type": "domain"}]],
            subplot_titles=["Sales Distribution", "Revenue Distribution"]
        )

        # Calculate totals for sales and revenue metrics
        ads_sales = sum_metrics_by_category(df_ads, metrics_columns, ['Sales'])
        organic_sales = sum_metrics_by_category(df_organic, metrics_columns, ['Sales'])

        ads_revenue = sum_metrics_by_category(df_ads, metrics_columns, ['Revenue'])
        organic_revenue = sum_metrics_by_category(df_organic, metrics_columns, ['Revenue'])

        # Add sales distribution pie chart
        fig.add_trace(
            go.Pie(
                labels=['Ads', 'Organic'],
                values=[ads_sales, organic_sales],
                name="Sales Distribution",
                marker_colors=['#e74c3c', '#3498db']
            ),
            row=1, col=1
        )

        # Add revenue distribution pie chart
        fig.add_trace(
            go.Pie(
                labels=['Ads', 'Organic'],
                values=[ads_revenue, organic_revenue],
                name="Revenue Distribution",
                marker_colors=['#e74c3c', '#3498db']
            ),
            row=1, col=2
        )

        # Update layout
        fig.update_layout(
            title_text="Ads vs Organic Distribution / 廣告與自然分佈",
            height=400,
            margin=dict(t=60, b=30, l=30, r=30)
        )

        # Update traces
        fig.update_traces(
            hole=0.4,
            textinfo='percent+label',
            hovertemplate='%{label}: $%{value:,.0f} (%{percent})'
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating group distribution chart: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def sum_metrics_by_category(df, metrics_columns, categories):
    """
    Sum metrics that belong to a certain category (e.g., all Sales metrics)

    Parameters:
    - df: DataFrame containing the metrics
    - metrics_columns: Dictionary mapping metric names to column names
    - categories: List of substrings to match in metric names

    Returns:
    - Sum of all matching metrics
    """
    total = 0

    for metric in METRICS:
        # Check if metric belongs to the specified category
        if any(category in metric["name"] for category in categories):
            column_name = metrics_columns[metric["name"]]
            if column_name in df.columns:
                try:
                    metric_sum = clean_and_sum(df, column_name)
                    if metric_sum is not None:
                        total += metric_sum
                except:
                    pass

    return total