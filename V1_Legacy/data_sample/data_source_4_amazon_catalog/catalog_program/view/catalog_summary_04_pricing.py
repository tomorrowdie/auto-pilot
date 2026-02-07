# catalog_summary_04_pricing.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =====================================================================
# Configuration Section - Edit these values to customize the component
# =====================================================================

# Component title
COMPONENT_TITLE = "Pricing & Profitability"
COMPONENT_TITLE_CN = "定價與盈利能力"

# Rank categories to display in tables
RANK_CATEGORIES = ['#1-10', '#11-30', '#31-50', '#51-100', '#101-150', '#151-200', '#201-300', '#301+']

# Rank columns for different groups
ADS_RANK_COLUMN = 'Ad Rank'
ORGANIC_RANK_COLUMN = 'Organic Rank'
COMBINED_RANK_COLUMN = 'Sales Rank (ALL)'

# Possible price column names
PRICE_COLUMNS = ['Price US$', 'Price US', 'Average Price US$', 'Price USD', 'Price', 'PriceUS']

# Possible fee column names
FEE_COLUMNS = ['Fees US$', 'Fees US', 'Average Fees US$', 'Fees USD', 'Fees', 'FeesUS']

# Metrics columns to display in the pricing table
PRICING_METRICS_COLS = [
    'Catalog Rank',
    'Average Price',
    'Average Fee',
    'Average Profit',
    'Count',
    'Std Dev',
    '25%',
    '50%',
    '75%',
    'Max'
]


# =====================================================================


def display_pricing(df_combined, df_ads, df_organic):
    """
    Display pricing and profitability metrics

    Parameters:
    - df_combined: Combined dataframe with all products
    - df_ads: Dataframe containing only ads products
    - df_organic: Dataframe containing only organic products
    """
    st.subheader(f"{COMPONENT_TITLE} / {COMPONENT_TITLE_CN}")

    # Ensure price and fee columns are consistent across all dataframes
    df_combined, price_col_combined, fee_col_combined = prepare_dataframe_for_pricing(df_combined, "Combined")

    if df_ads is not None and not df_ads.empty:
        df_ads, price_col_ads, fee_col_ads = prepare_dataframe_for_pricing(df_ads, "Ads")
    else:
        price_col_ads, fee_col_ads = None, None

    if df_organic is not None and not df_organic.empty:
        df_organic, price_col_organic, fee_col_organic = prepare_dataframe_for_pricing(df_organic, "Organic")
    else:
        price_col_organic, fee_col_organic = None, None

    # Create tabs for the three different groups
    group_tabs = st.tabs(["Ads Group", "Organic Group", "Combined Group"])

    with group_tabs[0]:  # Ads Group
        if df_ads is not None and not df_ads.empty:
            display_pricing_metrics(df_ads, "Ads", rank_column=ADS_RANK_COLUMN,
                                    price_column=price_col_ads, fee_column=fee_col_ads)
        else:
            st.info("No Ads data available")

    with group_tabs[1]:  # Organic Group
        if df_organic is not None and not df_organic.empty:
            display_pricing_metrics(df_organic, "Organic", rank_column=ORGANIC_RANK_COLUMN,
                                    price_column=price_col_organic, fee_column=fee_col_organic)
        else:
            st.info("No Organic data available")

    with group_tabs[2]:  # Combined Group
        display_pricing_metrics(df_combined, "Combined", rank_column=COMBINED_RANK_COLUMN,
                                price_column=price_col_combined, fee_column=fee_col_combined)


def prepare_dataframe_for_pricing(df, group_name):
    """
    Prepare dataframe for pricing analysis by identifying or creating price and fee columns
    Returns the dataframe and the names of the price and fee columns
    """
    # Make a copy to avoid modifying the original
    df = df.copy()

    # Check for price columns with various possible names
    price_column = None
    for col in PRICE_COLUMNS:
        if col in df.columns:
            price_column = col
            break

    # Check for fee columns with various possible names
    fee_column = None
    for col in FEE_COLUMNS:
        if col in df.columns:
            fee_column = col
            break

    # If price column is still not found, look for any column containing "price" (case insensitive)
    if not price_column:
        price_candidates = [col for col in df.columns if 'price' in col.lower()]
        if price_candidates:
            price_column = price_candidates[0]

    # If fee column is still not found, look for any column containing "fee" (case insensitive)
    if not fee_column:
        fee_candidates = [col for col in df.columns if 'fee' in col.lower()]
        if fee_candidates:
            fee_column = fee_candidates[0]

    # As a last resort, create placeholder columns
    if not price_column:
        if 'Price_Placeholder' not in df.columns:
            df['Price_Placeholder'] = 20  # Default placeholder value
        price_column = 'Price_Placeholder'

    if not fee_column:
        if 'Fee_Placeholder' not in df.columns:
            df['Fee_Placeholder'] = 5  # Default placeholder value
        fee_column = 'Fee_Placeholder'

    return df, price_column, fee_column


def display_pricing_metrics(df, group_name, rank_column, price_column, fee_column):
    """
    Display pricing and profitability metrics for a specific group
    """
    try:
        # Check if price and fee columns were provided, if not, try to detect them again
        if not price_column or not fee_column:
            df, price_column, fee_column = prepare_dataframe_for_pricing(df, group_name)

        # Calculate metrics for each rank category
        metrics_data = []

        for rank_category in RANK_CATEGORIES:
            row_data = [rank_category]

            # Get min and max rank from category
            min_rank, max_rank = get_rank_range(rank_category)

            # Get data for this rank range
            category_data = df[(df[rank_column] >= min_rank) & (df[rank_column] <= max_rank)]

            if len(category_data) > 0:
                # Clean and get numerical data
                category_data['Price_Clean'] = pd.to_numeric(
                    category_data[price_column].astype(str).str.replace('[\$,]', '', regex=True),
                    errors='coerce'
                )

                category_data['Fee_Clean'] = pd.to_numeric(
                    category_data[fee_column].astype(str).str.replace('[\$,]', '', regex=True),
                    errors='coerce'
                )

                # Calculate metrics
                avg_price = category_data['Price_Clean'].mean()
                avg_fee = category_data['Fee_Clean'].mean()
                avg_margin = avg_price - avg_fee
                count = len(category_data)
                std_dev = category_data['Price_Clean'].std()
                percentile_25 = category_data['Price_Clean'].quantile(0.25)
                percentile_50 = category_data['Price_Clean'].quantile(0.5)  # median
                percentile_75 = category_data['Price_Clean'].quantile(0.75)
                max_price = category_data['Price_Clean'].max()

                # Format and add to row data
                row_data.extend([
                    f"${avg_price:.2f}" if not pd.isna(avg_price) else '',
                    f"${avg_fee:.2f}" if not pd.isna(avg_fee) else '',
                    f"${avg_margin:.2f}" if not pd.isna(avg_margin) else '',
                    f"{count}",
                    f"${std_dev:.2f}" if not pd.isna(std_dev) else '',
                    f"${percentile_25:.2f}" if not pd.isna(percentile_25) else '',
                    f"${percentile_50:.2f}" if not pd.isna(percentile_50) else '',
                    f"${percentile_75:.2f}" if not pd.isna(percentile_75) else '',
                    f"${max_price:.2f}" if not pd.isna(max_price) else ''
                ])
            else:
                # If no data for this category, add empty values
                row_data.extend([''] * (len(PRICING_METRICS_COLS) - 1))

            metrics_data.append(row_data)

        # Create the DataFrame
        metrics_df = pd.DataFrame(metrics_data, columns=PRICING_METRICS_COLS)

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
            key=f"pricing_metrics_table_{group_name}"  # Unique key for each table
        )

        # Show price distribution visualization
        if len(category_data) > 0:
            st.subheader(f"Price Distribution for {group_name} Products")
            display_price_distribution(df, price_column)

        # Show sample calculation for transparency in a collapsible section
        with st.expander(f"How are {group_name} pricing calculations performed?"):
            st.write(f"Sample calculation for {group_name} group, #1-10 range:")
            top10_data = df[(df[rank_column] >= 1) & (df[rank_column] <= 10)]
            st.write(f"Number of products in range: {len(top10_data)}")

            if len(top10_data) > 0:
                st.write(f"Rank column used: {rank_column}")
                st.write(f"Price column used: {price_column}")
                st.write(f"Fee column used: {fee_column}")
                st.write(f"Rank values in this range: {sorted(top10_data[rank_column].tolist())}")

                # Show price data if available
                clean_prices = pd.to_numeric(
                    top10_data[price_column].astype(str).str.replace('[\$,]', '', regex=True),
                    errors='coerce'
                )
                st.write(f"Raw {price_column} values: {clean_prices.tolist()}")
                st.write(f"Average Price: ${clean_prices.mean():.2f}")

                # Show fee data if available
                clean_fees = pd.to_numeric(
                    top10_data[fee_column].astype(str).str.replace('[\$,]', '', regex=True),
                    errors='coerce'
                )
                st.write(f"Raw {fee_column} values: {clean_fees.tolist()}")
                st.write(f"Average Fee: ${clean_fees.mean():.2f}")

                # Calculate and show margin
                st.write(f"Average Gross Profit Margin: ${clean_prices.mean() - clean_fees.mean():.2f}")
            else:
                st.write("No data in this rank range")

    except Exception as e:
        st.error(f"Error displaying pricing metrics for {group_name}: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def display_price_distribution(df, price_column):
    """Display a histogram of price distribution"""
    try:
        # Clean price data
        price_data = pd.to_numeric(
            df[price_column].astype(str).str.replace('[\$,]', '', regex=True),
            errors='coerce'
        ).dropna()

        if len(price_data) == 0:
            st.info("No valid price data available for visualization")
            return

        # Filter out extreme outliers for better visualization (95th percentile)
        max_price = price_data.quantile(0.95)
        filtered_prices = price_data[price_data <= max_price]

        # Create histogram with Plotly
        fig = px.histogram(
            filtered_prices,
            nbins=30,
            title=f'Price Distribution (filtered to 95th percentile: ${max_price:.2f})',
            labels={'value': 'Price ($)'},
            opacity=0.8,
            color_discrete_sequence=['#3498db']  # Blue bars
        )

        # Add density line
        fig.add_trace(
            go.Scatter(
                x=filtered_prices.sort_values(),
                y=filtered_prices.value_counts(normalize=True, bins=30).sort_index(),
                mode='lines',
                name='Density',
                line=dict(color='#e74c3c', width=2)  # Red line
            )
        )

        fig.update_layout(
            xaxis_title='Price ($)',
            yaxis_title='Count',
            height=400,
            margin=dict(l=40, r=40, t=50, b=40),
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display key price statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average Price", f"${price_data.mean():.2f}")
        with col2:
            st.metric("Median Price", f"${price_data.median():.2f}")
        with col3:
            st.metric("Min Price", f"${price_data.min():.2f}")
        with col4:
            st.metric("Max Price", f"${price_data.max():.2f}")

    except Exception as e:
        st.error(f"Error displaying price distribution: {str(e)}")


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