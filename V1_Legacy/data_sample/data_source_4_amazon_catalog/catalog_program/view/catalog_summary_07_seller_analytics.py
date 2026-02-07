# catalog_summary_07_seller_analytics.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# =====================================================================
# Configuration Section - Edit these values to customize the component
# =====================================================================

# Component title
COMPONENT_TITLE = "Seller Analytics"
COMPONENT_TITLE_CN = "賣家分析"

# Seller metrics configuration
SELLER_METRICS = [
    {
        "name": "AMZ-operated stores",
        "name_cn": "AMZ 經營的商店",
        "country_code": "AMZ"
    },
    {
        "name": "AMZ-operated market capacity ratio",
        "name_cn": "AMZ 營運的市場容量比率",
        "country_code": "AMZ",
        "is_ratio": True
    },
    {
        "name": "US Owned Stores",
        "name_cn": "美國自營商店",
        "country_code": "US"
    },
    {
        "name": "US market capacity ratio",
        "name_cn": "美國市場容量比率",
        "country_code": "US",
        "is_ratio": True
    },
    {
        "name": "CN-operated stores",
        "name_cn": "中國經營的商店",
        "country_code": "CN"
    },
    {
        "name": "CN market capacity ratio",
        "name_cn": "中國市場容量比率",
        "country_code": "CN",
        "is_ratio": True
    },
    {
        "name": "HK-operated stores",
        "name_cn": "香港經營的商店",
        "country_code": "HK"
    },
    {
        "name": "HK market capacity ratio",
        "name_cn": "HK市場容量比率",
        "country_code": "HK",
        "is_ratio": True
    },
    {
        "name": "Average Seller Age (months)",
        "name_cn": "賣家平均年齡（月）",
        "special": "seller_age"
    }
]

# Possible column names for seller country
SELLER_COUNTRY_COLUMNS = ['Seller Country', 'Country', 'Merchant Country', 'Seller Origin']

# Possible column names for revenue
REVENUE_COLUMNS = [
    'ASIN Revenue', 'Revenue', 'Parent Level Revenue',
    'Monthly Revenue', 'Estimated Revenue', 'Total Revenue',
    'Market Volume'
]

# Possible column names for seller creation date
CREATION_DATE_COLUMNS = [
    'Creation Date', 'Seller Since', 'Store Creation Date',
    'Start Date', 'Launch Date', 'Seller Launch Date'
]


# =====================================================================


def display_seller_analytics(df_combined, df_ads, df_organic):
    """
    Display seller analytics metrics

    Parameters:
    - df_combined: Combined dataframe with all products
    - df_ads: Dataframe containing only ads products
    - df_organic: Dataframe containing only organic products
    """
    # Add debug prints
    st.write("Seller Analytics function called")

    # Check if dataframes have data
    st.write(f"Combined dataframe size: {len(df_combined) if df_combined is not None else 'None'}")
    st.write(f"Ads dataframe size: {len(df_ads) if df_ads is not None and not df_ads.empty else 'Empty or None'}")
    st.write(
        f"Organic dataframe size: {len(df_organic) if df_organic is not None and not df_organic.empty else 'Empty or None'}")

    # Display column names for debugging
    if df_combined is not None:
        st.write("Available columns:", df_combined.columns.tolist()[:10], "...")

    st.subheader(f"{COMPONENT_TITLE} / {COMPONENT_TITLE_CN}")

    # Identify the relevant columns
    seller_country_column = identify_column(df_combined, SELLER_COUNTRY_COLUMNS)
    revenue_column = identify_column(df_combined, REVENUE_COLUMNS)
    creation_date_column = identify_column(df_combined, CREATION_DATE_COLUMNS)

    # Check if required columns are found
    if not seller_country_column:
        st.warning(f"Seller country column not found. Using placeholder data.")
        # Create a placeholder column with random country values
        seller_country_column = "Seller_Country_Placeholder"
        countries = ["AMZ", "US", "CN", "HK", "Other"]
        weights = [0.25, 0.4, 0.2, 0.1, 0.05]  # Adjust weights as needed

        # Add placeholder column to each dataframe
        if df_combined is not None:
            df_combined[seller_country_column] = np.random.choice(
                countries, size=len(df_combined), p=weights
            )

        if df_ads is not None and not df_ads.empty:
            df_ads[seller_country_column] = np.random.choice(
                countries, size=len(df_ads), p=weights
            )

        if df_organic is not None and not df_organic.empty:
            df_organic[seller_country_column] = np.random.choice(
                countries, size=len(df_organic), p=weights
            )

    if not revenue_column:
        st.warning(f"Revenue column not found. Using placeholder data.")
        # Create a placeholder column with random revenue values
        revenue_column = "Revenue_Placeholder"

        # Add placeholder column to each dataframe
        if df_combined is not None:
            df_combined[revenue_column] = np.random.uniform(100, 10000, size=len(df_combined))

        if df_ads is not None and not df_ads.empty:
            df_ads[revenue_column] = np.random.uniform(100, 10000, size=len(df_ads))

        if df_organic is not None and not df_organic.empty:
            df_organic[revenue_column] = np.random.uniform(100, 10000, size=len(df_organic))

    if not creation_date_column:
        st.warning(f"Creation date column not found. Using placeholder data.")
        # Create a placeholder column with random dates (1-60 months ago)
        creation_date_column = "Creation_Date_Placeholder"

        # Get current date for age calculation
        current_date = datetime.now()

        # Generate random dates for each dataframe
        if df_combined is not None:
            df_combined[creation_date_column] = [
                current_date.replace(month=current_date.month - np.random.randint(1, 60))
                for _ in range(len(df_combined))
            ]

        if df_ads is not None and not df_ads.empty:
            df_ads[creation_date_column] = [
                current_date.replace(month=current_date.month - np.random.randint(1, 60))
                for _ in range(len(df_ads))
            ]

        if df_organic is not None and not df_organic.empty:
            df_organic[creation_date_column] = [
                current_date.replace(month=current_date.month - np.random.randint(1, 60))
                for _ in range(len(df_organic))
            ]

    # Create tabs for the three different groups
    group_tabs = st.tabs(["Ads Group / 廣告組", "Organic Group / 自然組", "Combined Group / 合併組"])

    with group_tabs[0]:  # Ads Group
        if df_ads is not None and not df_ads.empty:
            display_seller_metrics_table(df_ads, "Ads", seller_country_column, revenue_column, creation_date_column)
        else:
            st.info("No Ads data available / 沒有廣告數據")

    with group_tabs[1]:  # Organic Group
        if df_organic is not None and not df_organic.empty:
            display_seller_metrics_table(df_organic, "Organic", seller_country_column, revenue_column,
                                         creation_date_column)
        else:
            st.info("No Organic data available / 沒有自然數據")

    with group_tabs[2]:  # Combined Group
        display_seller_metrics_table(df_combined, "Combined", seller_country_column, revenue_column,
                                     creation_date_column)


def display_seller_metrics_table(df, group_name, seller_country_column, revenue_column, creation_date_column):
    """
    Display seller metrics table for a specific group
    """
    try:
        # Calculate metrics
        metrics_data = []

        # Get total revenue for ratio calculations
        total_revenue = df[revenue_column].sum() if revenue_column in df.columns else 0

        # Calculate metrics for each seller country
        for metric in SELLER_METRICS:
            if "special" in metric and metric["special"] == "seller_age":
                # Calculate average seller age in months
                avg_months = calculate_average_seller_age(df, creation_date_column)
                metric_value = f"{avg_months:.1f}" if avg_months is not None else "N/A"
            elif "is_ratio" in metric and metric["is_ratio"]:
                # Calculate market capacity ratio
                country_code = metric["country_code"]
                country_revenue = df.loc[df[
                                             seller_country_column] == country_code, revenue_column].sum() if seller_country_column in df.columns and revenue_column in df.columns else 0
                ratio = (country_revenue / total_revenue * 100) if total_revenue > 0 else 0
                metric_value = f"{ratio:.1f}%" if ratio is not None else "N/A"
            else:
                # Count stores by country
                country_code = metric["country_code"]
                count = df[df[seller_country_column] == country_code].shape[
                    0] if seller_country_column in df.columns else 0
                metric_value = str(count) if count is not None else "N/A"

            # Add row to table data
            metrics_data.append([
                f"{metric['name']} / {metric['name_cn']}",
                metric_value
            ])

        # Create the DataFrame for display
        metrics_df = pd.DataFrame(metrics_data, columns=["Metric / 指標", "Value / 值"])

        # Apply custom CSS for table styling
        apply_table_styling()

        # Display the table without the index column
        st.dataframe(
            metrics_df,
            use_container_width=True,
            hide_index=True,
            height=400,  # Make the table taller
            key=f"seller_metrics_table_{group_name}"  # Unique key for each table
        )

        # Create visualizations
        create_seller_visualizations(df, group_name, seller_country_column, revenue_column)

        # Show calculation details in expander
        with st.expander(f"How are {group_name} seller metrics calculated? / {group_name}賣家指標計算方式?"):
            st.write(f"### Seller metrics calculation details:")

            st.write(f"- Total products: {len(df)}")
            st.write(f"- Seller country column used: {seller_country_column}")
            st.write(f"- Revenue column used: {revenue_column}")
            st.write(f"- Creation date column used: {creation_date_column}")

            # Show country distribution
            if seller_country_column in df.columns:
                country_counts = df[seller_country_column].value_counts()
                st.write("### Country distribution:")
                for country, count in country_counts.items():
                    percentage = (count / len(df)) * 100
                    st.write(f"- {country}: {count} stores ({percentage:.1f}%)")

            # Show revenue by country
            if seller_country_column in df.columns and revenue_column in df.columns:
                st.write("### Revenue by country:")
                for country in df[seller_country_column].unique():
                    country_revenue = df.loc[df[seller_country_column] == country, revenue_column].sum()
                    percentage = (country_revenue / total_revenue) * 100 if total_revenue > 0 else 0
                    st.write(f"- {country}: ${country_revenue:,.2f} ({percentage:.1f}%)")

            # Show seller age calculation
            if creation_date_column in df.columns:
                st.write("### Sample seller age calculation:")
                sample_dates = df[creation_date_column].head(5)
                current_date = datetime.now()

                st.write(f"Current date: {current_date.strftime('%Y-%m-%d')}")
                for i, date in enumerate(sample_dates):
                    try:
                        date_obj = parse_date(date)
                        if date_obj:
                            months = calculate_months_between(date_obj, current_date)
                            st.write(f"- Seller {i + 1}: Creation date = {date}, Age = {months} months")
                    except:
                        st.write(f"- Seller {i + 1}: Could not parse date {date}")

    except Exception as e:
        st.error(f"Error displaying seller metrics for {group_name}: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def create_seller_visualizations(df, group_name, seller_country_column, revenue_column):
    """Create visualizations for seller analytics"""
    # Only create visualizations if we have the necessary columns
    if seller_country_column not in df.columns or revenue_column not in df.columns:
        return

    col1, col2 = st.columns(2)

    with col1:
        # Create store count pie chart
        create_store_count_chart(df, seller_country_column)

    with col2:
        # Create market capacity pie chart
        create_market_capacity_chart(df, seller_country_column, revenue_column)


def create_store_count_chart(df, seller_country_column):
    """Create pie chart of store counts by country"""
    try:
        # Count stores by country
        store_counts = df[seller_country_column].value_counts().reset_index()
        store_counts.columns = ['Country', 'Count']

        # Create pie chart
        fig = px.pie(
            store_counts,
            values='Count',
            names='Country',
            title='Store Distribution by Country / 按國家/地區的商店分佈',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Bold
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )

        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=30, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating store count chart: {str(e)}")


def create_market_capacity_chart(df, seller_country_column, revenue_column):
    """Create pie chart of market capacity by country"""
    try:
        # Group revenue by country
        revenue_by_country = df.groupby(seller_country_column)[revenue_column].sum().reset_index()
        revenue_by_country.columns = ['Country', 'Revenue']

        # Create pie chart
        fig = px.pie(
            revenue_by_country,
            values='Revenue',
            names='Country',
            title='Market Capacity by Country / 按國家/地區的市場容量',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Vivid
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )

        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=30, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating market capacity chart: {str(e)}")


def identify_column(df, possible_column_names):
    """
    Identify which column from a list of possible names exists in the dataframe
    Returns the name of the first matching column or None if none found
    """
    if df is None:
        st.write(f"DataFrame is None when searching for columns: {possible_column_names}")
        return None

    # For debugging, show what we're looking for
    st.write(f"Looking for columns like: {possible_column_names[:3]}... in available columns")

    # Check for exact matches first
    for col_name in possible_column_names:
        if col_name in df.columns:
            st.write(f"Found exact match for column: {col_name}")
            return col_name

    # Then check for partial matches (case insensitive)
    for df_col in df.columns:
        for possible_name in possible_column_names:
            if possible_name.lower() in df_col.lower():
                st.write(f"Found partial match: '{df_col}' matches with '{possible_name}'")
                return df_col

    st.write(f"No matching column found for: {possible_column_names}")
    return None


def calculate_average_seller_age(df, creation_date_column):
    """
    Calculate the average seller age in months based on the creation date
    """
    if creation_date_column not in df.columns:
        return None

    try:
        # Get current date
        current_date = datetime.now()

        # Calculate age for each seller
        ages = []
        for date_str in df[creation_date_column]:
            # Skip missing values
            if pd.isna(date_str):
                continue

            # Try to parse the date
            date_obj = parse_date(date_str)
            if date_obj:
                # Calculate months between creation date and current date
                months = calculate_months_between(date_obj, current_date)
                ages.append(months)

        # Return average age
        return np.mean(ages) if ages else None

    except Exception as e:
        st.error(f"Error calculating seller age: {str(e)}")
        return None


def parse_date(date_str):
    """
    Try to parse a date string in various formats
    Returns a datetime object or None if parsing fails
    """
    if pd.isna(date_str):
        return None

    # If already a datetime object, return it
    if isinstance(date_str, datetime):
        return date_str

    # Convert to string if not already
    date_str = str(date_str)

    # Try various date formats
    formats = [
        '%Y-%m-%d',  # 2023-01-15
        '%m/%d/%Y',  # 01/15/2023
        '%d/%m/%Y',  # 15/01/2023
        '%b %Y',  # Jan 2023
        '%B %Y',  # January 2023
        '%Y/%m/%d',  # 2023/01/15
        '%d-%b-%Y',  # 15-Jan-2023
        '%d-%B-%Y',  # 15-January-2023
        '%Y%m%d'  # 20230115
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # If all formats fail, try to extract year and month
    try:
        import re
        # Look for year-month pattern (e.g., "2022-05" or "May 2022")
        year_month_pattern = r'(\d{4})[-/](\d{1,2})'
        match = re.search(year_month_pattern, date_str)
        if match:
            year, month = map(int, match.groups())
            return datetime(year, month, 1)

        # Look for month-year pattern (e.g., "May 2022" or "May-2022")
        month_names = ["january", "february", "march", "april", "may", "june",
                       "july", "august", "september", "october", "november", "december",
                       "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        month_year_pattern = r'(' + '|'.join(month_names) + r')\s*[-]?\s*(\d{4})'
        match = re.search(month_year_pattern, date_str.lower())
        if match:
            month_str, year = match.groups()
            month = month_names.index(month_str) % 12 + 1  # Convert month name to number
            return datetime(int(year), month, 1)
    except:
        pass

    # If all parsing attempts fail
    return None


def calculate_months_between(start_date, end_date):
    """
    Calculate the number of months between two dates
    """
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)


def apply_table_styling():
    """Apply custom CSS styling to the metrics table"""
    st.markdown("""
    <style>
    /* Make the metric name column blue */
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