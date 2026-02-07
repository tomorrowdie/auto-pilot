# catalog_summary_05_product_performance.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =====================================================================
# Configuration Section - Edit these values to customize the component
# =====================================================================

# Component title
COMPONENT_TITLE = "Product Performance"
COMPONENT_TITLE_CN = "產品表現"

# Rank categories to display in tables
RANK_CATEGORIES = ['#1-10', '#11-30', '#31-50', '#51-100', '#101-150', '#151-200', '#201-300', '#301+']

# Rank columns for different groups
ADS_RANK_COLUMN = 'Ad Rank'
ORGANIC_RANK_COLUMN = 'Organic Rank'
COMBINED_RANK_COLUMN = 'Sales Rank (ALL)'

# Metrics column configurations with Chinese translations
PERFORMANCE_METRICS = [
    {
        "name": "Catalog Rank",
        "name_cn": "目錄排名",
        "width": "medium",
        "help": "Ranking group based on product position"
    },
    {
        "name": "Average BSR",
        "name_cn": "平均銷售排名",
        "candidates": ['BSR', 'Best Sellers Rank', 'BestSellersRank', 'Best Seller Rank'],
        "placeholder": 50000,
        "format": "{:,.0f}"
    },
    {
        "name": "Average Rating",
        "name_cn": "平均評分",
        "candidates": ['Rating', 'Product Rating', 'Star Rating', 'Stars', 'Average Rating'],
        "placeholder": 4.0,
        "format": "{:.1f}"
    },
    {
        "name": "Average Review Count",
        "name_cn": "平均評論數",
        "candidates": ['Review Count', 'Reviews', 'Number of Reviews', 'ReviewCount', 'Total Reviews'],
        "placeholder": 100,
        "format": "{:,.0f}"
    },
    {
        "name": "Review Velocity (reviews/month)",
        "name_cn": "評論增長速度 (每月)",
        "candidates": ['Review Velocity', 'ReviewVelocity', 'Reviews Per Month', 'Monthly Reviews'],
        "placeholder": 5,
        "format": "{:.1f}"
    },
    {
        "name": "Average Number of Images",
        "name_cn": "平均圖片數量",
        "candidates": ['Images', 'Image Count', 'Number of Images', 'ImageCount', 'Product Images'],
        "placeholder": 5,
        "format": "{:.1f}"
    }
]


# =====================================================================


def display_product_performance(df_combined, df_ads, df_organic):
    """
    Display product performance metrics

    Parameters:
    - df_combined: Combined dataframe with all products
    - df_ads: Dataframe containing only ads products
    - df_organic: Dataframe containing only organic products
    """
    st.subheader(f"{COMPONENT_TITLE} / {COMPONENT_TITLE_CN}")

    # Create tabs for the three different groups
    group_tabs = st.tabs(["Ads Group / 廣告組", "Organic Group / 自然組", "Combined Group / 合併組"])

    with group_tabs[0]:  # Ads Group
        if df_ads is not None and not df_ads.empty:
            display_performance_metrics_table(df_ads, "Ads", rank_column=ADS_RANK_COLUMN)
        else:
            st.info("No Ads data available / 沒有廣告數據")

    with group_tabs[1]:  # Organic Group
        if df_organic is not None and not df_organic.empty:
            display_performance_metrics_table(df_organic, "Organic", rank_column=ORGANIC_RANK_COLUMN)
        else:
            st.info("No Organic data available / 沒有自然數據")

    with group_tabs[2]:  # Combined Group
        display_performance_metrics_table(df_combined, "Combined", rank_column=COMBINED_RANK_COLUMN)


def display_performance_metrics_table(df, group_name, rank_column):
    """
    Display product performance metrics table for a specific group
    """
    try:
        # Ensure the rank column exists
        if rank_column not in df.columns:
            st.warning(
                f"Rank column '{rank_column}' not found for {group_name} group. Using '{COMBINED_RANK_COLUMN}' instead.")
            rank_column = COMBINED_RANK_COLUMN if COMBINED_RANK_COLUMN in df.columns else None

            if rank_column is None:
                st.error("No appropriate rank column found. Cannot calculate rank-based metrics.")
                return

        # Find or create required columns in dataframe
        df = prepare_dataframe_for_metrics(df)

        # Calculate metrics for each rank category
        metrics_data = []

        for rank_category in RANK_CATEGORIES:
            row_data = [rank_category]

            # Get min and max rank from category
            min_rank, max_rank = get_rank_range(rank_category)

            # Get data for this rank range
            category_data = df[(df[rank_column] >= min_rank) & (df[rank_column] <= max_rank)]

            if len(category_data) > 0:
                # Calculate metrics for each performance metric (skipping the first one which is Catalog Rank)
                for metric in PERFORMANCE_METRICS[1:]:
                    # The column to use is stored in df as the metric name with "_Column" suffix
                    column_name = f"{metric['name']}_Column"

                    if column_name in df.columns:
                        metric_value = clean_and_compute_average(category_data, df[column_name].iloc[0])
                        # Format the value
                        if metric_value is not None and not pd.isna(metric_value):
                            row_data.append(metric["format"].format(metric_value))
                        else:
                            row_data.append('')
                    else:
                        row_data.append('')
            else:
                # If no data for this category, add empty values
                row_data.extend([''] * (len(PERFORMANCE_METRICS) - 1))

            metrics_data.append(row_data)

        # Create column names with English and Chinese labels
        column_names = [f"{m['name']} / {m['name_cn']}" for m in PERFORMANCE_METRICS]

        # Create the DataFrame
        metrics_df = pd.DataFrame(metrics_data, columns=column_names)

        # Apply custom CSS for table styling
        apply_table_styling()

        # Display the table without the index column
        st.dataframe(
            metrics_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                f"{PERFORMANCE_METRICS[0]['name']} / {PERFORMANCE_METRICS[0]['name_cn']}": st.column_config.Column(
                    f"{PERFORMANCE_METRICS[0]['name']} / {PERFORMANCE_METRICS[0]['name_cn']}",
                    width="medium",
                    help=f"Ranking group based on {rank_column}"
                )
            },
            height=400,  # Make the table taller
            key=f"performance_metrics_table_{group_name}"  # Unique key for each table
        )

        # Create visualizations of key metrics
        if len(df) > 0:
            create_performance_visualizations(df, group_name)

        # Show sample calculation for transparency in a collapsible section
        with st.expander(
                f"How are {group_name} product performance calculations performed? / {group_name}產品表現計算方式?"):
            st.write(f"Sample calculation for {group_name} group, #1-10 range:")
            top10_data = df[(df[rank_column] >= 1) & (df[rank_column] <= 10)]
            st.write(f"Number of products in range: {len(top10_data)}")

            if len(top10_data) > 0:
                st.write(f"Rank column used: {rank_column}")

                # Show calculations for each metric
                for metric in PERFORMANCE_METRICS[1:]:
                    column_name = f"{metric['name']}_Column"
                    if column_name in df.columns:
                        source_column = df[column_name].iloc[0]
                        st.write(f"{metric['name']} column used: {source_column}")

                        if source_column in top10_data.columns:
                            # For BSR and Review Count, we need to handle comma formatting
                            if 'BSR' in metric['name'] or 'Review Count' in metric['name']:
                                clean_values = pd.to_numeric(
                                    top10_data[source_column].astype(str).str.replace('[,]', '', regex=True),
                                    errors='coerce'
                                )
                            else:
                                clean_values = pd.to_numeric(top10_data[source_column], errors='coerce')

                            if not clean_values.empty:
                                st.write(f"Average {metric['name']}: {metric['format'].format(clean_values.mean())}")
            else:
                st.write("No data in this rank range / 此排名範圍內沒有數據")

    except Exception as e:
        st.error(f"Error displaying product performance metrics for {group_name}: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def prepare_dataframe_for_metrics(df):
    """
    Prepare dataframe for metrics analysis by identifying or creating required columns
    Returns the modified dataframe with identified column names
    """
    # Make a copy to avoid modifying the original
    df = df.copy()

    # For each metric, find the appropriate column or create a placeholder
    for metric in PERFORMANCE_METRICS[1:]:  # Skip the first one which is Catalog Rank
        # Find a matching column from candidates
        found_column = None
        for candidate in metric["candidates"]:
            if candidate in df.columns:
                found_column = candidate
                break

        # If still not found, look for partial matches (case insensitive)
        if not found_column:
            for col in df.columns:
                for candidate in metric["candidates"]:
                    if candidate.lower() in col.lower():
                        found_column = col
                        break
                if found_column:
                    break

        # If not found, create placeholder column
        if not found_column:
            placeholder_name = f"{metric['name'].replace(' ', '')}_Placeholder"
            df[placeholder_name] = metric["placeholder"]
            found_column = placeholder_name

        # Store the column name for this metric
        df[f"{metric['name']}_Column"] = found_column

    return df


def create_performance_visualizations(df, group_name):
    """Create visualizations for key product performance metrics"""
    # Create 2x2 charts for key metrics
    col1, col2 = st.columns(2)

    with col1:
        # BSR Distribution
        bsr_column = df[f"{PERFORMANCE_METRICS[1]['name']}_Column"].iloc[0]
        if bsr_column in df.columns:
            create_bsr_visualization(df, bsr_column)

    with col2:
        # Rating Distribution
        rating_column = df[f"{PERFORMANCE_METRICS[2]['name']}_Column"].iloc[0]
        if rating_column in df.columns:
            create_rating_visualization(df, rating_column)


def create_bsr_visualization(df, bsr_column):
    """Create BSR distribution visualization"""
    try:
        # Clean BSR data
        bsr_data = pd.to_numeric(
            df[bsr_column].astype(str).str.replace('[,]', '', regex=True),
            errors='coerce'
        ).dropna()

        if len(bsr_data) == 0:
            st.info("No valid BSR data available for visualization")
            return

        # Apply log transformation to handle wide BSR range
        log_bsr = np.log10(bsr_data.replace(0, 1))  # Replace 0 with 1 to avoid log(0)

        # Create histogram
        fig = px.histogram(
            log_bsr,
            nbins=20,
            title='BSR Distribution (Log Scale) / 銷售排名分佈 (對數刻度)',
            labels={'value': 'Log10(BSR)'},
            color_discrete_sequence=['#3498db']
        )

        # Add a vertical line for median
        median_log_bsr = log_bsr.median()
        fig.add_vline(x=median_log_bsr, line_dash="dash", line_color="#e74c3c",
                      annotation_text=f"Median: {10 ** median_log_bsr:.0f}")

        fig.update_layout(
            xaxis_title='Log10(BSR)',
            yaxis_title='Count / 數量',
            height=350,
            margin=dict(l=40, r=40, t=50, b=40)
        )

        # Add custom ticks for better readability
        tick_vals = [1, 2, 3, 4, 5, 6]
        tick_text = ['10', '100', '1K', '10K', '100K', '1M']
        fig.update_xaxes(tickvals=tick_vals, ticktext=tick_text)

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating BSR visualization: {str(e)}")


def create_rating_visualization(df, rating_column):
    """Create rating distribution visualization"""
    try:
        # Clean rating data
        rating_data = pd.to_numeric(df[rating_column], errors='coerce').dropna()

        if len(rating_data) == 0:
            st.info("No valid rating data available for visualization")
            return

        # Create histogram
        fig = px.histogram(
            rating_data,
            nbins=10,
            range_x=[1, 5],
            title='Rating Distribution / 評分分佈',
            labels={'value': 'Rating / 評分'},
            color_discrete_sequence=['#2ecc71']
        )

        # Add a vertical line for average
        avg_rating = rating_data.mean()
        fig.add_vline(x=avg_rating, line_dash="dash", line_color="#e74c3c",
                      annotation_text=f"Avg: {avg_rating:.1f}")

        fig.update_layout(
            xaxis_title='Rating / 評分',
            yaxis_title='Count / 數量',
            height=350,
            margin=dict(l=40, r=40, t=50, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating rating visualization: {str(e)}")


def clean_and_compute_average(df, column):
    """Clean a column and compute its average value"""
    if column not in df.columns:
        return None

    try:
        # For BSR and Review Count, we need to handle comma formatting
        if any(bsr_name in column for bsr_name in ['BSR', 'Best Seller']):
            numeric_values = pd.to_numeric(
                df[column].astype(str).str.replace('[,]', '', regex=True),
                errors='coerce'
            )
        elif any(review_name in column for review_name in ['Review Count', 'Reviews']):
            numeric_values = pd.to_numeric(
                df[column].astype(str).str.replace('[,]', '', regex=True),
                errors='coerce'
            )
        else:
            numeric_values = pd.to_numeric(df[column], errors='coerce')

        # Drop NaN values before calculating mean
        numeric_values = numeric_values.dropna()

        # Return the average, or 0 if no valid values
        return numeric_values.mean() if len(numeric_values) > 0 else 0
    except:
        return None


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