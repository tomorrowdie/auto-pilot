# catalog_summary_03_sales_revenue.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =====================================================================
# Configuration Section - Edit these values to customize the component
# =====================================================================

# Component title
COMPONENT_TITLE = "Sales & Revenue Metrics"
COMPONENT_TITLE_CN = "銷售與收入指標"

# Rank categories to display in tables
RANK_CATEGORIES = ['#1-10', '#11-30', '#31-50', '#51-100', '#101-150', '#151-200', '#201-300', '#301+']

# Rank columns for different groups
ADS_RANK_COLUMN = 'Ad Rank'
ORGANIC_RANK_COLUMN = 'Organic Rank'
COMBINED_RANK_COLUMN = 'Sales Rank (ALL)'

# Sales metrics to look for in the dataframe
POTENTIAL_METRICS = [
    'Average Monthly Sales', 'Sector Sales Estimate', 'ASIN Sales',
    'Parent Level Sales', 'Recent Purchases', 'Parent Level Revenue',
    'ASIN Revenue', 'Market Volume', 'Price US', 'Fees US',
    'Price US$', 'Fees US$', 'Average Price US$', 'Average Fees US$'
]

# Default metrics to display if none found
DEFAULT_METRICS = [
    'Catalog Rank', 'Average Monthly Sales', 'Sector Sales Estimate',
    'ASIN Sales', 'Parent Level Sales', 'Recent Purchases',
    'Parent Level Revenue', 'ASIN Revenue', 'Market Volume'
]


# =====================================================================


def display_sales_revenue(df_combined, df_ads, df_organic):
    """
    Display sales and revenue metrics

    Parameters:
    - df_combined: Combined dataframe with all products
    - df_ads: Dataframe containing only ads products
    - df_organic: Dataframe containing only organic products
    """
    st.subheader(f"{COMPONENT_TITLE} / {COMPONENT_TITLE_CN}")

    # Create tabs for the three different groups
    group_tabs = st.tabs(["Ads Group", "Organic Group", "Combined Group"])

    with group_tabs[0]:  # Ads Group
        if df_ads is not None and not df_ads.empty:
            display_sales_metrics_table(df_ads, "Ads", rank_column=ADS_RANK_COLUMN)
        else:
            st.info("No Ads data available")

    with group_tabs[1]:  # Organic Group
        if df_organic is not None and not df_organic.empty:
            display_sales_metrics_table(df_organic, "Organic", rank_column=ORGANIC_RANK_COLUMN)
        else:
            st.info("No Organic data available")

    with group_tabs[2]:  # Combined Group
        display_sales_metrics_table(df_combined, "Combined", rank_column=COMBINED_RANK_COLUMN)


def display_sales_metrics_table(df, group_name, rank_column):
    """
    Display sales metrics table for a specific group using the appropriate rank column
    """
    try:
        # Create the metrics columns based on available data
        metrics_cols = ['Catalog Rank']
        available_metrics = []

        # Check which sales metrics columns are available in the dataframe
        for metric in POTENTIAL_METRICS:
            if metric in df.columns:
                metrics_cols.append(metric)
                available_metrics.append(metric)

        # If no metrics columns found, use default set and search for similar columns
        if len(available_metrics) == 0:
            metrics_cols = DEFAULT_METRICS
            available_metrics = [col for col in df.columns if any(metric in col for metric in
                                                                  ['Sales', 'Revenue', 'Purchases', 'Price', 'Volume',
                                                                   'Fees'])]

        # Ensure the rank column exists
        if rank_column not in df.columns:
            st.warning(
                f"Rank column '{rank_column}' not found for {group_name} group. Using '{COMBINED_RANK_COLUMN}' instead.")
            rank_column = COMBINED_RANK_COLUMN if COMBINED_RANK_COLUMN in df.columns else None

            if rank_column is None:
                st.error("No appropriate rank column found. Cannot calculate rank-based metrics.")
                return

        # Calculate metrics for each rank category
        metrics_data = []

        for rank_category in RANK_CATEGORIES:
            row_data = [rank_category]

            # Get min and max rank from category
            min_rank, max_rank = get_rank_range(rank_category)

            # Get data for this rank range
            category_data = df[(df[rank_column] >= min_rank) & (df[rank_column] <= max_rank)]

            # Calculate metrics for each available column
            for metric in available_metrics:
                if metric in df.columns:
                    try:
                        if len(category_data) > 0:
                            avg_value = clean_and_compute_average(category_data, metric)
                            # Special formatting for price and fees columns
                            if 'Price' in metric or 'Fees' in metric:
                                row_data.append(f"${avg_value:.2f}" if avg_value is not None else '')
                            else:
                                row_data.append(format_metric_value(avg_value, metric))
                        else:
                            row_data.append('')
                    except Exception as e:
                        st.error(f"Error calculating {metric} for {rank_category}: {str(e)}")
                        row_data.append('')
                else:
                    row_data.append('')

            # If row_data doesn't match expected length, pad with empty strings
            while len(row_data) < len(metrics_cols):
                row_data.append('')

            metrics_data.append(row_data)

        # Create the DataFrame
        metrics_df = pd.DataFrame(metrics_data, columns=metrics_cols)

        # Apply custom CSS for table styling
        apply_table_styling()

        # Display the table without the index column
        st.dataframe(
            metrics_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Catalog Rank": st.column_config.Column(
                    "Catalog Rank",
                    width="medium",
                    help=f"Ranking group based on {rank_column}"
                )
            },
            height=400,  # Make the table taller
            key=f"metrics_table_{group_name}"  # Unique key for each table
        )

        # Show sample calculation for transparency in a collapsible section
        with st.expander(f"How are {group_name} calculations performed?"):
            if len(available_metrics) > 0 and available_metrics[0] in df.columns:
                sample_metric = available_metrics[0]
                st.write(f"Sample calculation for {group_name} group, #1-10 range, {sample_metric}:")
                top10_data = df[(df[rank_column] >= 1) & (df[rank_column] <= 10)]
                st.write(f"Number of products in range: {len(top10_data)}")

                if len(top10_data) > 0:
                    clean_values = pd.to_numeric(
                        top10_data[sample_metric].astype(str).str.replace('[\$,]', '', regex=True), errors='coerce')
                    st.write(f"Rank column used: {rank_column}")
                    st.write(f"Rank values in this range: {sorted(top10_data[rank_column].tolist())}")
                    st.write(f"Raw {sample_metric} values: {clean_values.tolist()}")
                    st.write(f"Average: {clean_values.mean():.2f}")
                else:
                    st.write("No data in this rank range")

    except Exception as e:
        st.error(f"Error displaying sales metrics for {group_name}: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def apply_table_styling():
    """Apply custom CSS styling to the metrics table"""
    st.markdown("""
    <style>
    /* Make the Catalog Rank column blue */
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


def clean_and_compute_average(df, column):
    """Clean a column and compute its average value"""
    if column not in df.columns:
        return None

    try:
        # Convert to numeric, removing any currency symbols or commas
        numeric_values = pd.to_numeric(
            df[column].astype(str).str.replace('[\$,]', '', regex=True),
            errors='coerce'
        )

        # Drop NaN values before calculating mean
        numeric_values = numeric_values.dropna()

        # Return the average, or 0 if no valid values
        return numeric_values.mean() if len(numeric_values) > 0 else 0
    except:
        return None


def format_metric_value(value, metric):
    """Format the metric value appropriately based on the type of metric"""
    if value is None:
        return ''

    # Apply appropriate formatting based on the metric type
    if 'Price' in metric or 'Revenue' in metric:
        return f"${value:.2f}"
    elif 'Fees' in metric:
        return f"${value:.2f}"
    elif 'Sales' in metric or 'Purchases' in metric or 'Volume' in metric:
        return f"{value:.0f}" if value >= 10 else f"{value:.1f}"
    else:
        return f"{value:.2f}"


def get_rank_range(rank_category):
    """Helper function to get min and max rank from category name"""
    if rank_category == '#1-10':
        return 1, 10
    elif rank_category == '#11-30':
        return 11, 30
    elif rank_category == '#31-50':
        return 31, 50
    elif rank_category == '#51-100':
        return 51, 100
    elif rank_category == '#101-150':
        return 101, 150
    elif rank_category == '#151-200':
        return 151, 200
    elif rank_category == '#201-300':
        return 201, 300
    elif rank_category == '#301+':
        return 301, float('inf')
    else:
        # Default case (shouldn't happen)
        return 0, float('inf')