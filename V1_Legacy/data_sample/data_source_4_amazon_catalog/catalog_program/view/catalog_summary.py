import streamlit as st
import pandas as pd
import numpy as np


def generate_summary_section(df_combined, df_ads, df_organic):
    """
    Generate the summary section with key metrics for Ads, Organic, and Combined groups
    """
    try:
        # Create a summary dataframe with the structure you specified
        summary_cols = ['Market Volume', 'Market Sales', 'Average Gross Margin', 'Average Rating', 'Top 10 (volume)']
        summary_rows = ['Ads', 'Organic', 'Combined']

        # Create empty dataframe with the right structure
        summary_data = []
        for _ in range(len(summary_rows)):
            summary_data.append([''] * len(summary_cols))

        summary_df = pd.DataFrame(summary_data, columns=summary_cols, index=summary_rows)

        # Display the summary table with styling
        st.dataframe(summary_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating summary section: {str(e)}")


def generate_sales_metrics(df_combined, df_ads=None, df_organic=None):
    """
    Generate sales and revenue metrics table by catalog rank with tabs for different groups
    """
    try:
        # Create tabs for the three different groups
        group_tabs = st.tabs(["Ads Group", "Organic Group", "Combined Group"])

        with group_tabs[0]:  # Ads Group
            if df_ads is not None and not df_ads.empty:
                display_sales_metrics_table(df_ads, "Ads", rank_column='Ad Rank')
            else:
                st.info("No Ads data available")

        with group_tabs[1]:  # Organic Group
            if df_organic is not None and not df_organic.empty:
                display_sales_metrics_table(df_organic, "Organic", rank_column='Organic Rank')
            else:
                st.info("No Organic data available")

        with group_tabs[2]:  # Combined Group
            display_sales_metrics_table(df_combined, "Combined", rank_column='Sales Rank (ALL)')
    except Exception as e:
        st.error(f"Error generating sales metrics: {str(e)}")


def display_sales_metrics_table(df, group_name, rank_column='Sales Rank (ALL)'):
    """
    Display sales metrics table for a specific group using the appropriate rank column
    """
    try:
        # Define the rank buckets - excluding the 'Catalog Insight' row
        rank_categories = ['#1-10', '#11-30', '31-50', '51-100', '101-150', '151-200', '201-300', '301+']

        # Create the metrics columns based on available data
        metrics_cols = ['Catalog Rank']
        available_metrics = []

        # Check which sales metrics columns are available in the dataframe
        potential_metrics = [
            'Average Monthly Sales', 'Sector Sales Estimate', 'ASIN Sales',
            'Parent Level Sales', 'Recent Purchases', 'Parent Level Revenue',
            'ASIN Revenue', 'Market Volume', 'Price US', 'Fees US',
            'Price US$', 'Fees US$', 'Average Price US$', 'Average Fees US$'
        ]

        # Check for columns that exist in the dataframe
        for metric in potential_metrics:
            if metric in df.columns:
                metrics_cols.append(metric)
                available_metrics.append(metric)

        # If no metrics columns found, use default set
        if len(available_metrics) == 0:
            metrics_cols = [
                'Catalog Rank', 'Average Monthly Sales', 'Sector Sales Estimate/Price US$',
                'ASIN Sales', 'Parent Level Sales', 'Recent Purchases',
                'Parent Level Revenue', 'ASIN Revenue', 'Market Volume'
            ]

            # Use existing columns from the dataframe that might match
            available_metrics = [col for col in df.columns if any(metric in col for metric in
                                                                  ['Sales', 'Revenue', 'Purchases', 'Price', 'Volume',
                                                                   'Fees'])]

        # Ensure the rank column exists
        if rank_column not in df.columns:
            st.warning(
                f"Rank column '{rank_column}' not found for {group_name} group. Using 'Sales Rank (ALL)' instead.")
            rank_column = 'Sales Rank (ALL)' if 'Sales Rank (ALL)' in df.columns else None

            if rank_column is None:
                st.error("No appropriate rank column found. Cannot calculate rank-based metrics.")
                return

        # Calculate metrics for each rank category
        metrics_data = []

        for rank_category in rank_categories:
            row_data = [rank_category]

            # Extract rank range from category name
            if rank_category == '#1-10':
                min_rank, max_rank = 1, 10
            elif rank_category == '#11-30':
                min_rank, max_rank = 11, 30
            elif rank_category == '31-50':
                min_rank, max_rank = 31, 50
            elif rank_category == '51-100':
                min_rank, max_rank = 51, 100
            elif rank_category == '101-150':
                min_rank, max_rank = 101, 150
            elif rank_category == '151-200':
                min_rank, max_rank = 151, 200
            elif rank_category == '201-300':
                min_rank, max_rank = 201, 300
            elif rank_category == '301+':
                min_rank, max_rank = 301, float('inf')
            else:
                # Default case (shouldn't happen)
                min_rank, max_rank = 0, float('inf')

            # Get data for this rank range - handling missing ranks
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

        # Apply custom CSS to increase font size and style the table
        st.markdown("""
        <style>
        .metrics-table {
            font-size: 16px !important; 
        }
        .metrics-table th {
            font-weight: bold !important;
            background-color: #4B0082 !important;
            color: white !important;
        }
        .metrics-table tr td:first-child {
            background-color: #4B0082 !important;
            color: white !important;
            font-weight: bold !important;
        }
        .metrics-table tr td {
            background-color: #1E1E1E !important;
            color: white !important;
        }
        .stDataFrame div[data-testid="stTable"] table {
            width: 100% !important;
        }
        .stDataFrame div[data-testid="stTable"] {
            font-size: 16px !important;
        }

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


def categorize_by_rank(df, rank_column='Sales Rank (ALL)'):
    """
    Categorize products into rank buckets based on the specified rank column
    """
    if rank_column not in df.columns:
        return df.copy()

    # Make a copy to avoid modifying the original
    df_copy = df.copy()

    # Create rank category
    conditions = [
        (df_copy[rank_column] <= 10),
        (df_copy[rank_column] > 10) & (df_copy[rank_column] <= 30),
        (df_copy[rank_column] > 30) & (df_copy[rank_column] <= 50),
        (df_copy[rank_column] > 50) & (df_copy[rank_column] <= 100),
        (df_copy[rank_column] > 100) & (df_copy[rank_column] <= 150),
        (df_copy[rank_column] > 150) & (df_copy[rank_column] <= 200),
        (df_copy[rank_column] > 200) & (df_copy[rank_column] <= 300),
        (df_copy[rank_column] > 300)
    ]

    values = ['#1-10', '#11-30', '31-50', '51-100', '101-150', '151-200', '201-300', '301+']

    df_copy['Rank Category'] = np.select(conditions, values, default='Other')

    return df_copy


def prepare_dataframe_for_pricing(df, group_name):
    """
    Prepare dataframe for pricing analysis by identifying or creating price and fee columns
    Returns the dataframe and the names of the price and fee columns
    """
    # Make a copy to avoid modifying the original
    df = df.copy()

    # Check for price columns with various possible names (expanded list)
    price_columns = ['Price US$', 'Price US', 'Average Price US$', 'Price USD', 'Price', 'PriceUS']
    price_column = None
    for col in price_columns:
        if col in df.columns:
            price_column = col
            break

    # Check for fee columns with various possible names (expanded list)
    fee_columns = ['Fees US$', 'Fees US', 'Average Fees US$', 'Fees USD', 'Fees', 'FeesUS']
    fee_column = None
    for col in fee_columns:
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
        # Check if we can use a common price column from another group's dataframe
        if 'Price_Placeholder' not in df.columns:
            # Create a dummy price column with average price of 20 (for demonstration)
            df['Price_Placeholder'] = 20
        price_column = 'Price_Placeholder'

    if not fee_column:
        # Create a dummy fee column with average fee of 5 (for demonstration)
        if 'Fee_Placeholder' not in df.columns:
            df['Fee_Placeholder'] = 5
        fee_column = 'Fee_Placeholder'

    return df, price_column, fee_column


def generate_pricing_profitability(df_combined, df_ads=None, df_organic=None):
    """
    Generate pricing and profitability metrics table with tabs for different groups
    """
    try:
        # Ensure price and fee columns are consistent across all dataframes
        df_combined, price_col_combined, fee_col_combined = prepare_dataframe_for_pricing(df_combined, "Combined")

        if df_ads is not None and not df_ads.empty:
            df_ads, price_col_ads, fee_col_ads = prepare_dataframe_for_pricing(df_ads, "Ads")

        if df_organic is not None and not df_organic.empty:
            df_organic, price_col_organic, fee_col_organic = prepare_dataframe_for_pricing(df_organic, "Organic")

        # Create tabs for the three different groups
        group_tabs = st.tabs(["Ads Group", "Organic Group", "Combined Group"])

        with group_tabs[0]:  # Ads Group
            if df_ads is not None and not df_ads.empty:
                display_pricing_metrics(df_ads, "Ads", rank_column='Ad Rank', price_column=price_col_ads,
                                        fee_column=fee_col_ads)
            else:
                st.info("No Ads data available")

        with group_tabs[1]:  # Organic Group
            if df_organic is not None and not df_organic.empty:
                display_pricing_metrics(df_organic, "Organic", rank_column='Organic Rank',
                                        price_column=price_col_organic, fee_column=fee_col_organic)
            else:
                st.info("No Organic data available")

        with group_tabs[2]:  # Combined Group
            display_pricing_metrics(df_combined, "Combined", rank_column='Sales Rank (ALL)',
                                    price_column=price_col_combined, fee_column=fee_col_combined)
    except Exception as e:
        st.error(f"Error generating pricing metrics: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def display_pricing_metrics(df, group_name, rank_column='Sales Rank (ALL)', price_column=None, fee_column=None):
    """
    Display pricing and profitability metrics for a specific group
    """
    try:
        # Define the rank buckets
        rank_categories = ['#1-10', '#11-30', '31-50', '51-100', '101-150', '151-200', '201-300', '301+']

        # Check if price and fee columns were provided, if not, try to detect them
        if not price_column or not fee_column:
            df, price_column, fee_column = prepare_dataframe_for_pricing(df, group_name)

        # Define the metrics columns
        metrics_cols = [
            'Catalog Rank',
            'Average Price',
            'Average Fee',
            'Average Gross Profit Margin',
            'Count',
            'Std Dev',
            '25%',
            '50%',
            '75%',
            'Max'
        ]

        # Calculate metrics for each rank category
        metrics_data = []

        for rank_category in rank_categories:
            row_data = [rank_category]

            # Extract rank range from category name
            if rank_category == '#1-10':
                min_rank, max_rank = 1, 10
            elif rank_category == '#11-30':
                min_rank, max_rank = 11, 30
            elif rank_category == '31-50':
                min_rank, max_rank = 31, 50
            elif rank_category == '51-100':
                min_rank, max_rank = 51, 100
            elif rank_category == '101-150':
                min_rank, max_rank = 101, 150
            elif rank_category == '151-200':
                min_rank, max_rank = 151, 200
            elif rank_category == '201-300':
                min_rank, max_rank = 201, 300
            elif rank_category == '301+':
                min_rank, max_rank = 301, float('inf')
            else:
                # Default case (shouldn't happen)
                min_rank, max_rank = 0, float('inf')

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
                row_data.extend([''] * (len(metrics_cols) - 1))

            metrics_data.append(row_data)

        # Create the DataFrame
        metrics_df = pd.DataFrame(metrics_data, columns=metrics_cols)

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


def generate_product_performance(df_combined, df_ads=None, df_organic=None):
    """
    Generate product performance metrics table with tabs for different groups
    """
    try:
        # Create tabs for the three different groups
        group_tabs = st.tabs(["Ads Group", "Organic Group", "Combined Group"])

        with group_tabs[0]:  # Ads Group
            if df_ads is not None and not df_ads.empty:
                display_product_performance_table(df_ads, "Ads", rank_column='Ad Rank')
            else:
                st.info("No Ads data available")

        with group_tabs[1]:  # Organic Group
            if df_organic is not None and not df_organic.empty:
                display_product_performance_table(df_organic, "Organic", rank_column='Organic Rank')
            else:
                st.info("No Organic data available")

        with group_tabs[2]:  # Combined Group
            display_product_performance_table(df_combined, "Combined", rank_column='Sales Rank (ALL)')
    except Exception as e:
        st.error(f"Error generating product performance metrics: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def display_product_performance_table(df, group_name, rank_column='Sales Rank (ALL)'):
    """
    Display product performance metrics table for a specific group
    """
    try:
        # Define the rank buckets
        rank_categories = ['#1-10', '#11-30', '31-50', '51-100', '101-150', '151-200', '201-300', '301+']

        # Identify columns for product performance metrics
        # Look for BSR column
        bsr_columns = ['BSR', 'Best Sellers Rank', 'BestSellersRank', 'Best Seller Rank']
        bsr_column = find_column_in_dataframe(df, bsr_columns)

        # Look for Rating column
        rating_columns = ['Rating', 'Product Rating', 'Star Rating', 'Stars', 'Average Rating']
        rating_column = find_column_in_dataframe(df, rating_columns)

        # Look for Review Count column
        review_count_columns = ['Review Count', 'Reviews', 'Number of Reviews', 'ReviewCount', 'Total Reviews']
        review_count_column = find_column_in_dataframe(df, review_count_columns)

        # Look for Review Velocity column
        review_velocity_columns = ['Review Velocity', 'ReviewVelocity', 'Reviews Per Month', 'Monthly Reviews']
        review_velocity_column = find_column_in_dataframe(df, review_velocity_columns)

        # Look for Images column
        images_columns = ['Images', 'Image Count', 'Number of Images', 'ImageCount', 'Product Images']
        images_column = find_column_in_dataframe(df, images_columns)

        # Create placeholder columns if needed
        if not bsr_column:
            df['BSR_Placeholder'] = 50000  # Default placeholder value
            bsr_column = 'BSR_Placeholder'

        if not rating_column:
            df['Rating_Placeholder'] = 4.0  # Default placeholder value
            rating_column = 'Rating_Placeholder'

        if not review_count_column:
            df['Review_Count_Placeholder'] = 100  # Default placeholder value
            review_count_column = 'Review_Count_Placeholder'

        if not review_velocity_column:
            df['Review_Velocity_Placeholder'] = 5  # Default placeholder value
            review_velocity_column = 'Review_Velocity_Placeholder'

        if not images_column:
            df['Images_Placeholder'] = 5  # Default placeholder value
            images_column = 'Images_Placeholder'

        # Define the metrics columns
        metrics_cols = [
            'Catalog Rank',
            'Average BSR',
            'Average Rating',
            'Average Review Count',
            'Review Velocity (reviews/month)',
            'Average Number of Images'
        ]

        # Calculate metrics for each rank category
        metrics_data = []

        for rank_category in rank_categories:
            row_data = [rank_category]

            # Extract rank range from category name
            min_rank, max_rank = get_rank_range(rank_category)

            # Get data for this rank range
            category_data = df[(df[rank_column] >= min_rank) & (df[rank_column] <= max_rank)]

            if len(category_data) > 0:
                # Calculate metrics
                avg_bsr = clean_and_compute_average(category_data, bsr_column)
                avg_rating = clean_and_compute_average(category_data, rating_column)
                avg_review_count = clean_and_compute_average(category_data, review_count_column)
                avg_review_velocity = clean_and_compute_average(category_data, review_velocity_column)
                avg_images = clean_and_compute_average(category_data, images_column)

                # Format and add to row data
                row_data.extend([
                    f"{avg_bsr:,.0f}" if not pd.isna(avg_bsr) else '',
                    f"{avg_rating:.1f}" if not pd.isna(avg_rating) else '',
                    f"{avg_review_count:,.0f}" if not pd.isna(avg_review_count) else '',
                    f"{avg_review_velocity:.1f}" if not pd.isna(avg_review_velocity) else '',
                    f"{avg_images:.1f}" if not pd.isna(avg_images) else ''
                ])
            else:
                # If no data for this category, add empty values
                row_data.extend([''] * (len(metrics_cols) - 1))

            metrics_data.append(row_data)

        # Create the DataFrame
        metrics_df = pd.DataFrame(metrics_data, columns=metrics_cols)

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
            key=f"product_performance_table_{group_name}"  # Unique key for each table
        )

        # Show sample calculation for transparency in a collapsible section
        with st.expander(f"How are {group_name} product performance calculations performed?"):
            st.write(f"Sample calculation for {group_name} group, #1-10 range:")
            top10_data = df[(df[rank_column] >= 1) & (df[rank_column] <= 10)]
            st.write(f"Number of products in range: {len(top10_data)}")

            if len(top10_data) > 0:
                st.write(f"Rank column used: {rank_column}")

                # Show calculations for each metric if data is available
                if bsr_column:
                    st.write(f"BSR column used: {bsr_column}")
                    clean_bsr = pd.to_numeric(
                        top10_data[bsr_column].astype(str).str.replace('[,]', '', regex=True),
                        errors='coerce'
                    )
                    st.write(f"Average BSR: {clean_bsr.mean():,.0f}")

                if rating_column:
                    st.write(f"Rating column used: {rating_column}")
                    clean_rating = pd.to_numeric(
                        top10_data[rating_column],
                        errors='coerce'
                    )
                    st.write(f"Average Rating: {clean_rating.mean():.1f}")

                if review_count_column:
                    st.write(f"Review Count column used: {review_count_column}")
                    clean_review_count = pd.to_numeric(
                        top10_data[review_count_column].astype(str).str.replace('[,]', '', regex=True),
                        errors='coerce'
                    )
                    st.write(f"Average Review Count: {clean_review_count.mean():,.0f}")

                if review_velocity_column:
                    st.write(f"Review Velocity column used: {review_velocity_column}")
                    clean_review_velocity = pd.to_numeric(
                        top10_data[review_velocity_column],
                        errors='coerce'
                    )
                    st.write(f"Average Review Velocity: {clean_review_velocity.mean():.1f}")

                if images_column:
                    st.write(f"Images column used: {images_column}")
                    clean_images = pd.to_numeric(
                        top10_data[images_column],
                        errors='coerce'
                    )
                    st.write(f"Average Number of Images: {clean_images.mean():.1f}")
            else:
                st.write("No data in this rank range")

    except Exception as e:
        st.error(f"Error displaying product performance metrics for {group_name}: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

    def find_column_in_dataframe(df, possible_column_names):
        """
        Find a column in the dataframe based on a list of possible column names
        Returns the name of the first matching column found, or None if not found
        """
        # First check for exact matches
        for col_name in possible_column_names:
            if col_name in df.columns:
                return col_name

        # Then check for partial matches (case insensitive)
        for col_name in df.columns:
            for possible_name in possible_column_names:
                if possible_name.lower() in col_name.lower():
                    return col_name

        # If no match is found, check for any column that might contain relevant keywords
        keywords = []
        for name in possible_column_names:
            keywords.extend(name.lower().split())

        for col_name in df.columns:
            for keyword in keywords:
                if keyword in col_name.lower():
                    return col_name

        # No match found
        return None

    def get_rank_range(rank_category):
        """Helper function to get min and max rank from category name"""
        if rank_category == '#1-10':
            return 1, 10
        elif rank_category == '#11-30':
            return 11, 30
        elif rank_category == '31-50':
            return 31, 50
        elif rank_category == '51-100':
            return 51, 100
        elif rank_category == '101-150':
            return 101, 150
        elif rank_category == '151-200':
            return 151, 200
        elif rank_category == '201-300':
            return 201, 300
        elif rank_category == '301+':
            return 301, float('inf')
        else:
            # Default case (shouldn't happen)
            return 0, float('inf')