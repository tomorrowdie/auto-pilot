import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_price_analysis(df_combined, df_ads, df_organic):
    """Price distribution and comparison between organic and ads using Plotly"""
    st.subheader("Price Analysis / 價格分析")

    # Ensure we have price data
    if 'Price US' not in df_combined.columns:
        st.warning("Price data not available in the dataset")
        return

    try:
        # Clean price data
        df_combined['Price_Clean'] = pd.to_numeric(
            df_combined['Price US'].astype(str).str.replace('[\$,]', '', regex=True),
            errors='coerce'
        )

        if not df_ads.empty and 'Price US' in df_ads.columns:
            df_ads['Price_Clean'] = pd.to_numeric(
                df_ads['Price US'].astype(str).str.replace('[\$,]', '', regex=True),
                errors='coerce'
            )

        if not df_organic.empty and 'Price US' in df_organic.columns:
            df_organic['Price_Clean'] = pd.to_numeric(
                df_organic['Price US'].astype(str).str.replace('[\$,]', '', regex=True),
                errors='coerce'
            )

        # Price statistics table
        price_stats = pd.DataFrame({
            'Statistic': ['Count', 'Mean', 'Median', 'Min', 'Max', 'Std Dev'],
            'All Products': [
                len(df_combined),
                f"${df_combined['Price_Clean'].mean():.2f}",
                f"${df_combined['Price_Clean'].median():.2f}",
                f"${df_combined['Price_Clean'].min():.2f}",
                f"${df_combined['Price_Clean'].max():.2f}",
                f"${df_combined['Price_Clean'].std():.2f}"
            ]
        })

        # Add ads and organic columns if available
        if not df_ads.empty and 'Price_Clean' in df_ads.columns:
            price_stats['Ads Products'] = [
                len(df_ads),
                f"${df_ads['Price_Clean'].mean():.2f}",
                f"${df_ads['Price_Clean'].median():.2f}",
                f"${df_ads['Price_Clean'].min():.2f}",
                f"${df_ads['Price_Clean'].max():.2f}",
                f"${df_ads['Price_Clean'].std():.2f}"
            ]

        if not df_organic.empty and 'Price_Clean' in df_organic.columns:
            price_stats['Organic Products'] = [
                len(df_organic),
                f"${df_organic['Price_Clean'].mean():.2f}",
                f"${df_organic['Price_Clean'].median():.2f}",
                f"${df_organic['Price_Clean'].min():.2f}",
                f"${df_organic['Price_Clean'].max():.2f}",
                f"${df_organic['Price_Clean'].std():.2f}"
            ]

        # Display price statistics table
        st.write("**Price Statistics / 價格統計**")
        st.dataframe(price_stats.set_index('Statistic'), use_container_width=True)

        # Visualizations with Plotly
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Price Distribution / 價格分佈**")

            # Filter out outliers for better visualization
            price_filter = df_combined['Price_Clean'] <= df_combined['Price_Clean'].quantile(0.95)
            filtered_prices = df_combined.loc[price_filter, 'Price_Clean']

            # Create histogram with Plotly
            fig = px.histogram(
                filtered_prices,
                nbins=30,
                labels={'value': 'Price ($)'},
                title='Price Distribution of All Products (95th percentile)',
                opacity=0.8
            )

            # Add KDE line
            fig.add_trace(
                go.Scatter(
                    x=filtered_prices.sort_values(),
                    y=filtered_prices.value_counts(normalize=True, bins=30).sort_index(),
                    mode='lines',
                    name='Density',
                    line=dict(color='red', width=2)
                )
            )

            fig.update_layout(
                xaxis_title='Price ($)',
                yaxis_title='Count',
                height=500,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.write("**Price Comparison: Ads vs Organic / 價格比較：廣告 vs 自然**")
            if not df_ads.empty and not df_organic.empty:
                # Create box plot with Plotly
                ads_filter = df_ads['Price_Clean'] <= df_ads['Price_Clean'].quantile(0.95)
                organic_filter = df_organic['Price_Clean'] <= df_organic['Price_Clean'].quantile(0.95)

                fig = go.Figure()

                fig.add_trace(
                    go.Box(
                        y=df_ads.loc[ads_filter, 'Price_Clean'].values,
                        name='Ads',
                        marker_color='#e74c3c',
                        boxmean=True
                    )
                )

                fig.add_trace(
                    go.Box(
                        y=df_organic.loc[organic_filter, 'Price_Clean'].values,
                        name='Organic',
                        marker_color='#3498db',
                        boxmean=True
                    )
                )

                fig.update_layout(
                    title='Price Comparison: Ads vs Organic Products (95th percentile)',
                    yaxis_title='Price ($)',
                    height=500,
                    hovermode='y unified'
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to compare ads and organic prices")

    except Exception as e:
        st.error(f"Error processing price data: {str(e)}")
        st.error("Make sure your price data is in the correct format")


def create_brand_analysis(df_combined):
    """Brand analysis and visualizations using Plotly"""
    st.subheader("Brand Analysis / 品牌分析")

    if 'Brand' not in df_combined.columns:
        st.warning("Brand data not available in the dataset")
        return

    # Count brands
    brand_counts = df_combined['Brand'].value_counts().reset_index()
    brand_counts.columns = ['Brand', 'Count']

    # Display top brands table
    st.write("**Top Brands / 熱門品牌**")
    st.dataframe(brand_counts.head(10), use_container_width=True)

    # Brand visualization with Plotly
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Brand Distribution / 品牌分佈**")
        # Get top N brands for visualization
        top_n = min(10, len(brand_counts))
        if top_n > 0:
            top_brands = brand_counts.head(top_n)

            # Add "Others" category if there are more brands
            other_count = brand_counts['Count'][top_n:].sum() if len(brand_counts) > top_n else 0
            if other_count > 0:
                others_df = pd.DataFrame([{"Brand": "Others", "Count": other_count}])
                top_brands = pd.concat([top_brands, others_df], ignore_index=True)

            # Create pie chart with Plotly
            fig = px.pie(
                top_brands,
                values='Count',
                names='Brand',
                title=f'Top {top_n} Brands Market Share',
                hole=0.3,  # Create a donut chart
                color_discrete_sequence=px.colors.qualitative.Plotly
            )

            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hoverinfo='label+percent+value'
            )

            fig.update_layout(height=500)

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough brand data for visualization")

    with col2:
        st.write("**Brand Count by Type / 按類型劃分的品牌數量**")
        if 'Organic VS Ads' in df_combined.columns:
            # Count unique brands in each category
            organic_brands = df_combined[df_combined['Organic VS Ads'] == 'Organic']['Brand'].nunique()
            ads_brands = df_combined[df_combined['Organic VS Ads'] == 'Ads']['Brand'].nunique()

            # Create data for bar chart
            brand_type_data = pd.DataFrame({
                'Type': ['Organic', 'Ads'],
                'Unique Brands': [organic_brands, ads_brands]
            })

            # Create bar chart with Plotly
            fig = px.bar(
                brand_type_data,
                x='Type',
                y='Unique Brands',
                title='Unique Brands by Product Type',
                color='Type',
                color_discrete_map={'Organic': '#3498db', 'Ads': '#e74c3c'},
                text='Unique Brands'  # Show values on bars
            )

            fig.update_traces(
                textposition='outside',
                textfont_size=14
            )

            fig.update_layout(
                xaxis_title='',
                yaxis_title='Number of Unique Brands',
                height=500,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Classification data not available for brand type analysis")


def create_ranking_analysis(df_combined):
    """Analysis of product rankings using Plotly"""
    st.subheader("Ranking Analysis / 排名分析")

    # Check if ranking columns exist
    has_bsr = 'BSR' in df_combined.columns
    has_organic_rank = 'Organic Rank' in df_combined.columns
    has_ad_rank = 'Ad Rank' in df_combined.columns

    if not (has_bsr or has_organic_rank or has_ad_rank):
        st.warning("Ranking data not available in the dataset")
        return

    # Show BSR distribution if available
    if has_bsr:
        st.write("**BSR Distribution / BSR 分佈**")

        try:
            # Clean and convert BSR data
            df_combined['BSR_Clean'] = pd.to_numeric(
                df_combined['BSR'].astype(str).str.replace(',', ''),
                errors='coerce'
            )

            # Create BSR bins for analysis
            bsr_bins = [0, 100, 1000, 10000, 100000, float('inf')]
            bin_labels = ['Top 100', '101-1,000', '1,001-10,000', '10,001-100,000', '100,001+']

            df_combined['BSR_Category'] = pd.cut(
                df_combined['BSR_Clean'],
                bins=bsr_bins,
                labels=bin_labels,
                right=False
            )

            # Count products in each BSR category
            bsr_counts = df_combined['BSR_Category'].value_counts().sort_index()

            # Create table
            bsr_table = pd.DataFrame({
                'BSR Range': bsr_counts.index,
                'Count': bsr_counts.values,
                'Percentage': (bsr_counts.values / bsr_counts.sum() * 100).round(2)
            })

            # Display BSR distribution table
            st.dataframe(bsr_table, use_container_width=True)

            # Create bar chart with Plotly
            fig = px.bar(
                bsr_table,
                x='BSR Range',
                y='Count',
                text='Count',
                title='Product Distribution by BSR Range',
                color='BSR Range',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )

            fig.update_traces(
                textposition='outside',
                textfont_size=14
            )

            fig.update_layout(
                xaxis_title='BSR Range',
                yaxis_title='Number of Products',
                height=500,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error processing BSR data: {str(e)}")

    # Compare organic vs ad rankings if available
    if has_organic_rank and has_ad_rank and 'Organic VS Ads' in df_combined.columns:
        st.write("**Organic vs Ads Ranking Analysis / 自然排名 vs 廣告排名分析**")

        try:
            # Get first page products (top results)
            first_page_products = df_combined[df_combined['Sales Rank (ALL)'] <= 48]

            # Count organic vs ads on first page
            first_page_counts = first_page_products['Organic VS Ads'].value_counts()

            # Create comparison table
            col1, col2 = st.columns(2)

            with col1:
                # Create pie chart with Plotly
                fig = px.pie(
                    values=first_page_counts.values,
                    names=first_page_counts.index,
                    title='First Page Product Distribution',
                    color=first_page_counts.index,
                    color_discrete_map={'Organic': '#3498db', 'Ads': '#e74c3c'},
                    hole=0.4
                )

                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hoverinfo='label+percent+value'
                )

                fig.update_layout(height=500)

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Create a metric table
                metrics_data = {
                    'Metric': [
                        'Total First Page Products',
                        'Organic Products',
                        'Ads Products',
                        'Organic Percentage',
                        'Ads Percentage'
                    ],
                    'Value': [
                        len(first_page_products),
                        first_page_counts.get('Organic', 0),
                        first_page_counts.get('Ads', 0),
                        f"{first_page_counts.get('Organic', 0) / len(first_page_products) * 100:.2f}%" if len(
                            first_page_products) > 0 else "0%",
                        f"{first_page_counts.get('Ads', 0) / len(first_page_products) * 100:.2f}%" if len(
                            first_page_products) > 0 else "0%"
                    ]
                }
                metrics_df = pd.DataFrame(metrics_data)
                st.dataframe(metrics_df.set_index('Metric'), use_container_width=True)

        except Exception as e:
            st.error(f"Error processing ranking data: {str(e)}")


def create_rank_distribution_chart(df):
    """Create a rank distribution chart by catalog rank using Plotly"""
    if 'Sales Rank (ALL)' not in df.columns:
        return None

    try:
        # Add rank categories
        conditions = [
            (df['Sales Rank (ALL)'] <= 10),
            (df['Sales Rank (ALL)'] > 10) & (df['Sales Rank (ALL)'] <= 30),
            (df['Sales Rank (ALL)'] > 30) & (df['Sales Rank (ALL)'] <= 50),
            (df['Sales Rank (ALL)'] > 50) & (df['Sales Rank (ALL)'] <= 100),
            (df['Sales Rank (ALL)'] > 100) & (df['Sales Rank (ALL)'] <= 150),
            (df['Sales Rank (ALL)'] > 150) & (df['Sales Rank (ALL)'] <= 200),
            (df['Sales Rank (ALL)'] > 200) & (df['Sales Rank (ALL)'] <= 300),
            (df['Sales Rank (ALL)'] > 300)
        ]

        values = ['#1-10', '#11-30', '31-50', '51-100', '101-150', '151-200', '201-300', '301+']

        df_rank = df.copy()
        df_rank['Rank Category'] = np.select(conditions, values, default='Other')

        # Count by rank category
        rank_counts = df_rank['Rank Category'].value_counts().sort_index()

        rank_data = pd.DataFrame({
            'Rank Range': rank_counts.index,
            'Count': rank_counts.values
        })

        # Create bar chart
        fig = px.bar(
            rank_data,
            x='Rank Range',
            y='Count',
            title='Product Distribution by Rank Range',
            text='Count',
            color='Rank Range',
            color_discrete_sequence=px.colors.qualitative.D3
        )

        fig.update_traces(textposition='outside')

        fig.update_layout(
            xaxis_title='Rank Range',
            yaxis_title='Number of Products',
            height=500,
            showlegend=False
        )

        return fig

    except Exception as e:
        print(f"Error creating rank distribution chart: {str(e)}")
        return None