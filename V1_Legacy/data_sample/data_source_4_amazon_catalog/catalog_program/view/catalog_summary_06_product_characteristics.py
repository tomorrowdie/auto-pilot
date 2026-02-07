# catalog_summary_06_product_characteristics.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
from collections import Counter

# =====================================================================
# Configuration Section - Edit these values to customize the component
# =====================================================================

# Component title
COMPONENT_TITLE = "Product Characteristics"
COMPONENT_TITLE_CN = "產品特性"

# Rank categories to display in tables
RANK_CATEGORIES = ['#1-10', '#11-30', '#31-50', '#51-100', '#101-150', '#151-200', '#201-300', '#301+']

# Rank columns for different groups
ADS_RANK_COLUMN = 'Ad Rank'
ORGANIC_RANK_COLUMN = 'Organic Rank'
COMBINED_RANK_COLUMN = 'Sales Rank (ALL)'

# Possible column names for physical characteristics
WEIGHT_COLUMNS = ['Weight', 'Item Weight', 'Product Weight', 'Net Weight', 'Ship Weight']
DIMENSION_COLUMNS = ['Dimensions', 'Product Dimensions', 'Item Dimensions', 'Package Dimensions', 'Size']
SIZE_COLUMNS = ['Size', 'Size Tier', 'Product Size', 'Package Size']
CATEGORY_COLUMNS = ['Category', 'Department', 'Product Category', 'Product Type', 'Type']
ABA_CLICK_COLUMNS = ['ABA Most Clicked', 'ABA Click Position', 'Most Clicked Position']

# Metrics column configurations with Chinese translations
CHARACTERISTICS_METRICS = [
    {
        "name": "Catalog Rank",
        "name_cn": "目錄排名",
        "width": "medium",
        "help": "Ranking group based on product position"
    },
    {
        "name": "Average Weight (lbs)",
        "name_cn": "平均重量 (磅)",
        "candidates": WEIGHT_COLUMNS,
        "placeholder": 1.5,
        "format": "{:.2f}"
    },
    {
        "name": "Average Dimensions (in³)",
        "name_cn": "平均尺寸 (立方英寸)",
        "candidates": DIMENSION_COLUMNS,
        "placeholder": 100,
        "format": "{:.1f}"
    },
    {
        "name": "Size Tier Distribution",
        "name_cn": "尺寸層級分佈",
        "candidates": SIZE_COLUMNS,
        "placeholder": "Standard",
        "format": "{}"
    },
    {
        "name": "Category Distribution",
        "name_cn": "類別分佈",
        "candidates": CATEGORY_COLUMNS,
        "placeholder": "General",
        "format": "{}"
    },
    {
        "name": "Top ABA Click Positions",
        "name_cn": "最常點擊位置",
        "candidates": ABA_CLICK_COLUMNS,
        "placeholder": "Position 1",
        "format": "{}"
    }
]


# =====================================================================


def display_product_characteristics(df_combined, df_ads, df_organic):
    """
    Display product characteristics metrics

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
            display_characteristics_metrics_table(df_ads, "Ads", rank_column=ADS_RANK_COLUMN)
        else:
            st.info("No Ads data available / 沒有廣告數據")

    with group_tabs[1]:  # Organic Group
        if df_organic is not None and not df_organic.empty:
            display_characteristics_metrics_table(df_organic, "Organic", rank_column=ORGANIC_RANK_COLUMN)
        else:
            st.info("No Organic data available / 沒有自然數據")

    with group_tabs[2]:  # Combined Group
        display_characteristics_metrics_table(df_combined, "Combined", rank_column=COMBINED_RANK_COLUMN)


def display_characteristics_metrics_table(df, group_name, rank_column):
    """
    Display product characteristics metrics table for a specific group
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
        df = prepare_dataframe_for_characteristics(df)

        # Calculate metrics for each rank category
        metrics_data = []

        for rank_category in RANK_CATEGORIES:
            row_data = [rank_category]

            # Get min and max rank from category
            min_rank, max_rank = get_rank_range(rank_category)

            # Get data for this rank range
            category_data = df[(df[rank_column] >= min_rank) & (df[rank_column] <= max_rank)]

            if len(category_data) > 0:
                # Calculate metrics for each characteristic (skipping the first one which is Catalog Rank)
                for metric in CHARACTERISTICS_METRICS[1:]:
                    # The column to use is stored in df as the metric name with "_Column" suffix
                    column_name = f"{metric['name']}_Column"

                    if column_name in df.columns:
                        source_column = df[column_name].iloc[0]

                        # Handle different metric types differently
                        if metric["name"] == "Average Weight (lbs)":
                            value = calculate_average_weight(category_data, source_column)
                            formatted_value = metric["format"].format(value) if value is not None else ''

                        elif metric["name"] == "Average Dimensions (in³)":
                            value = calculate_average_dimensions(category_data, source_column)
                            formatted_value = metric["format"].format(value) if value is not None else ''

                        elif metric["name"] == "Size Tier Distribution":
                            formatted_value = calculate_size_distribution(category_data, source_column)

                        elif metric["name"] == "Category Distribution":
                            formatted_value = calculate_category_distribution(category_data, source_column)

                        elif metric["name"] == "Top ABA Click Positions":
                            formatted_value = calculate_aba_click_positions(category_data, source_column)

                        else:
                            # Default fallback
                            formatted_value = ''

                        row_data.append(formatted_value)
                    else:
                        row_data.append('')
            else:
                # If no data for this category, add empty values
                row_data.extend([''] * (len(CHARACTERISTICS_METRICS) - 1))

            metrics_data.append(row_data)

        # Create column names with English and Chinese labels
        column_names = [f"{m['name']} / {m['name_cn']}" for m in CHARACTERISTICS_METRICS]

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
                f"{CHARACTERISTICS_METRICS[0]['name']} / {CHARACTERISTICS_METRICS[0]['name_cn']}": st.column_config.Column(
                    f"{CHARACTERISTICS_METRICS[0]['name']} / {CHARACTERISTICS_METRICS[0]['name_cn']}",
                    width="medium",
                    help=f"Ranking group based on {rank_column}"
                )
            },
            height=400,  # Make the table taller
            key=f"characteristics_metrics_table_{group_name}"  # Unique key for each table
        )

        # Create visualizations of key characteristics
        if len(df) > 0:
            create_characteristics_visualizations(df, group_name, rank_column)

        # Show sample calculation for transparency in a collapsible section
        with st.expander(f"How are {group_name} product characteristics calculated? / {group_name}產品特性計算方式?"):
            st.write(f"Sample calculation for {group_name} group, #1-10 range:")
            top10_data = df[(df[rank_column] >= 1) & (df[rank_column] <= 10)]
            st.write(f"Number of products in range: {len(top10_data)}")

            if len(top10_data) > 0:
                st.write(f"Rank column used: {rank_column}")

                # Weight calculation example
                weight_column = df[f"{CHARACTERISTICS_METRICS[1]['name']}_Column"].iloc[0]
                if weight_column in top10_data.columns:
                    st.write(f"Weight column used: {weight_column}")
                    weight_values = extract_numeric_values(top10_data[weight_column], 'weight')
                    if not weight_values.empty:  # Fixed version
                        st.write(f"Sample weight values: {[f'{v:.2f}' for v in weight_values[:5]]}")
                        st.write(f"Average weight: {weight_values.mean():.2f} lbs")

                # Size distribution example
                size_column = df[f"{CHARACTERISTICS_METRICS[3]['name']}_Column"].iloc[0]
                if size_column in top10_data.columns:
                    st.write(f"Size column used: {size_column}")
                    size_counts = top10_data[size_column].value_counts()
                    if not size_counts.empty:
                        st.write("Size distribution:")
                        for size, count in size_counts.items():
                            percentage = (count / len(top10_data)) * 100
                            st.write(f"- {size}: {count} products ({percentage:.1f}%)")
            else:
                st.write("No data in this rank range / 此排名範圍內沒有數據")

    except Exception as e:
        st.error(f"Error displaying product characteristics for {group_name}: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def prepare_dataframe_for_characteristics(df):
    """
    Prepare dataframe for characteristics analysis by identifying or creating required columns
    Returns the modified dataframe with identified column names
    """
    # Make a copy to avoid modifying the original
    df = df.copy()

    # For each metric, find the appropriate column or create a placeholder
    for metric in CHARACTERISTICS_METRICS[1:]:  # Skip the first one which is Catalog Rank
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
            if metric["name"] == "Size Tier Distribution" or metric["name"] == "Category Distribution":
                # For categorical fields, use the placeholder as is
                df[placeholder_name] = metric["placeholder"]
            else:
                # For numeric fields, use the placeholder value
                df[placeholder_name] = metric["placeholder"]
            found_column = placeholder_name

        # Store the column name for this metric
        df[f"{metric['name']}_Column"] = found_column

    return df


def calculate_average_weight(df, column):
    """Calculate average weight from a column that may contain weight information"""
    try:
        if column not in df.columns:
            return None

        # Extract numeric values representing weight
        weight_values = extract_numeric_values(df[column], 'weight')

        # Use .empty attribute to check if the series has values
        if not weight_values.empty:
            return weight_values.mean()
        else:
            return None
    except:
        return None


def calculate_average_dimensions(df, column):
    """Calculate average dimensions (volume) from a dimension column"""
    try:
        if column not in df.columns:
            return None

        # Extract dimensions and calculate volumes
        volumes = []

        for value in df[column]:
            if pd.isna(value):
                continue

            # Handle different dimension formats
            # Common format: LxWxH (e.g., "10 x 5 x 2 inches")
            dimensions_str = str(value).lower()

            # Try to extract dimensions using regex
            # Looking for patterns like: 10 x 5 x 2 or 10" x 5" x 2"
            dimensions_pattern = r'(\d+\.?\d*)\s*["\']?\s*x\s*(\d+\.?\d*)\s*["\']?\s*x\s*(\d+\.?\d*)'
            matches = re.findall(dimensions_pattern, dimensions_str)

            if matches:
                # Use the first match
                l, w, h = map(float, matches[0])
                volume = l * w * h
                volumes.append(volume)

        if volumes:
            return np.mean(volumes)
        else:
            return None
    except:
        return None


def calculate_size_distribution(df, column):
    """Calculate size distribution and return top 2 sizes with percentages"""
    try:
        if column not in df.columns:
            return ""

        # Count occurrences of each size
        size_counts = df[column].value_counts()

        if len(size_counts) == 0:
            return ""

        # Get top 2 sizes
        top_sizes = size_counts.head(2)

        # Format as "Size1: XX%, Size2: YY%"
        result = []
        for size, count in top_sizes.items():
            percentage = (count / len(df)) * 100
            result.append(f"{size}: {percentage:.0f}%")

        return ", ".join(result)
    except:
        return ""


def calculate_category_distribution(df, column):
    """Calculate category distribution and return top category with percentage"""
    try:
        if column not in df.columns:
            return ""

        # Count occurrences of each category
        category_counts = df[column].value_counts()

        if len(category_counts) == 0:
            return ""

        # Get top category
        top_category = category_counts.index[0]
        count = category_counts.iloc[0]
        percentage = (count / len(df)) * 100

        # Format as "Category: XX%"
        return f"{top_category}: {percentage:.0f}%"
    except:
        return ""


def calculate_aba_click_positions(df, column):
    """
    Calculate the most frequent ABA click position
    If multiple positions have equal frequency, show the one with the lowest position number
    """
    try:
        if column not in df.columns:
            return ""

        # Extract position numbers using regex
        positions = []
        for value in df[column].dropna():
            # Look for patterns like "Position 3" or just "3"
            matches = re.findall(r'(?:position\s*)?(\d+)', str(value).lower())
            if matches:
                positions.append(int(matches[0]))

        if not positions:
            return ""

        # Count occurrences of each position
        position_counts = Counter(positions)

        if not position_counts:
            return ""

        # Find the most common positions
        most_common_count = position_counts.most_common(1)[0][1]
        most_common_positions = [pos for pos, count in position_counts.items() if count == most_common_count]

        # If multiple positions have the same frequency, pick the lowest number
        best_position = min(most_common_positions)

        return f"Position {best_position}"
    except:
        return ""


def extract_numeric_values(series, value_type='weight'):
    """
    Extract numeric values from a series that may contain weight or dimension information

    Parameters:
    - series: pandas Series containing the values
    - value_type: 'weight' or 'dimension' to determine extraction logic

    Returns:
    - pandas Series of extracted numeric values
    """
    numeric_values = []

    for value in series.dropna():
        value_str = str(value).lower()

        # Extract numeric part using regex
        if value_type == 'weight':
            # Look for patterns like "5 lbs" or "5.2 pounds"
            matches = re.findall(r'(\d+\.?\d*)\s*(?:lbs?|pounds?|oz|ounces?|kg|kilograms?)', value_str)
            if matches:
                # Convert to pounds if needed
                weight = float(matches[0])
                if 'oz' in value_str or 'ounce' in value_str:
                    weight /= 16  # Convert ounces to pounds
                elif 'kg' in value_str or 'kilogram' in value_str:
                    weight *= 2.20462  # Convert kg to pounds
                numeric_values.append(weight)
            else:
                # Try to extract just a number
                matches = re.findall(r'^(\d+\.?\d*)$', value_str)
                if matches:
                    numeric_values.append(float(matches[0]))

    return pd.Series(numeric_values)


def create_characteristics_visualizations(df, group_name, rank_column):
    """Create visualizations for product characteristics"""
    # Create 2 columns for charts
    col1, col2 = st.columns(2)

    with col1:
        # Weight Distribution
        weight_column = df[f"{CHARACTERISTICS_METRICS[1]['name']}_Column"].iloc[0]
        if weight_column in df.columns:
            create_weight_visualization(df, weight_column)

    with col2:
        # Category or Size Distribution
        category_column = df[f"{CHARACTERISTICS_METRICS[4]['name']}_Column"].iloc[0]
        if category_column in df.columns:
            create_category_visualization(df, category_column)


def create_weight_visualization(df, weight_column):
    """Create weight distribution visualization"""
    try:
        # Extract weight values
        weight_values = extract_numeric_values(df[weight_column], 'weight')

        if weight_values.empty or len(weight_values) < 5:  # Need at least a few values to make a meaningful chart
            st.info("Not enough valid weight data for visualization")
            return

        # Filter out extreme outliers for better visualization (95th percentile)
        max_weight = weight_values.quantile(0.95)
        filtered_weights = weight_values[weight_values <= max_weight]

        # Create histogram
        fig = px.histogram(
            filtered_weights,
            nbins=20,
            title='Weight Distribution / 重量分佈',
            labels={'value': 'Weight (lbs) / 重量（磅）'},
            color_discrete_sequence=['#3498db']
        )

        # Add a vertical line for average
        avg_weight = filtered_weights.mean()
        fig.add_vline(x=avg_weight, line_dash="dash", line_color="#e74c3c",
                      annotation_text=f"Avg: {avg_weight:.2f} lbs")

        fig.update_layout(
            xaxis_title='Weight (lbs) / 重量（磅）',
            yaxis_title='Count / 數量',
            height=350,
            margin=dict(l=40, r=40, t=50, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating weight visualization: {str(e)}")


def create_category_visualization(df, category_column):
    """Create category distribution visualization"""
    try:
        if category_column not in df.columns:
            st.info("Category data not available for visualization")
            return

        # Count categories
        category_counts = df[category_column].value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']

        # Limit to top 10 categories for better visualization
        if len(category_counts) > 10:
            other_count = category_counts.iloc[10:]['Count'].sum()
            top_categories = category_counts.iloc[:10].copy()
            if other_count > 0:
                other_row = pd.DataFrame({'Category': ['Other'], 'Count': [other_count]})
                top_categories = pd.concat([top_categories, other_row], ignore_index=True)
        else:
            top_categories = category_counts

        # Create pie chart
        fig = px.pie(
            top_categories,
            values='Count',
            names='Category',
            title='Category Distribution / 類別分佈',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )

        fig.update_layout(
            height=350,
            margin=dict(l=40, r=40, t=50, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating category visualization: {str(e)}")


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