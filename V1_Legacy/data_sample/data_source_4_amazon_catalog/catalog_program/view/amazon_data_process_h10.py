import streamlit as st
import pandas as pd
import os
from datetime import datetime


def show_page():
    st.title('Amazon Data Process H10 / 亞馬遜數據處理 H10')

    # Just one tab now, no need for tabs at all
    show_process_data_section()


def show_process_data_section():
    """Combined process for uploading, combining files and updating rankings"""
    st.header("Process Helium Xray Files / 處理 Helium Xray 文件")

    # Data privacy notice in both English and Traditional Chinese
    st.warning("""
    **Data Privacy Notice**:
    We do not store or collect any of your data. All processing happens locally in your browser, and your data remains private.

    **數據隱私聲明**：
    我們不儲存或收集您的任何數據。所有處理都在您的瀏覽器中本地進行，您的數據保持私密。
    """)

    # Clear any previous data processing flags if needed
    if 'data_processed' in st.session_state and st.session_state.get('clear_previous', True):
        del st.session_state['data_processed']
        st.session_state['clear_previous'] = False

    st.info("""
    This section combines multiple Helium Xray CSV files into a single dataset and adds ranking classifications.

    本部分將多個 Helium Xray CSV 文件合併為單一數據集，並添加排名分類。
    """)

    # Demo tip
    st.info("""
    💡 **Want to see the final result without uploading files?**

    Go to the **Amazon Catalog Insight** page and click 'View Bed Pillow Market Analysis' to see a full demo.

    💡 **想在不上傳文件的情況下查看最終結果？**

    前往 **Amazon Catalog Insight** 頁面並點擊 'View Bed Pillow Market Analysis' 查看完整演示。
    """)

    # File uploader for multiple files
    uploaded_files = st.file_uploader("Upload Helium Xray CSV files / 上傳 Helium Xray CSV 文件",
                                      type=['csv'],
                                      accept_multiple_files=True,
                                      key="combine_files_uploader")

    if uploaded_files:
        st.write(f"Uploaded {len(uploaded_files)} files / 已上傳 {len(uploaded_files)} 個文件")

        # Display file names
        with st.expander("View uploaded files / 查看已上傳文件"):
            for file in uploaded_files:
                st.write(f"- {file.name}")

        # Process button
        if st.button("Process Files / 處理文件"):
            with st.spinner("Processing files... / 處理文件中..."):
                try:
                    # Step 1: Combine files
                    combined_df, date_str, week_number, file_info = combine_files(uploaded_files)

                    # Show file processing summary
                    st.subheader("File Processing Summary / 文件處理摘要")
                    with st.expander("View processing details / 查看處理詳情"):
                        for info in file_info:
                            st.write(f"- {info['filename']}: {info['rows']} rows, {info['columns']} columns")

                    # Store in session state
                    st.session_state['combined_df'] = combined_df
                    st.session_state['file_date'] = date_str
                    st.session_state['week_number'] = week_number

                    # Show sample of combined data
                    st.success(
                        f"Successfully combined {len(file_info)} files into {len(combined_df)} rows. / 成功合併 {len(file_info)} 個文件為 {len(combined_df)} 行。")
                    st.subheader("Preview of Combined Data / 合併數據預覽")

                    # Show a small sample to avoid display issues
                    with st.expander("View combined data sample / 查看合併數據示例"):
                        # Show just 5 rows and limited columns for clear display
                        display_cols = select_important_columns(combined_df)
                        st.dataframe(combined_df[display_cols].head(5))
                        st.caption("Showing first 5 rows with key columns / 顯示前 5 行和關鍵列")

                    # Display basic info
                    st.info(
                        f"Combined data contains {len(combined_df)} rows and {len(combined_df.columns)} columns. / 合併數據包含 {len(combined_df)} 行和 {len(combined_df.columns)} 列。")

                    # Step 2: Automatically update rankings
                    st.write("---")
                    st.subheader("Updating Rankings... / 更新排名中...")

                    # Update rankings with progress indicator
                    progress_bar = st.progress(0)
                    updated_df = update_rank_columns(combined_df, progress_callback=progress_bar)
                    progress_bar.empty()

                    # Create three dataframes and store them in session state
                    create_analysis_dataframes(updated_df)

                    # Store updated data in session state
                    st.session_state['updated_df'] = updated_df

                    # Set a flag indicating data is processed and ready for analysis
                    st.session_state['data_processed'] = True

                    # Store additional metadata for better analysis context
                    st.session_state['processing_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state['processed_files_count'] = len(file_info)
                    st.session_state['processed_rows_count'] = len(updated_df)
                    st.session_state['processed_columns'] = list(updated_df.columns)

                    # Show sample of updated data
                    st.success(
                        "Successfully updated rankings and created analysis dataframes. / 成功更新排名並創建分析數據框。")

                    # Display counts with metrics
                    organic_count = (updated_df['Organic VS Ads'] == 'Organic').sum()
                    ads_count = (updated_df['Organic VS Ads'] == 'Ads').sum()

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Products / 總產品數", len(updated_df))
                    with col2:
                        st.metric("Organic Products / 自然產品數", organic_count)
                    with col3:
                        st.metric("Ads Products / 廣告產品數", ads_count)

                    # Display preview of the three dataframes
                    st.subheader("Preview of Analysis DataFrames / 分析數據框預覽")

                    # Create three tabs for the three dataframes
                    tab1, tab2, tab3 = st.tabs([
                        "Ads Products (DF1) / 廣告產品",
                        "Organic Products (DF2) / 自然產品",
                        "Combined Data (DF3) / 合併數據"
                    ])

                    # Select important columns for display
                    with tab1:
                        if 'df_ads' in st.session_state:
                            ads_df = st.session_state['df_ads']
                            display_cols = select_important_columns(ads_df)
                            st.write(f"Ads Products: {len(ads_df)} rows / 廣告產品：{len(ads_df)} 行")
                            st.dataframe(ads_df[display_cols].head(5))

                    with tab2:
                        if 'df_organic' in st.session_state:
                            organic_df = st.session_state['df_organic']
                            display_cols = select_important_columns(organic_df)
                            st.write(f"Organic Products: {len(organic_df)} rows / 自然產品：{len(organic_df)} 行")
                            st.dataframe(organic_df[display_cols].head(5))

                    with tab3:
                        display_cols = select_important_columns(updated_df)
                        st.write(f"Combined Data: {len(updated_df)} rows / 合併數據：{len(updated_df)} 行")
                        st.dataframe(updated_df[display_cols].head(5))

                    # Download buttons for all three dataframes - moved outside the processor
                    st.session_state['download_ready'] = True

                    # Store filenames in session state for consistent download options
                    st.session_state['ads_filename'] = f"Week{week_number}_{date_str}_ads.csv"
                    st.session_state['organic_filename'] = f"Week{week_number}_{date_str}_organic.csv"
                    st.session_state['combined_filename'] = f"Week{week_number}_{date_str}_combined_updated.csv"

                    # Instead of the "Proceed to Analysis" section, add instructions
                    st.write("---")
                    st.info("""
                    ### Next Steps

                    To analyze your processed data, please go to the **Amazon Catalog Insight** page from the navigation menu.

                    ### 下一步

                    要分析您的處理數據，請從導航菜單前往 **Amazon Catalog Insight** 頁面。
                    """)

                except Exception as e:
                    st.error(f"Error processing files: {str(e)} / 處理文件時出錯：{str(e)}")
                    # Show more detailed error information
                    import traceback
                    st.error(traceback.format_exc())

    # Show download options only if data has been processed
    if st.session_state.get('download_ready', False):
        show_download_options()


def show_download_options():
    """Show download options for all three dataframes"""
    st.write("---")
    st.subheader("Download Options / 下載選項")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Download ads dataframe
        if 'df_ads' in st.session_state:
            ads_df = st.session_state['df_ads']
            ads_csv = convert_df_to_csv(ads_df)
            ads_filename = st.session_state.get('ads_filename', "ads_data.csv")

            st.download_button(
                label="Download Ads CSV / 下載廣告數據 CSV",
                data=ads_csv,
                file_name=ads_filename,
                mime="text/csv",
                key="download_ads"
            )

    with col2:
        # Download organic dataframe
        if 'df_organic' in st.session_state:
            organic_df = st.session_state['df_organic']
            organic_csv = convert_df_to_csv(organic_df)
            organic_filename = st.session_state.get('organic_filename', "organic_data.csv")

            st.download_button(
                label="Download Organic CSV / 下載自然數據 CSV",
                data=organic_csv,
                file_name=organic_filename,
                mime="text/csv",
                key="download_organic"
            )

    with col3:
        # Download combined dataframe
        if 'df_combined' in st.session_state:
            combined_df = st.session_state['df_combined']
            combined_csv = convert_df_to_csv(combined_df)
            combined_filename = st.session_state.get('combined_filename', "combined_data.csv")

            st.download_button(
                label="Download Combined CSV / 下載合併數據 CSV",
                data=combined_csv,
                file_name=combined_filename,
                mime="text/csv",
                key="download_combined"
            )


def select_important_columns(df):
    """Select the most important columns for display to avoid overflow"""
    priority_columns = [
        'Display Order', 'Product Details', 'ASIN', 'Brand', 'Price US',
        'BSR', 'Organic VS Ads', 'Sales Rank (ALL)',
        'Organic Rank', 'Ad Rank', 'Source Files'
    ]

    # Return only columns that exist in the dataframe
    return [col for col in priority_columns if col in df.columns]


def create_analysis_dataframes(df):
    """
    Create three dataframes for analysis and store them in session state:
    - df_ads: DataFrame containing only ads products
    - df_organic: DataFrame containing only organic products
    - df_combined: Complete DataFrame with both ads and organic products
    """
    if 'Organic VS Ads' not in df.columns:
        st.warning("Classification column not found - cannot split data / 找不到分類列 - 無法拆分數據")
        return

    # Create ads dataframe (DF1)
    ads_df = df[df['Organic VS Ads'] == 'Ads'].copy()

    # Create organic dataframe (DF2)
    organic_df = df[df['Organic VS Ads'] == 'Organic'].copy()

    # DF3 is just the complete dataframe (df)

    # Store all three in session state
    st.session_state['df_ads'] = ads_df
    st.session_state['df_organic'] = organic_df
    st.session_state['df_combined'] = df

    # Log info about created dataframes
    st.success(f"""
    Created three dataframes for analysis:
    - Ads Products (DF1): {len(ads_df)} rows
    - Organic Products (DF2): {len(organic_df)} rows
    - Combined (DF3): {len(df)} rows

    已創建三個用於分析的數據框：
    - 廣告產品 (DF1)：{len(ads_df)} 行
    - 自然產品 (DF2)：{len(organic_df)} 行
    - 合併 (DF3)：{len(df)} 行
    """)


# Helper Functions

def combine_files(uploaded_files):
    """Combine multiple uploaded CSV files with improved error handling and sequential Display Order"""
    all_dataframes = []
    file_info = []

    # Get filenames for date detection
    filenames = [file.name for file in uploaded_files]
    date_str, week_number = detect_date_from_filenames(filenames)

    # Log what we're about to process
    st.write(f"Processing {len(uploaded_files)} files...")

    # Track successful and failed files
    success_count = 0
    failed_files = []
    current_display_order = 1  # Start Display Order from 1

    for i, file in enumerate(uploaded_files):
        try:
            # Read CSV and add source file column
            st.write(f"Reading file {i + 1}/{len(uploaded_files)}: {file.name}")
            df = pd.read_csv(file)
            rows_count = len(df)
            cols_count = len(df.columns)
            st.write(f"- Read {rows_count} rows and {cols_count} columns")

            # Check if 'Display Order' exists and update it to be sequential across all files
            if 'Display Order' in df.columns:
                # Replace the Display Order with sequential numbers
                df['Display Order'] = range(current_display_order, current_display_order + len(df))
                # Update the next starting point
                current_display_order += len(df)

            # Add source information
            df['Source Files'] = file.name
            all_dataframes.append(df)

            # Keep track of information about each file
            file_info.append({
                'filename': file.name,
                'rows': rows_count,
                'columns': cols_count
            })

            success_count += 1

        except Exception as e:
            st.error(f"Error processing file {file.name}: {str(e)}")
            failed_files.append(file.name)

    if len(all_dataframes) == 0:
        raise ValueError("No files could be processed successfully")

    # Show summary before combining
    st.write(f"Successfully read {success_count} files out of {len(uploaded_files)}")
    if failed_files:
        st.warning(f"Failed to process {len(failed_files)} files: {', '.join(failed_files)}")

    # Combine all dataframes
    st.write("Combining dataframes...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    st.write(f"Combined data has {len(combined_df)} rows and {len(combined_df.columns)} columns")

    # Verify all files are represented in the combined dataframe
    source_files_in_df = combined_df['Source Files'].unique()
    st.write(f"Combined data contains {len(source_files_in_df)} unique source files")

    # Verify Display Order is properly sequential
    if 'Display Order' in combined_df.columns:
        min_order = combined_df['Display Order'].min()
        max_order = combined_df['Display Order'].max()
        st.write(f"Display Order ranges from {min_order} to {max_order}")

        # Check if display order is properly sequential
        expected_count = max_order - min_order + 1
        actual_count = len(combined_df)
        if expected_count != actual_count:
            st.warning(
                f"Display Order may have gaps or duplicates. Expected {expected_count} values, got {actual_count}.")

    return combined_df, date_str, week_number, file_info


def detect_date_from_filenames(filenames):
    """Extract date and week number from filenames"""
    for filename in filenames:
        # Try to extract date from Helium_10_Xray_YYYY-MM-DD format
        if "Helium_10_Xray_" in filename:
            parts = filename.split('_')
            if len(parts) >= 4:
                date_part = parts[3]
                try:
                    # Extract just the date part (not time)
                    date_only = date_part.split('-', 3)[:3]
                    date_str = '-'.join(date_only)
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    return date_str, file_date.isocalendar()[1]
                except ValueError:
                    continue

    # Try another pattern for your specific files (YYYYMMDD)
    for filename in filenames:
        if "Helium_10_Xray_" in filename:
            parts = filename.split('_')
            if len(parts) >= 4:
                date_part = parts[3][:8]  # Extract first 8 chars (YYYYMMDD)
                try:
                    file_date = datetime.strptime(date_part, '%Y%m%d')
                    date_str = file_date.strftime('%Y-%m-%d')
                    return date_str, file_date.isocalendar()[1]
                except ValueError:
                    continue

    # If no valid date found, use today's date
    today = datetime.now()
    return today.strftime('%Y-%m-%d'), today.isocalendar()[1]


def update_rank_columns(df, progress_callback=None):
    """
    Update ranking columns and add Organic vs Ads classification
    without modifying original columns
    """
    # Create a copy to avoid modifying the original
    df_updated = df.copy()
    total_steps = 6
    current_step = 0

    # Ensure Source Files column exists (should be added during combine step)
    if 'Source Files' not in df_updated.columns:
        df_updated['Source Files'] = "Unknown"

    if progress_callback:
        current_step += 1
        progress_callback.progress(current_step / total_steps)

    # Clean numeric columns by removing commas and converting to numeric types
    numeric_columns = [
        'Parent Level Sales', 'ASIN Sales', 'Recent Purchases',
        'Parent Level Revenue', 'ASIN Revenue', 'BSR', 'Review Count'
    ]

    for col in numeric_columns:
        if col in df_updated.columns:
            # Replace commas and convert to numeric
            df_updated[col] = pd.to_numeric(
                df_updated[col].astype(str).str.replace(',', ''),
                errors='coerce'
            )

    if progress_callback:
        current_step += 1
        progress_callback.progress(current_step / total_steps)

    # Add Sales Rank (ALL) - starting from 1 to max rows
    df_updated['Sales Rank (ALL)'] = range(1, len(df_updated) + 1)

    if progress_callback:
        current_step += 1
        progress_callback.progress(current_step / total_steps)

    # Add Organic VS Ads classification
    df_updated['Organic VS Ads'] = df_updated['Product Details'].apply(
        lambda x: 'Ads' if '($)' in str(x) else 'Organic'
    )

    if progress_callback:
        current_step += 1
        progress_callback.progress(current_step / total_steps)

    # Initialize Organic Rank and Ad Rank columns
    df_updated['Organic Rank'] = pd.NA
    df_updated['Ad Rank'] = pd.NA

    if progress_callback:
        current_step += 1
        progress_callback.progress(current_step / total_steps)

    # Create separate rankings
    organic_mask = df_updated['Organic VS Ads'] == 'Organic'
    ads_mask = df_updated['Organic VS Ads'] == 'Ads'

    # Assign rankings - start from 1 for each type
    df_updated.loc[organic_mask, 'Organic Rank'] = range(1, organic_mask.sum() + 1)
    df_updated.loc[ads_mask, 'Ad Rank'] = range(1, ads_mask.sum() + 1)

    if progress_callback:
        current_step += 1
        progress_callback.progress(current_step / total_steps)

    return df_updated


def convert_df_to_csv(df):
    """Convert dataframe to CSV for download"""
    return df.to_csv(index=False).encode('utf-8')


def display_df_info(df):
    """Display basic dataframe information"""
    st.write(f"Data Shape / 數據形狀: {df.shape[0]} rows × {df.shape[1]} columns")

    # Display preview with top 5 and last 5 rows
    with st.expander("Data Preview / 數據預覽"):
        if len(df) <= 10:
            st.dataframe(df)
        else:
            # Create a new dataframe with top 5 and last 5 rows
            preview_df = pd.concat([df.head(5), df.tail(5)])
            st.dataframe(preview_df)
            st.caption("Showing top 5 and last 5 rows / 顯示前 5 行和後 5 行")


if __name__ == "__main__":
    show_page()