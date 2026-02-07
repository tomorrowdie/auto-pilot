# catalog_summary_08_detailed_analysis.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =====================================================================
# Configuration Section - Edit these values to customize the component
# =====================================================================

# Component title
COMPONENT_TITLE = "Detailed Analysis"
COMPONENT_TITLE_CN = "詳細分析"

# Rank columns for different groups
ADS_RANK_COLUMN = 'Ad Rank'
ORGANIC_RANK_COLUMN = 'Organic Rank'
COMBINED_RANK_COLUMN = 'Sales Rank (ALL)'

# Columns to analyze (product attributes)
ATTRIBUTE_COLUMNS = [
    'Brand', 'Category', 'Size', 'Material', 'Color', 'Product Type',
    'Model Number', 'Package', 'Features', 'Product Line'
]


# =====================================================================


def display_detail_analysis(df_combined, df_ads, df_organic):
    """
    Display detailed analysis of product data with advanced metrics

    Parameters:
    - df_combined: Combined dataframe with all products
    - df_ads: Dataframe containing only ads products
    - df_organic: Dataframe containing only organic products
    """
    st.subheader(f"{COMPONENT_TITLE} / {COMPONENT_TITLE_CN}")

    # Create tabs for different analyses
    tab1, tab2, tab3 = st.tabs([
        "Product Attribute Analysis / 產品屬性分析",
        "Top Products Analysis / 熱門產品分析",
        "Competitive Analysis / 競爭分析"
    ])

    with tab1:
        display_attribute_analysis(df_combined)

    with tab2:
        display_top_products_analysis(df_combined, df_ads, df_organic)

    with tab3:
        display_competitive_analysis(df_combined)


def display_attribute_analysis(df):
    """Analyze product attributes and their impact on sales and rankings"""
    st.write("### Product Attribute Analysis / 產品屬性分析")

    # Find available attribute columns in the dataframe
    available_attributes = []
    for attr in ATTRIBUTE_COLUMNS:
        for col in df.columns:
            if attr.lower() in col.lower():
                available_attributes.append(col)
                break

    if not available_attributes:
        st.info("No product attribute columns found in the data. Please check column names.")
        return

    # Let user select an attribute to analyze
    selected_attribute = st.selectbox(
        "Select an attribute to analyze / 選擇要分析的屬性",
        options=available_attributes,
        index=0 if available_attributes else None
    )

    if not selected_attribute:
        return

    # Select metric to analyze correlation with
    metric_options = []
    for col in df.columns:
        # Look for sales, revenue, or price columns
        if any(term in col.lower() for term in ['sales', 'revenue', 'price', 'bsr', 'rating']):
            try:
                # Check if column is numeric
                pd.to_numeric(df[col].astype(str).str.replace('[\$,]', '', regex=True), errors='coerce').mean()
                metric_options.append(col)
            except:
                pass

    if not metric_options:
        st.info("No metrics columns found for analysis.")
        return

    selected_metric = st.selectbox(
        "Select a metric to analyze / 選擇要分析的指標",
        options=metric_options,
        index=0 if metric_options else None
    )

    if not selected_metric:
        return

    # Analyze the selected attribute and metric
    st.write(f"#### Analysis of {selected_attribute} by {selected_metric}")

    # Clean the metric column for analysis
    df['Metric_Clean'] = pd.to_numeric(
        df[selected_metric].astype(str).str.replace('[\$,]', '', regex=True),
        errors='coerce'
    )

    # Group by the attribute and aggregate
    attribute_analysis = df.groupby(selected_attribute)['Metric_Clean'].agg([
        ('Count', 'count'),
        ('Mean', 'mean'),
        ('Median', 'median'),
        ('Min', 'min'),
        ('Max', 'max')
    ]).reset_index()

    # Sort by mean value (descending)
    attribute_analysis = attribute_analysis.sort_values('Mean', ascending=False)

    # Format numeric columns
    for col in ['Mean', 'Median', 'Min', 'Max']:
        if 'price' in selected_metric.lower() or 'revenue' in selected_metric.lower():
            attribute_analysis[col] = attribute_analysis[col].map('${:,.2f}'.format)
        else:
            attribute_analysis[col] = attribute_analysis[col].map('{:,.1f}'.format)

    # Display the table
    st.dataframe(attribute_analysis, use_container_width=True)

    # Create a visualization
    try:
        # Prepare data for visualization
        viz_data = df.groupby(selected_attribute)['Metric_Clean'].mean().reset_index()
        viz_data = viz_data.sort_values('Metric_Clean', ascending=False)

        # Limit to top 10 attributes for better visualization
        if len(viz_data) > 10:
            viz_data = viz_data.head(10)

        # Create bar chart
        fig = px.bar(
            viz_data,
            x=selected_attribute,
            y='Metric_Clean',
            title=f"Average {selected_metric} by {selected_attribute}",
            labels={
                selected_attribute: selected_attribute,
                'Metric_Clean': selected_metric
            },
            color='Metric_Clean',
            color_continuous_scale='Viridis'
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")


def display_top_products_analysis(df_combined, df_ads, df_organic):
    """Display detailed analysis of top-performing products"""
    st.write("### Top Products Analysis / 熱門產品分析")

    # Select dataset to analyze
    dataset_option = st.radio(
        "Select dataset to analyze / 選擇要分析的數據集",
        options=["Combined Data", "Ads Products", "Organic Products"],
        index=0,
        horizontal=True
    )

    if dataset_option == "Combined Data":
        df = df_combined
        rank_column = COMBINED_RANK_COLUMN
    elif dataset_option == "Ads Products":
        df = df_ads
        rank_column = ADS_RANK_COLUMN
    else:
        df = df_organic
        rank_column = ORGANIC_RANK_COLUMN

    if df is None or df.empty:
        st.info(f"No data available for {dataset_option}")
        return

    # Select how many top products to analyze
    top_n = st.slider(
        "Select number of top products to analyze / 選擇要分析的熱門產品數量",
        min_value=5,
        max_value=50,
        value=10,
        step=5
    )

    # Ensure rank column exists
    if rank_column not in df.columns:
        st.warning(f"Rank column '{rank_column}' not found. Using display order instead.")
        if 'Display Order' in df.columns:
            rank_column = 'Display Order'
        else:
            st.error("No suitable ranking column found.")
            return

    # Get top N products
    top_products = df.sort_values(rank_column).head(top_n)

    # Display product details
    st.write(f"#### Top {top_n} Products")

    # Select columns to display
    display_cols = ['Product Details', 'ASIN', 'Brand', rank_column]

    # Add metrics columns if they exist
    for col in df.columns:
        if any(term in col.lower() for term in ['price', 'bsr', 'rating', 'review count', 'sales']):
            if col not in display_cols:
                display_cols.append(col)

    # Only use columns that actually exist in the dataframe
    display_cols = [col for col in display_cols if col in df.columns]

    # Display the table
    st.dataframe(top_products[display_cols], use_container_width=True)

    # Create a visualization of key metrics for top products
    create_top_products_chart(top_products)

    # Show common attributes among top products
    show_common_attributes(top_products)


def create_top_products_chart(df):
    """Create a chart visualizing key metrics of top products"""
    try:
        # Select a metric for visualization
        metric_options = []
        for col in df.columns:
            # Look for sales, revenue, or price columns
            if any(term in col.lower() for term in ['sales', 'revenue', 'price', 'bsr']):
                try:
                    # Check if column is numeric
                    pd.to_numeric(df[col].astype(str).str.replace('[\$,]', '', regex=True), errors='coerce').mean()
                    metric_options.append(col)
                except:
                    pass

        if not metric_options:
            return

        selected_metric = st.selectbox(
            "Select a metric to visualize / 選擇要可視化的指標",
            options=metric_options,
            index=0 if metric_options else None
        )

        if not selected_metric:
            return

        # Clean the metric column for visualization
        df['Metric_Clean'] = pd.to_numeric(
            df[selected_metric].astype(str).str.replace('[\$,]', '', regex=True),
            errors='coerce'
        )

        # Create a product identifier for x-axis
        if 'ASIN' in df.columns:
            df['Product_ID'] = df['ASIN']
        elif 'Product Details' in df.columns:
            df['Product_ID'] = df['Product Details'].str.slice(0, 30) + '...'
        else:
            df['Product_ID'] = range(1, len(df) + 1)

        # Sort by metric value
        df_sorted = df.sort_values('Metric_Clean', ascending=False)

        # Create bar chart
        fig = px.bar(
            df_sorted,
            x='Product_ID',
            y='Metric_Clean',
            title=f"{selected_metric} for Top Products",
            labels={
                'Product_ID': 'Product',
                'Metric_Clean': selected_metric
            },
            color='Metric_Clean',
            text='Metric_Clean'
        )

        # Format text values
        if 'price' in selected_metric.lower() or 'revenue' in selected_metric.lower():
            fig.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
        else:
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")


def show_common_attributes(df):
    """Identify common attributes and patterns among top products"""
    st.write("#### Common Attributes Among Top Products")

    # Find available attribute columns
    attribute_columns = []
    for attr in ATTRIBUTE_COLUMNS:
        for col in df.columns:
            if attr.lower() in col.lower():
                attribute_columns.append(col)
                break

    if not attribute_columns:
        st.info("No attribute columns found for pattern analysis.")
        return

    # Analyze patterns in each attribute
    for attr in attribute_columns:
        try:
            # Count occurrences of each value
            value_counts = df[attr].value_counts()

            # Display top values if there are any patterns
            if len(value_counts) > 0 and len(value_counts) < len(df):
                top_value = value_counts.index[0]
                top_count = value_counts.iloc[0]
                percentage = (top_count / len(df)) * 100

                st.write(f"**{attr}**: {top_value} ({top_count} products, {percentage:.1f}%)")

                # Create a small pie chart for distribution
                if len(value_counts) <= 5:  # Only for attributes with few distinct values
                    fig = px.pie(
                        names=value_counts.index,
                        values=value_counts.values,
                        title=f"{attr} Distribution"
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
        except:
            # Skip attributes that can't be analyzed
            pass


def display_competitive_analysis(df):
    """Display competitive analysis based on brand performance"""
    st.write("### Competitive Analysis / 競爭分析")

    # Check for brand column
    brand_column = None
    for col in df.columns:
        if 'brand' in col.lower():
            brand_column = col
            break

    if not brand_column:
        st.info("Brand column not found in the data. Cannot perform competitive analysis.")
        return

    # Get top brands by product count
    brand_counts = df[brand_column].value_counts().reset_index()
    brand_counts.columns = ['Brand', 'Product Count']

    # Select top N brands for analysis
    top_n = st.slider(
        "Select number of top brands to analyze / 選擇要分析的頂級品牌數量",
        min_value=3,
        max_value=20,
        value=10,
        step=1
    )

    top_brands = brand_counts.head(top_n)['Brand'].tolist()

    # Filter data to include only top brands
    filtered_df = df[df[brand_column].isin(top_brands)]

    # Create metrics for competitive analysis
    brand_metrics = []

    for brand in top_brands:
        brand_data = filtered_df[filtered_df[brand_column] == brand]

        # Calculate various metrics
        product_count = len(brand_data)

        # Get average price if price column exists
        avg_price = None
        for col in df.columns:
            if 'price' in col.lower():
                try:
                    avg_price = pd.to_numeric(
                        brand_data[col].astype(str).str.replace('[\$,]', '', regex=True),
                        errors='coerce'
                    ).mean()
                    break
                except:
                    pass

        # Get average rating if rating column exists
        avg_rating = None
        for col in df.columns:
            if 'rating' in col.lower():
                try:
                    avg_rating = pd.to_numeric(brand_data[col], errors='coerce').mean()
                    break
                except:
                    pass

        # Get average review count if review count column exists
        avg_reviews = None
        for col in df.columns:
            if 'review' in col.lower() and 'count' in col.lower():
                try:
                    avg_reviews = pd.to_numeric(
                        brand_data[col].astype(str).str.replace(',', ''),
                        errors='coerce'
                    ).mean()
                    break
                except:
                    pass

        # Get average BSR if BSR column exists
        avg_bsr = None
        for col in df.columns:
            if 'bsr' in col.lower() or 'best seller' in col.lower():
                try:
                    avg_bsr = pd.to_numeric(
                        brand_data[col].astype(str).str.replace(',', ''),
                        errors='coerce'
                    ).mean()
                    break
                except:
                    pass

        # Get average sales if sales column exists
        avg_sales = None
        for col in df.columns:
            if 'sales' in col.lower():
                try:
                    avg_sales = pd.to_numeric(
                        brand_data[col].astype(str).str.replace(',', ''),
                        errors='coerce'
                    ).mean()
                    break
                except:
                    pass

        # Add to brand metrics
        brand_metrics.append({
            'Brand': brand,
            'Product Count': product_count,
            'Avg Price': f"${avg_price:.2f}" if avg_price is not None else 'N/A',
            'Avg Rating': f"{avg_rating:.1f}" if avg_rating is not None else 'N/A',
            'Avg Reviews': f"{avg_reviews:,.0f}" if avg_reviews is not None else 'N/A',
            'Avg BSR': f"{avg_bsr:,.0f}" if avg_bsr is not None else 'N/A',
            'Avg Sales': f"{avg_sales:,.0f}" if avg_sales is not None else 'N/A',
            'Avg Price Numeric': avg_price,
            'Avg Rating Numeric': avg_rating,
            'Avg Reviews Numeric': avg_reviews,
            'Avg BSR Numeric': avg_bsr,
            'Avg Sales Numeric': avg_sales
        })

    # Create DataFrame and display
    brand_df = pd.DataFrame(brand_metrics)

    # Display only the non-numeric columns
    display_cols = [col for col in brand_df.columns if 'Numeric' not in col]
    st.dataframe(brand_df[display_cols], use_container_width=True)

    # Create competitive analysis chart
    create_competitive_chart(brand_df)


def create_competitive_chart(df):
    """Create a radar chart or bubble chart for competitive analysis"""
    # Select metrics for analysis
    metric_options = []
    for col in df.columns:
        if 'Numeric' in col and df[col].notna().any():
            metric_display_name = col.replace(' Numeric', '')
            metric_options.append((metric_display_name, col))

    if len(metric_options) < 2:
        st.info("Not enough metrics available for competitive visualization.")
        return

    # Let user select visualization type
    viz_type = st.radio(
        "Select visualization type / 選擇可視化類型",
        options=["Radar Chart", "Bubble Chart"],
        index=0,
        horizontal=True
    )

    if viz_type == "Radar Chart":
        create_radar_chart(df, metric_options)
    else:
        create_bubble_chart(df, metric_options)


def create_radar_chart(df, metric_options):
    """Create a radar chart comparing brands across metrics"""
    try:
        # Select up to 5 metrics for the radar chart
        if len(metric_options) > 5:
            st.info("For better visualization, please select up to 5 metrics:")
            selected_metrics = []
            for i, (name, col) in enumerate(metric_options[:5]):
                if st.checkbox(name, value=(i < 5)):
                    selected_metrics.append((name, col))
        else:
            selected_metrics = metric_options

        if not selected_metrics:
            return

        # Get brands and metric data
        brands = df['Brand'].tolist()

        # Create figure
        fig = go.Figure()

        # Add traces for each brand
        for i, brand in enumerate(brands):
            brand_data = df[df['Brand'] == brand].iloc[0]

            # Get values for each metric
            values = []
            for _, col in selected_metrics:
                if pd.notna(brand_data[col]):
                    values.append(brand_data[col])
                else:
                    values.append(0)

            # Need to repeat the first value to close the polygon
            values.append(values[0])

            # Get metric names
            categories = [name for name, _ in selected_metrics]
            categories.append(categories[0])

            # Add to radar chart
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=brand
            ))

        # Update layout
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]  # Will be updated
                )
            ),
            showlegend=True,
            height=500,
            title="Brand Competitive Analysis (Radar Chart)"
        )

        # Normalize the data for better visualization
        for i, (_, col) in enumerate(selected_metrics):
            max_val = df[col].max()
            if max_val > 0:
                for j, brand in enumerate(brands):
                    fig.data[j].r[i] = fig.data[j].r[i] / max_val

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating radar chart: {str(e)}")


def create_bubble_chart(df, metric_options):
    """Create a bubble chart comparing brands across three metrics"""
    try:
        # Get at least 3 metrics for bubble chart (x, y, size)
        if len(metric_options) < 3:
            st.info("Bubble chart requires at least 3 metrics. Not enough metrics available.")
            return

        # Select metrics for x, y, and size
        col1, col2, col3 = st.columns(3)

        with col1:
            x_metric = st.selectbox(
                "X-axis metric / X軸指標",
                options=[name for name, _ in metric_options],
                index=0
            )
            x_col = [col for name, col in metric_options if name == x_metric][0]

        with col2:
            y_metric = st.selectbox(
                "Y-axis metric / Y軸指標",
                options=[name for name, _ in metric_options],
                index=min(1, len(metric_options) - 1)
            )
            y_col = [col for name, col in metric_options if name == y_metric][0]

        with col3:
            size_metric = st.selectbox(
                "Bubble size metric / 氣泡大小指標",
                options=[name for name, _ in metric_options],
                index=min(2, len(metric_options) - 1)
            )
            size_col = [col for name, col in metric_options if name == size_metric][0]

        # Create bubble chart
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            size=size_col,
            color='Brand',
            hover_name='Brand',
            text='Brand',
            title=f"Brand Competitive Analysis: {x_metric} vs {y_metric} (size: {size_metric})",
            labels={
                x_col: x_metric,
                y_col: y_metric,
                size_col: size_metric
            }
        )

        fig.update_traces(textposition='top center')
        fig.update_layout(height=600)

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating bubble chart: {str(e)}")