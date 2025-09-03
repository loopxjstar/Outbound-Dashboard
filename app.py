import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from src.data_processor import DataProcessor
from src.database import DatabaseManager
from src.calls_processor import CallsProcessor
from src.combined_processor import CombinedProcessor

# Configure page
st.set_page_config(
    page_title="CSV Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_processor' not in st.session_state:
    st.session_state.data_processor = DataProcessor()
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'calls_processor' not in st.session_state:
    st.session_state.calls_processor = CallsProcessor()
if 'combined_processor' not in st.session_state:
    st.session_state.combined_processor = CombinedProcessor()

def main():
    # Create a container at the top for consistent focus
    header_container = st.container()
    with header_container:
        st.title("📊 Communication Analytics Dashboard")
        st.markdown("Upload your CSV files and analyze email and call trends across different time periods")
    
    # Create main navigation tabs
    email_tab, calls_tab, combined_tab = st.tabs(["📧 Email Analytics", "📞 Calls Analytics", "📊 Combined Analytics"])
    
    with email_tab:
        show_email_dashboard()
    
    with calls_tab:
        show_calls_dashboard()
    
    with combined_tab:
        show_combined_dashboard()

def show_email_dashboard():
    """Handle the multi-SDR email analytics dashboard with card-based UI"""
    
    # Initialize SDR data in session state if not present
    if 'sdr_data' not in st.session_state:
        st.session_state.sdr_data = {}
    if 'num_sdrs' not in st.session_state:
        st.session_state.num_sdrs = 1  # Start with 1 SDR card
    
    # Sidebar for demo/upload choice
    with st.sidebar:
        st.header("📧 Email Data")
        
        # Pre-processed vs Upload choice
        data_source = st.radio(
            "Choose data source:",
            ["📂 Use Pre-processed Data", "📤 Upload Multiple SDR Files"],
            index=0,  # Default to demo files
            key="email_data_source"
        )
        
        if data_source == "📂 Use Pre-processed Data":
            st.success("✅ Using pre-processed data")
            st.info("Loads processed email data from `data/processed_files/`")
            
            # Pre-processed data loading button
            if st.button("Load Pre-processed Data", type="primary", key="load_demo_email"):
                load_demo_data_multi_sdr()
    
    # Main area for multi-SDR file upload
    if data_source == "📤 Upload Multiple SDR Files":
        st.header("📊 Multi-SDR Data Upload")
        st.info("Upload Send and Open files for each SDR separately. They will be joined individually then combined.")
        
        # Add/Remove SDR controls
        col1, col2, col3, col4 = st.columns([2, 1, 1, 4])
        with col1:
            st.markdown("### 👥 SDR Management")
        with col2:
            if st.button("➕ Add SDR", key="add_sdr"):
                st.session_state.num_sdrs = min(st.session_state.num_sdrs + 1, 10)  # Max 10 SDRs
                st.rerun()
        with col3:
            if st.button("➖ Remove SDR", key="remove_sdr"):
                if st.session_state.num_sdrs > 1:
                    st.session_state.num_sdrs -= 1
                    # Remove the last SDR's data
                    sdr_key = f"sdr_{st.session_state.num_sdrs}"
                    if sdr_key in st.session_state.sdr_data:
                        del st.session_state.sdr_data[sdr_key]
                    st.rerun()
        
        st.divider()
        
        # Create card layout for SDRs
        num_cols = min(3, st.session_state.num_sdrs)  # Max 3 columns per row
        sdr_cards_data = []
        
        for i in range(st.session_state.num_sdrs):
            sdr_cards_data.append(i)
        
        # Process SDRs in rows of 3
        for row_start in range(0, len(sdr_cards_data), 3):
            cols = st.columns(min(3, len(sdr_cards_data) - row_start))
            
            for col_idx, sdr_idx in enumerate(sdr_cards_data[row_start:row_start + 3]):
                with cols[col_idx]:
                    with st.container(border=True):
                        # Card header with status icon
                        sdr_key = f"sdr_{sdr_idx}"
                        sdr_info = st.session_state.sdr_data.get(sdr_key, {})
                        
                        # Check if SDR is ready
                        is_ready = (sdr_info.get('name') and 
                                   sdr_info.get('send_file') is not None and 
                                   sdr_info.get('open_file') is not None)
                        
                        # Card title with status
                        if is_ready:
                            st.markdown(f"### ✅ SDR {sdr_idx + 1}")
                        else:
                            st.markdown(f"### 👤 SDR {sdr_idx + 1}")
                        
                        # SDR Name input
                        sdr_name = st.text_input(
                            "SDR Name",
                            value=sdr_info.get('name', ''),
                            key=f"sdr_name_{sdr_idx}",
                            placeholder="e.g., John Smith"
                        )
                        
                        # Send file uploader
                        send_file = st.file_uploader(
                            "📤 Send Mails CSV",
                            type=['csv'],
                            key=f"send_{sdr_idx}"
                        )
                        
                        # Open file uploader
                        open_file = st.file_uploader(
                            "📥 Open Mails CSV",
                            type=['csv'],
                            key=f"open_{sdr_idx}"
                        )
                        
                        # Store SDR data in session state
                        st.session_state.sdr_data[sdr_key] = {
                            'name': sdr_name,
                            'send_file': send_file,
                            'open_file': open_file,
                            'index': sdr_idx
                        }
                        
                        # Status indicator
                        if is_ready:
                            st.success("Ready to process")
                        elif sdr_name and (send_file or open_file):
                            missing = []
                            if not send_file:
                                missing.append("Send file")
                            if not open_file:
                                missing.append("Open file")
                            st.warning(f"Missing: {', '.join(missing)}")
                        elif sdr_name:
                            st.info("Upload both files")
                        else:
                            st.info("Enter SDR name")
        
        # Processing section
        st.divider()
        
        # Count ready SDRs
        ready_sdrs = [sdr for sdr in st.session_state.sdr_data.values() 
                      if sdr.get('name') and sdr.get('send_file') and sdr.get('open_file')]
        
        # Summary and process button
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            if ready_sdrs:
                st.success(f"📊 {len(ready_sdrs)} SDR(s) ready to process")
            else:
                st.warning("No SDRs ready - please complete at least one SDR card")
        
        with col2:
            st.info("📋 **Contacts CSV**: Using `data/contacts.csv`")
        
        with col3:
            if st.button("🚀 Process All SDRs", 
                        type="primary", 
                        disabled=len(ready_sdrs) == 0,
                        key="process_multi_sdr"):
                process_multi_sdr_data(ready_sdrs)
    
    # Main email dashboard
    if 'successful_data' in st.session_state:
        show_dashboard()
    else:
        if data_source == "📤 Upload Multiple SDR Files":
            show_multi_sdr_welcome()
        else:
            show_welcome_message()

def show_calls_dashboard():
    """Handle the simple calls analytics dashboard"""
    # Sidebar for demo/upload choice and calls file upload
    with st.sidebar:
        st.header("📞 Calls Data")
        
        # Pre-processed vs Upload choice
        data_source = st.radio(
            "Choose data source:",
            ["📂 Use Pre-processed Data", "📤 Upload My Files"],
            index=0,  # Default to demo files
            key="calls_data_source"
        )
        
        if data_source == "📂 Use Pre-processed Data":
            st.success("✅ Using pre-processed calls data")
            st.info("Loads processed calls data from `data/processed_files/`")
            
            # Pre-processed data loading button
            if st.button("Load Pre-processed Data", type="primary", key="load_demo_calls"):
                load_demo_data_calls()
                
        else:  # Upload My Files
            st.header("📞 Calls File Upload")
            
            # Single calls file uploader
            calls_file = st.file_uploader("Upload Calls Record CSV", type=['csv'], key='calls_record')
            
            # Process calls file button
            if st.button("Process Calls File", type="primary", key="process_calls_file"):
                if calls_file:
                    with st.spinner("Processing calls file..."):
                        try:
                            # Process the calls data
                            is_valid, error_messages, calls_data = st.session_state.calls_processor.process_calls_file(calls_file)
                            
                            if is_valid:
                                # Store in session state (separate from email data)
                                st.session_state.calls_data = calls_data
                                
                                st.success(f"Calls file processed successfully!")
                                st.info(f"📞 **Processing Summary:**\n"
                                       f"- Total call records: {len(calls_data):,}\n"
                                       f"- Required columns: ✅ All present")
                                
                                st.rerun()
                            else:
                                # Show validation errors
                                st.error("**Calls File Validation Failed**")
                                for error in error_messages:
                                    st.error(error)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please upload a Calls Record CSV file")
    
    # Main calls dashboard content
    if 'calls_data' in st.session_state:
        show_calls_analytics()
    else:
        show_calls_welcome_message()

def show_calls_welcome_message():
    """Welcome message for calls section"""
    st.info("👆 Upload your Calls Record CSV file using the sidebar to get started")
    
    # Show expected calls file format
    with st.expander("📋 Expected Calls CSV File Format"):
        st.subheader("Calls Record CSV")
        st.markdown("**Required columns:**")
        st.code("""
Assigned,Call Disposition,Date,Company / Account,Contact,Call Duration (seconds)
John Smith,Interested,2025-07-02 14:30:00,Acme Corp,jane@acme.com,180
Jane Doe,Not Interested,2025-07-02 15:15:00,Tech Solutions,bob@tech.com,120
        """)
        
        st.markdown("**Column Descriptions:**")
        st.write("- **Assigned**: Person assigned to make the call")
        st.write("- **Call Disposition**: Result/outcome of the call")
        st.write("- **Date**: Date and time of the call")
        st.write("- **Company / Account**: Company name or account")
        st.write("- **Contact**: Contact person (usually email)")
        st.write("- **Call Duration (seconds)**: Duration in seconds")

def show_calls_analytics():
    """Show simplified calls analytics dashboard with hierarchical filtering"""
    calls_data = st.session_state.calls_data
    
    st.subheader("📞 Calls Analytics Dashboard")
    
    # File Summary Row (before filters - shows complete uploaded file stats)
    show_file_summary(calls_data)
    
    # Hierarchical Filtering System
    st.subheader("📊 Filters")
    
    # Step 1: Assigned Filter
    col1, col2 = st.columns(2)
    
    with col1:
        assigned_list = ['All'] + sorted(calls_data['Assigned'].dropna().unique().tolist())
        selected_assigned = st.selectbox(
            "👤 Assigned",
            assigned_list,
            key="assigned_filter"
        )
    
    # Filter by Assigned first
    if selected_assigned != 'All':
        filtered_data_step1 = calls_data[calls_data['Assigned'] == selected_assigned]
    else:
        filtered_data_step1 = calls_data.copy()
    
    with col2:
        # Step 2: Date Range Filter (on assigned-filtered data)
        if len(filtered_data_step1) > 0 and 'Date' in filtered_data_step1.columns:
            min_date = filtered_data_step1['Date'].min().date()
            max_date = filtered_data_step1['Date'].max().date()
            
            date_range = st.date_input(
                "📅 Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="calls_date_filter"
            )
        else:
            date_range = None
    
    # Apply date filter
    if date_range and len(date_range) == 2:
        filtered_data_step2 = filtered_data_step1[
            (filtered_data_step1['Date'].dt.date >= date_range[0]) & 
            (filtered_data_step1['Date'].dt.date <= date_range[1])
        ]
    else:
        filtered_data_step2 = filtered_data_step1.copy()
    
    # Step 3: Call Disposition and Company Filters (on date-filtered data)
    col3, col4 = st.columns(2)
    
    with col3:
        if len(filtered_data_step2) > 0:
            dispositions = ['All'] + sorted(filtered_data_step2['Call Disposition'].dropna().unique().tolist())
            selected_disposition = st.selectbox(
                "📞 Call Disposition",
                dispositions,
                key="disposition_filter"
            )
        else:
            selected_disposition = 'All'
    
    with col4:
        if len(filtered_data_step2) > 0:
            companies = ['All'] + sorted(filtered_data_step2['Company / Account'].dropna().unique().tolist())
            selected_company = st.selectbox(
                "🏢 Company / Account",
                companies,
                key="company_filter"
            )
        else:
            selected_company = 'All'
    
    # Apply final filters
    filtered_data_final = filtered_data_step2.copy()
    
    if selected_disposition != 'All':
        filtered_data_final = filtered_data_final[filtered_data_final['Call Disposition'] == selected_disposition]
    
    if selected_company != 'All':
        filtered_data_final = filtered_data_final[filtered_data_final['Company / Account'] == selected_company]
    
    # Show filter summary
    st.info(f"📞 Showing {len(filtered_data_final):,} call records (filtered from {len(calls_data):,} total)")
    
    # Show KPIs only - no individual records
    show_simple_calls_kpis(filtered_data_final)
    
    # Show filtered call records table
    show_calls_data_table(filtered_data_final)

def show_file_summary(data):
    """Display file-level summary statistics (no filters applied)"""
    st.subheader("📋 File Summary")
    
    # Create 3 columns for the summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_records = len(data)
        st.metric(
            "Total Records", 
            f"{total_records:,}", 
            help="Total number of call records in the uploaded file"
        )
    
    with col2:
        unique_companies = data['Company / Account'].nunique() if 'Company / Account' in data.columns else 0
        st.metric(
            "Unique Companies", 
            f"{unique_companies:,}", 
            help="Number of unique companies/accounts in the file"
        )
    
    with col3:
        # Calculate connect rate (records with "Connected" disposition)
        if 'Call Disposition' in data.columns:
            connected_records = len(data[data['Call Disposition'].str.strip().str.lower() == 'connected'])
            connect_rate = (connected_records / total_records * 100) if total_records > 0 else 0
            st.metric(
                "Connect Rate", 
                f"{connect_rate:.1f}%", 
                delta=f"{connected_records} connected",
                help="Percentage of calls with 'Connected' disposition"
            )
        else:
            st.metric(
                "Connect Rate", 
                "N/A", 
                help="Call Disposition column not available"
            )
    
    # Add a separator line
    st.divider()

def show_simple_calls_kpis(data):
    """Display simple calls KPI cards - numbers only, no individual records"""
    st.subheader("📈 Call Metrics")
    
    if len(data) == 0:
        st.warning("No data available for the selected filters")
        return
    
    # Create KPI columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_calls = len(data)
        st.metric("Total Calls", f"{total_calls:,}", help="Total number of calls in filtered data")
    
    with col2:
        unique_companies = data['Company / Account'].nunique() if 'Company / Account' in data.columns else 0
        st.metric("Unique Companies", f"{unique_companies:,}", help="Number of unique companies called")
    
    with col3:
        # Connect Rate for filtered data
        if 'Call Disposition' in data.columns and len(data) > 0:
            connected_records = len(data[data['Call Disposition'].str.strip().str.lower() == 'connected'])
            connect_rate = (connected_records / len(data) * 100) if len(data) > 0 else 0
            st.metric(
                "Connect Rate", 
                f"{connect_rate:.1f}%", 
                delta=f"{connected_records} connected",
                help="Percentage of filtered calls with 'Connected' disposition"
            )
        else:
            st.metric("Connect Rate", "N/A", help="Call Disposition data not available")
    
    with col4:
        if 'Call Duration (seconds)' in data.columns:
            total_duration = data['Call Duration (seconds)'].sum()
            total_hours = total_duration / 3600
            st.metric("Total Duration", f"{total_hours:.1f} hrs", help="Total time spent on calls")
        else:
            st.metric("Total Duration", "N/A", help="Duration data not available")
    
    # Second row of KPIs
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        unique_contacts = data['Contact'].nunique() if 'Contact' in data.columns else 0
        st.metric("Unique Contacts", f"{unique_contacts:,}", help="Number of unique contacts called")
    
    with col6:
        # Most common disposition
        if 'Call Disposition' in data.columns and len(data) > 0:
            top_disposition = data['Call Disposition'].mode().iloc[0] if len(data['Call Disposition'].mode()) > 0 else "N/A"
            disposition_count = len(data[data['Call Disposition'] == top_disposition]) if top_disposition != "N/A" else 0
            st.metric("Top Disposition", f"{top_disposition}", delta=f"{disposition_count} calls", help="Most common call disposition")
        else:
            st.metric("Top Disposition", "N/A", help="Disposition data not available")
    
    with col7:
        # Disposition distribution
        if 'Call Disposition' in data.columns and len(data) > 0:
            unique_dispositions = data['Call Disposition'].nunique()
            st.metric("Disposition Types", f"{unique_dispositions:,}", help="Number of different dispositions")
        else:
            st.metric("Disposition Types", "N/A", help="Disposition data not available")
    
    with col8:
        # Daily average (if date range is selected)
        if 'Date' in data.columns and len(data) > 0:
            date_range = data['Date'].max() - data['Date'].min()
            days = max(date_range.days, 1)  # At least 1 day
            daily_avg = len(data) / days
            st.metric("Daily Avg", f"{daily_avg:.1f}", help="Average calls per day in the selected period")
        else:
            st.metric("Daily Avg", "N/A", help="Date data not available")

def show_calls_data_table(data):
    """Display filtered call records table with all columns"""
    st.subheader("📋 Filtered Call Records")
    
    if len(data) == 0:
        st.warning("No call records match the selected filters")
        return
    
    # Sort options
    col1, col2, col3 = st.columns([2, 2, 4])
    
    with col1:
        # Sort column selector
        sort_columns = ['Date', 'Assigned', 'Call Disposition', 'Company / Account', 'Call Duration (seconds)']
        available_sort_columns = [col for col in sort_columns if col in data.columns]
        
        sort_column = st.selectbox(
            "Sort by:",
            available_sort_columns,
            key="calls_table_sort"
        )
    
    with col2:
        # Sort order
        sort_ascending = st.selectbox(
            "Order:",
            ["Descending", "Ascending"],
            key="calls_table_order"
        ) == "Ascending"
    
    # Apply sorting
    if sort_column and sort_column in data.columns:
        data_sorted = data.sort_values(sort_column, ascending=sort_ascending)
    else:
        data_sorted = data.copy()
    
    # Display the table with all columns
    st.dataframe(
        data_sorted,
        use_container_width=True,
        height=400
    )
    
    # Show record count
    st.caption(f"Showing {len(data_sorted):,} call records")
    
    # Download button
    csv = data_sorted.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Call Records",
        data=csv,
        file_name=f"filtered_call_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="download_calls"
    )


def load_demo_data_email():
    """Load demo data for Email Analytics tab"""
    import os
    
    try:
        # Define demo file paths
        demo_files = {
            'send_mails': 'data/send_data.csv',
            'open_mails': 'data/open_data.csv', 
            'contacts': 'data/contacts.csv'
        }
        
        # Check if demo files exist
        missing_files = []
        for file_key, file_path in demo_files.items():
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            st.error(f"❌ Demo files not found: {', '.join(missing_files)}")
            return
            
        with st.spinner("Loading demo data..."):
            # Process demo files through the same pipeline as uploaded files
            result = st.session_state.data_processor.process_files(demo_files)
            
            if len(result) == 6:
                successful_data, failed_data, validation_errors, original_send_count, send_df, send_open_df = result
            elif len(result) == 4:
                successful_data, failed_data, validation_errors, original_send_count = result
                send_df, send_open_df = None, None
            elif len(result) == 3:
                successful_data, failed_data, validation_errors = result
                original_send_count = len(successful_data) if successful_data is not None else 0
                send_df, send_open_df = None, None
            else:
                successful_data, failed_data = result
                validation_errors = []
                original_send_count = len(successful_data) if successful_data is not None else 0
                send_df, send_open_df = None, None
            
            if successful_data is not None:
                # Store in session state (same as uploaded files)
                st.session_state.successful_data = successful_data
                st.session_state.failed_data = failed_data
                st.session_state.original_send_count = original_send_count
                st.session_state.send_df = send_df
                st.session_state.send_open_df = send_open_df
                
                # Show success message
                total_processed = len(successful_data) + len(failed_data)
                success_rate = len(successful_data) / total_processed * 100 if total_processed > 0 else 0
                
                st.success(f"✅ Demo data loaded successfully!")
                st.info(f"📊 **{len(successful_data):,}** successful records ({success_rate:.1f}% success rate)")
                
                if validation_errors:
                    with st.expander("⚠️ Validation Issues", expanded=False):
                        for error in validation_errors:
                            st.warning(error)
            else:
                st.error("❌ Failed to process demo data")
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                        
    except Exception as e:
        st.error(f"❌ Error loading demo data: {str(e)}")

def load_demo_data_calls():
    """Load pre-processed demo calls data from processed_files folder"""
    import os
    import json
    
    try:
        st.info("🔄 Loading pre-processed calls data...")
        
        # Check if processed files exist
        processed_calls_file = 'data/processed_files/processed_calls_data.csv'
        metadata_file = 'data/processed_files/preprocessing_metadata.json'
        
        if not os.path.exists(processed_calls_file):
            st.error("❌ Pre-processed calls data not found!")
            st.info("🔧 Please run the preprocessing script first: `python preprocess_data.py`")
            return
        
        # Load processed calls data
        calls_data = pd.read_csv(processed_calls_file)
        
        # Load metadata if exists
        metadata = {}
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        # Parse datetime columns if they exist
        date_columns = ['Date', 'date', 'call_date']  # Common call date column names
        for col in date_columns:
            if col in calls_data.columns:
                try:
                    calls_data[col] = pd.to_datetime(calls_data[col])
                    break  # Only convert the first matching column
                except:
                    continue
        
        # Store in session state
        st.session_state.calls_data = calls_data
        
        # Calculate metrics from metadata or data
        total_calls = len(calls_data)
        
        st.success(f"✅ Pre-processed calls data loaded successfully!")
        
        # Show processing summary
        processing_info = []
        processing_info.append(f"- Total call records: {total_calls:,}")
        
        # Show calls processing info from metadata
        if 'calls_processing' in metadata:
            calls_stats = metadata['calls_processing']
            if 'total_records' in calls_stats:
                processing_info.append(f"- Records processed: {calls_stats['total_records']:,}")
            if 'errors' in calls_stats and calls_stats['errors']:
                processing_info.append(f"- Processing warnings: {len(calls_stats['errors'])}")
        
        # Show processing date if available
        if 'processing_date' in metadata:
            processing_date = metadata['processing_date'][:19].replace('T', ' ')  # Format datetime
            processing_info.append(f"- Processed on: {processing_date}")
        
        st.info("📞 **Processing Summary:**\n" + "\n".join(processing_info))
        
        st.rerun()
                        
    except Exception as e:
        st.error(f"Error loading pre-processed calls data: {str(e)}")
        st.info("💡 Make sure to run: `python preprocess_data.py` first")

def load_demo_data_combined():
    """Load pre-processed combined data from processed_files folder"""
    import os
    import json
    
    try:
        # Define pre-processed file paths
        processed_combined_file = 'data/processed_files/processed_combined_data.csv'
        processed_email_file = 'data/processed_files/processed_email_data.csv'
        processed_calls_file = 'data/processed_files/processed_calls_data.csv'
        contacts_failed_file = 'data/processed_files/contacts_failed_records.csv'
        metadata_file = 'data/processed_files/preprocessing_metadata.json'
        
        # Check if pre-processed files exist
        required_files = [processed_combined_file, processed_email_file, processed_calls_file, metadata_file]
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            st.error(f"❌ Pre-processed files not found: {', '.join(missing_files)}")
            st.info("💡 Please run the preprocessing script: `python preprocess_data.py`")
            return
            
        with st.spinner("Loading pre-processed combined data..."):
            # Load metadata
            with open(metadata_file, 'r') as f:
                preprocessing_metadata = json.load(f)
            
            # Load pre-processed combined data
            combined_data = pd.read_csv(processed_combined_file)
            
            # Load individual email and calls data for context
            email_data = pd.read_csv(processed_email_file)
            calls_data = pd.read_csv(processed_calls_file)
            
            # Convert date columns to datetime for all datasets
            for df in [combined_data, email_data]:
                if 'sent_date' in df.columns:
                    df['sent_date'] = pd.to_datetime(df['sent_date'], errors='coerce')
                if 'last_opened' in df.columns:
                    df['last_opened'] = pd.to_datetime(df['last_opened'], errors='coerce')
            
            # Convert date columns for calls data
            date_columns = ['Date', 'date', 'call_date']
            for col in date_columns:
                if col in calls_data.columns:
                    calls_data[col] = pd.to_datetime(calls_data[col], errors='coerce')
                    break
            
            # Load failed contacts records if exists
            failed_data = None
            if os.path.exists(contacts_failed_file):
                failed_data = pd.read_csv(contacts_failed_file)
                # Convert date columns for failed data too
                if 'sent_date' in failed_data.columns:
                    failed_data['sent_date'] = pd.to_datetime(failed_data['sent_date'], errors='coerce')
                if 'last_opened' in failed_data.columns:
                    failed_data['last_opened'] = pd.to_datetime(failed_data['last_opened'], errors='coerce')
            else:
                failed_data = pd.DataFrame()
                
            # Store in session state
            st.session_state.successful_data = email_data
            st.session_state.failed_data = failed_data
            st.session_state.calls_data = calls_data
            
            # Store combined data
            st.session_state.combined_joined_data = combined_data
            
            # Calculate join stats from metadata
            combined_stats = preprocessing_metadata.get('combined_processing', {})
            join_stats = {
                'joined_records': combined_stats.get('records_with_calls', 0),
                'email_only_records': combined_stats.get('records_without_calls', 0),
                'calls_only_records': 0,  # Not tracked in preprocessing
                'join_success_rate': combined_stats.get('success_rate', 0.0),
                'total_email_records': combined_stats.get('total_combined_records', 0),
                'total_calls_records': preprocessing_metadata.get('calls_processing', {}).get('total_records', 0)
            }
            st.session_state.combined_join_stats = join_stats
            
            # Separate data for UI consistency
            has_calls = combined_data['Total_Calls'] > 0
            st.session_state.combined_email_only_data = combined_data[~has_calls].copy()
            st.session_state.combined_calls_only_data = pd.DataFrame()  # Not applicable for LEFT join
            st.session_state.combined_email_failed = failed_data
            
            # Create metadata
            metadata = {
                'email_total': preprocessing_metadata.get('email_processing', {}).get('contacts_join_stats', {}).get('total_send_open_records', 0),
                'email_successful': preprocessing_metadata.get('email_processing', {}).get('contacts_join_stats', {}).get('successful_contacts_join', 0),
                'email_failed': preprocessing_metadata.get('email_processing', {}).get('contacts_join_stats', {}).get('failed_contacts_join', 0),
                'calls_total': preprocessing_metadata.get('calls_processing', {}).get('total_records', 0),
                'joined_records': join_stats['joined_records'],
                'email_only_records': join_stats['email_only_records'],
                'calls_only_records': join_stats['calls_only_records'],
                'join_success_rate': join_stats['join_success_rate'],
                'processing_timestamp': preprocessing_metadata.get('processing_date', ''),
                'data_source': 'pre_processed_files'
            }
            st.session_state.combined_metadata = metadata
            
            # Reconstruct send_df and send_open_df for KPI calculations (combining successful + failed)
            # This ensures KPI calculations work properly
            total_processed = len(email_data) + len(failed_data) if failed_data is not None else len(email_data)
            st.session_state.original_send_count = total_processed
            st.session_state.send_df = None  # Not needed for pre-processed data
            st.session_state.send_open_df = None  # Not needed for pre-processed data
                
            # Show success message
            processing_date = preprocessing_metadata.get('processing_date', 'Unknown')
            st.success(f"✅ Pre-processed combined data loaded successfully!")
            st.info(f"📧 **Email**: {len(email_data):,} records | 📞 **Calls**: {len(calls_data):,} records")
            st.info(f"🔗 **Combined**: {len(combined_data):,} records ({join_stats['joined_records']} with calls, {join_stats['email_only_records']} email-only)")
            st.caption(f"🕒 Processed on: {processing_date}")
                
            st.rerun()
                        
    except Exception as e:
        st.error(f"❌ Error loading pre-processed combined data: {str(e)}")
        st.info("💡 Make sure to run: `python preprocess_data.py` first")

def load_demo_data_multi_sdr():
    """Load pre-processed demo data from processed_files folder"""
    try:
        st.info("🔄 Loading pre-processed demo data...")
        
        # Check if processed files exist
        processed_email_file = 'data/processed_files/processed_email_data.csv'
        contacts_failed_file = 'data/processed_files/contacts_failed_records.csv'
        metadata_file = 'data/processed_files/preprocessing_metadata.json'
        
        if not os.path.exists(processed_email_file):
            st.error("❌ Pre-processed email data not found!")
            st.info("🔧 Please run the preprocessing script first: `python preprocess_data.py`")
            return
        
        # Load processed email data
        successful_data = pd.read_csv(processed_email_file)
        
        # Convert date columns to datetime for proper filtering
        if 'sent_date' in successful_data.columns:
            successful_data['sent_date'] = pd.to_datetime(successful_data['sent_date'], errors='coerce')
        if 'last_opened' in successful_data.columns:
            successful_data['last_opened'] = pd.to_datetime(successful_data['last_opened'], errors='coerce')
        
        # Load failed data if exists
        failed_data = pd.DataFrame()
        if os.path.exists(contacts_failed_file):
            failed_data = pd.read_csv(contacts_failed_file)
            # Convert date columns to datetime for failed data too
            if 'sent_date' in failed_data.columns:
                failed_data['sent_date'] = pd.to_datetime(failed_data['sent_date'], errors='coerce')
            if 'last_opened' in failed_data.columns:
                failed_data['last_opened'] = pd.to_datetime(failed_data['last_opened'], errors='coerce')
        
        # Load metadata if exists
        metadata = {}
        if os.path.exists(metadata_file):
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        # Parse datetime columns
        if 'sent_date' in successful_data.columns:
            successful_data['sent_date'] = pd.to_datetime(successful_data['sent_date'])
        if len(failed_data) > 0 and 'sent_date' in failed_data.columns:
            failed_data['sent_date'] = pd.to_datetime(failed_data['sent_date'])
        
        # Store in session state
        st.session_state.successful_data = successful_data
        st.session_state.failed_data = failed_data
        
        # Calculate metrics from metadata or data
        if 'email_processing' in metadata and 'contacts_join_stats' in metadata['email_processing']:
            contacts_stats = metadata['email_processing']['contacts_join_stats']
            original_send_count = contacts_stats.get('total_send_open_records', len(successful_data) + len(failed_data))
            successful_count = contacts_stats.get('successful_contacts_join', len(successful_data))
            failed_count = contacts_stats.get('failed_contacts_join', len(failed_data))
        else:
            # Fallback to actual data counts
            original_send_count = len(successful_data) + len(failed_data)
            successful_count = len(successful_data)
            failed_count = len(failed_data)
        
        st.session_state.original_send_count = original_send_count
        
        # For KPI calculations, we need to simulate the intermediate datasets
        # Since we don't have the actual send_df and send_open_df, we'll use the successful_data
        # The successful_data is essentially the final join result
        
        # For send_df: Use successful_data + failed_data (all records that went through send stage)
        all_records = pd.concat([successful_data, failed_data], ignore_index=True) if len(failed_data) > 0 else successful_data
        st.session_state.send_df = all_records  # This represents all send records
        
        # For send_open_df: Use successful_data + failed_data (all records that went through send-open join)
        st.session_state.send_open_df = all_records  # This represents send-open joined data
        
        # Calculate success rate
        total_processed = successful_count + failed_count
        success_rate = (successful_count / total_processed * 100) if total_processed > 0 else 0
        
        st.success(f"✅ Pre-processed demo data loaded successfully!")
        
        # Show processing summary
        processing_info = []
        processing_info.append(f"- Total records processed: {total_processed:,}")
        processing_info.append(f"- Successful matches: {successful_count:,} ({success_rate:.1f}%)")
        processing_info.append(f"- Failed matches: {failed_count:,} ({100-success_rate:.1f}%)")
        
        # Show SDR information if available
        if 'email_processing' in metadata and 'send_open_join_stats' in metadata['email_processing']:
            sdr_stats = metadata['email_processing']['send_open_join_stats']
            sdr_names = list(sdr_stats.keys())
            if sdr_names:
                processing_info.append(f"- SDRs processed: {', '.join(sdr_names)}")
        
        # Show processing date if available
        if 'processing_date' in metadata:
            processing_date = metadata['processing_date'][:19].replace('T', ' ')  # Format datetime
            processing_info.append(f"- Processed on: {processing_date}")
        
        st.info("📊 **Processing Summary:**\n" + "\n".join(processing_info))
        
        st.rerun()
            
    except Exception as e:
        st.error(f"Error loading pre-processed demo data: {str(e)}")
        st.info("💡 Make sure to run: `python preprocess_data.py` first")

def process_multi_sdr_data(ready_sdrs):
    """Process multiple SDR files individually then combine"""
    with st.spinner("🔄 Processing SDR data..."):
        try:
            all_send_open_successful = []
            all_send_open_failed = []
            processing_log = []
            
            # Step 1: Process each SDR individually (Send-Open join only)
            for idx, sdr_info in enumerate(ready_sdrs):
                sdr_name = sdr_info['name']
                processing_log.append(f"Processing SDR {idx + 1}: {sdr_name}...")
                
                # Process this SDR's Send-Open join
                send_open_successful, send_open_failed, errors = st.session_state.data_processor.process_single_sdr(
                    sdr_info['send_file'],
                    sdr_info['open_file'], 
                    sdr_name
                )
                
                if send_open_successful is not None:
                    all_send_open_successful.append(send_open_successful)
                    if send_open_failed is not None and len(send_open_failed) > 0:
                        all_send_open_failed.append(send_open_failed)
                    
                    processing_log.append(f"✅ {sdr_name}: {len(send_open_successful)} Send-Open joined, {len(send_open_failed) if send_open_failed is not None else 0} failed")
                else:
                    processing_log.append(f"❌ {sdr_name}: Failed - {', '.join(errors)}")
            
            # Step 2: Combine all SDRs' Send-Open data
            if all_send_open_successful:
                combined_send_open = pd.concat(all_send_open_successful, ignore_index=True)
                combined_send_open_failed = pd.concat(all_send_open_failed, ignore_index=True) if all_send_open_failed else pd.DataFrame()
                
                processing_log.append(f"📊 Combined {len(all_send_open_successful)} SDRs: {len(combined_send_open)} total Send-Open records")
                
                # Step 3: Join combined data with contacts
                final_successful, contacts_failed, errors = st.session_state.data_processor.process_multi_sdr_combined(
                    combined_send_open
                )
                
                if final_successful is not None:
                    # Combine all failed records
                    all_failed_list = []
                    if len(combined_send_open_failed) > 0:
                        all_failed_list.append(combined_send_open_failed)
                    if contacts_failed is not None and len(contacts_failed) > 0:
                        all_failed_list.append(contacts_failed)
                    
                    all_failed = pd.concat(all_failed_list, ignore_index=True) if all_failed_list else pd.DataFrame()
                    
                    # Store in session state
                    st.session_state.successful_data = final_successful
                    st.session_state.failed_data = all_failed
                    st.session_state.original_send_count = len(combined_send_open) + len(combined_send_open_failed)
                    st.session_state.multi_sdr_processing_log = processing_log
                    
                    processing_log.append(f"✅ Final: {len(final_successful)} records with contacts, {len(all_failed)} total failed")
                    
                    # Show summary
                    st.success(f"✅ Successfully processed {len(all_send_open_successful)} SDRs!")
                    
                    # Show detailed log
                    with st.expander("📋 Processing Details", expanded=True):
                        for log_entry in processing_log:
                            if "✅" in log_entry:
                                st.success(log_entry)
                            elif "❌" in log_entry:
                                st.error(log_entry)
                            else:
                                st.info(log_entry)
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("SDRs Processed", len(all_send_open_successful))
                    with col2:
                        st.metric("Total Records", len(final_successful) + len(all_failed))
                    with col3:
                        st.metric("Successful", len(final_successful))
                    with col4:
                        st.metric("Failed", len(all_failed))
                    
                    st.rerun()
                else:
                    st.error(f"Failed to join with contacts: {', '.join(errors)}")
            else:
                st.error("No SDR Send-Open joins were successful")
                
        except Exception as e:
            st.error(f"Error processing SDR data: {str(e)}")

def show_multi_sdr_welcome():
    """Show welcome message for multi-SDR mode"""
    st.info("👆 Add SDRs and upload their Send/Open files to get started")
    
    # Show instructions
    with st.expander("📋 How to use Multi-SDR Upload"):
        st.markdown("""
        ### Steps to process multiple SDR data:
        
        1. **Add SDRs**: Click "➕ Add SDR" to create more SDR cards (up to 10)
        2. **Enter SDR Name**: Type the SDR's name in each card
        3. **Upload Files**: Upload Send and Open CSV files for each SDR
        4. **Process**: Click "🚀 Process All SDRs" when ready
        
        ### Benefits of Multi-SDR Processing:
        - **Individual Joining**: Each SDR's Send-Open data is joined separately
        - **No Collisions**: Prevents mixing of data between SDRs
        - **SDR Attribution**: Each record is tagged with the SDR's name
        - **Combined Analytics**: View aggregated metrics across all SDRs
        
        ### File Requirements:
        - Each SDR needs both Send and Open files
        - Files should follow the standard format
        - Contacts database is shared across all SDRs
        """)

def show_welcome_message():
    st.info("👆 Upload your CSV files using the sidebar to get started")
    
    # Show expected file formats
    with st.expander("📋 Expected CSV File Formats"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Send Mails CSV")
            st.code("""
recipient_name,sent_date,Recipient Email
john@example.com,02/07/2025 19:34:57,john@example.com
jane@test.com,02/07/2025 19:35:12,jane@test.com
            """)
            
            st.subheader("Contacts CSV")
            st.info("📋 **Contacts CSV**: Auto-loaded from internal database (`data/contacts.csv`)")
            st.code("""
Email,Company URL,Name,Title
john@example.com,example.com,John Doe,Manager
jane@test.com,test.com,Jane Smith,Director
            """)
        
        with col2:
            st.subheader("Open Mails CSV")
            st.code("""
recipient_name,sent_date,Views,Clicks
john@example.com,02/07/2025 19:35:02,1,2
jane@test.com,02/07/2025 19:35:15,0,0
            """)
            
            # st.subheader("Account History CSV")
            # st.code("""
# Edit Date,Company URL,New Value,Account Owner
# 02/07/2025 10:00:00,example.com,Status Updated,John Smith
# 03/07/2025 15:30:00,test.com,Contact Added,Jane Doe
#             """)
        
        # with col3:
        #     st.subheader("Opportunity Details CSV")
        #     st.code("""
# Company URL,Amount,Created Date
# example.com,50000,02/07/2025 09:00:00
# test.com,75000,03/07/2025 14:00:00
# example.com,25000,04/07/2025 16:30:00
#             """)

def show_dashboard():
    successful_data = st.session_state.successful_data
    failed_data = st.session_state.failed_data
    original_send_count = st.session_state.get('original_send_count', len(successful_data))
    
    # Scroll to top if flag is set (after file processing)
    if st.session_state.get('should_scroll_to_top', False):
        st.components.v1.html("""
        <script>
            setTimeout(function() {
                window.scrollTo({top: 0, behavior: 'smooth'});
            }, 100);
        </script>
        """, height=0)
        st.session_state.should_scroll_to_top = False
    
    # Add tabs for successful and failed data
    tab1, tab2 = st.tabs(["✅ Successful Matches", "❌ Failed Records"])
    
    with tab1:
        show_successful_dashboard(successful_data, original_send_count)
    
    with tab2:
        show_failed_records(failed_data)

def show_successful_dashboard(data, original_send_count):
    if len(data) == 0:
        st.warning("No successful matches found.")
        return
    
    # Get intermediate datasets from session state
    send_df = st.session_state.get('send_df', None)
    send_open_df = st.session_state.get('send_open_df', None)
    
    # Dashboard filters
    st.subheader("📊 Dashboard Filters")
    
    # Check if SDR_Name column exists (multi-SDR data)
    has_sdr_data = 'SDR_Name' in data.columns
    
    if has_sdr_data:
        # 5 columns for SDR filter
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
    else:
        # 4 columns without SDR filter
        col1, col2, col3, col4 = st.columns([3, 3, 3, 3])
    
    with col1:
        # Date range selector - check if we have a clicked date range from chart
        min_date = data['sent_date'].min().date()
        max_date = data['sent_date'].max().date()
        
        # Use clicked date range if available, otherwise use full range
        if 'clicked_date_range' in st.session_state:
            default_start, default_end = st.session_state.clicked_date_range
            default_value = (default_start, default_end)
        else:
            default_value = (min_date, max_date)
        
        date_range = st.date_input(
            "📅 Date Range",
            value=default_value,
            min_value=min_date,
            max_value=max_date,
            key="date_range"
        )
    
    if has_sdr_data:
        with col2:
            # SDR filter
            sdr_names = ['All SDRs'] + sorted(data['SDR_Name'].dropna().unique().tolist())
            selected_sdr = st.selectbox(
                "👤 SDR",
                sdr_names,
                key="sdr_filter"
            )
        
        with col3:
            analysis_type = st.selectbox(
                "📈 Analysis",
                ["Week-on-Week", "Month-on-Month"],
                key="analysis_type"
            )
        
        with col4:
            # Metric selector
            metric = st.selectbox(
                "📊 Metric",
                ["Views", "Clicks", "total_sends"],
                key="metric"
            )
        
        with col5:
            # Reset filters button
            if st.button("🔄 Reset", type="secondary"):
                # Clear clicked date range from session state safely
                st.session_state.pop('clicked_date_range', None)
                st.rerun()
    else:
        with col2:
            analysis_type = st.selectbox(
                "Analysis Type",
                ["Week-on-Week", "Month-on-Month"],
                key="analysis_type"
            )
        
        with col3:
            # Metric selector
            metric = st.selectbox(
                "Primary Metric",
                ["Views", "Clicks", "total_sends"],
                key="metric"
            )
        
        with col4:
            # Reset filters button
            if st.button("Reset Filters", type="secondary"):
                # Clear clicked date range from session state safely
                st.session_state.pop('clicked_date_range', None)
                st.rerun()
    
    # Apply filters to all datasets
    filtered_data = data.copy()
    filtered_send_df = send_df.copy() if send_df is not None else None
    filtered_send_open_df = send_open_df.copy() if send_open_df is not None else None
    
    # Filter by date range - apply to all datasets
    if len(date_range) == 2:
        # Filter final dataset (Send x Open x Contacts)
        filtered_data = filtered_data[
            (filtered_data['sent_date'].dt.date >= date_range[0]) & 
            (filtered_data['sent_date'].dt.date <= date_range[1])
        ]
        
        # Filter Send dataset
        if filtered_send_df is not None and 'sent_date' in filtered_send_df.columns:
            filtered_send_df = filtered_send_df[
                (filtered_send_df['sent_date'].dt.date >= date_range[0]) & 
                (filtered_send_df['sent_date'].dt.date <= date_range[1])
            ]
        
        # Filter Send-Open dataset
        if filtered_send_open_df is not None and 'sent_date' in filtered_send_open_df.columns:
            filtered_send_open_df = filtered_send_open_df[
                (filtered_send_open_df['sent_date'].dt.date >= date_range[0]) & 
                (filtered_send_open_df['sent_date'].dt.date <= date_range[1])
            ]
    
    # Filter by SDR if applicable  
    if has_sdr_data and 'sdr_filter' in st.session_state:
        selected_sdr = st.session_state.sdr_filter
        if selected_sdr != 'All SDRs':
            # Filter final dataset
            filtered_data = filtered_data[filtered_data['SDR_Name'] == selected_sdr]
            
            # Filter Send dataset
            if filtered_send_df is not None and 'SDR_Name' in filtered_send_df.columns:
                filtered_send_df = filtered_send_df[filtered_send_df['SDR_Name'] == selected_sdr]
            
            # Filter Send-Open dataset
            if filtered_send_open_df is not None and 'SDR_Name' in filtered_send_open_df.columns:
                filtered_send_open_df = filtered_send_open_df[filtered_send_open_df['SDR_Name'] == selected_sdr]
    
    # Show filter summary with chart interaction info
    filter_info = f"📈 Showing {len(filtered_data):,} records (filtered from {len(data):,} total)"
    
    # Add SDR filter info if applicable
    if has_sdr_data and 'sdr_filter' in st.session_state:
        selected_sdr = st.session_state.sdr_filter
        if selected_sdr != 'All SDRs':
            filter_info += f" | 👤 SDR: {selected_sdr}"
    
    if 'clicked_date_range' in st.session_state:
        clicked_start, clicked_end = st.session_state.clicked_date_range
        filter_info += f" | 📊 Chart filter: {clicked_start} to {clicked_end}"
    
    st.info(filter_info)
    
    # Create dashboard sections with stage-specific datasets
    show_kpi_cards(filtered_data, filtered_send_df, filtered_send_open_df)
    show_trend_charts(filtered_data, analysis_type, metric)
    show_engagement_table(filtered_data)
    show_send_open_join_data(data)  # Show Send-Open join successful records
    show_data_table(filtered_data)

def show_kpi_cards(final_data, send_df, send_open_df):
    st.subheader("📈 Key Performance Indicators")
    
    # Create expandable section to show KPI data sources
    with st.expander("ℹ️ KPI Data Sources", expanded=False):
        st.write("**KPI calculations are based on different pipeline stages:**")
        st.write("- **Stage 1 (Send Data)**: Total Sends, Total Prospect Count, Open Rate")  
        st.write("- **Stage 2 (Send-Open Data)**: Opened Prospect Count, Prospect Opened")
        st.write("- **Stage 3 (Final Data)**: Accounts Owned, Contact Match Rate, High Engagement")
        st.write("- All KPIs are filtered by the selected date range")
    
    # First Row: Stage 1 (Send Data) KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_sends = len(send_df) if send_df is not None else 0
        st.metric("Total Sends", f"{total_sends:,}", help="From filtered Send Mails data")
    
    with col2:
        # Total Prospect Count: Unique emails in Send data
        if send_df is not None and 'Recipient Email' in send_df.columns:
            total_prospect_count = send_df['Recipient Email'].nunique()
            st.metric("Total Prospect Count", f"{total_prospect_count:,}", help="Unique prospects in Send Mails data")
        else:
            st.metric("Total Prospect Count", "N/A", help="Send data not available")
    
    with col3:
        # Open Rate: % of sends that have actual open data (non-NULL Views)
        if send_df is not None and send_open_df is not None:
            # Count records with non-NULL Views (actual opens)
            actual_opens_count = send_open_df['Views'].notna().sum() if 'Views' in send_open_df.columns else 0
            open_rate = (actual_opens_count / len(send_df) * 100) if len(send_df) > 0 else 0
            st.metric("Open Rate", f"{open_rate:.1f}%", help="% of sends that were actually opened (have non-NULL Views)")
        else:
            st.metric("Open Rate", "N/A", help="Send-Open data not available")
    
    # Second Row: Stage 2 (Send-Open Data) KPIs
    col4, col5 = st.columns(2)
    
    # Commented out KPIs as requested
    # with col4:
    #     total_views = send_open_df['Views'].sum() if send_open_df is not None and 'Views' in send_open_df.columns else 0
    #     st.metric("Total Views", f"{total_views:,}", help="From filtered Send-Open data")
    # 
    # with col5:
    #     total_clicks = send_open_df['Clicks'].sum() if send_open_df is not None and 'Clicks' in send_open_df.columns else 0
    #     st.metric("Total Clicks", f"{total_clicks:,}", help="From filtered Send-Open data")
    # 
    # with col6:
    #     view_rate = (total_views / total_sends * 100) if total_sends > 0 else 0
    #     st.metric("View Rate", f"{view_rate:.1f}%", help="Total Views / Total Sends")
    # 
    # with col7:
    #     click_rate = (total_clicks / total_sends * 100) if total_sends > 0 else 0
    #     st.metric("Click Rate", f"{click_rate:.1f}%", help="Total Clicks / Total Sends")
    
    with col4:
        # Opened Prospect Count: Unique emails with actual opens (non-NULL Views)
        if send_open_df is not None and 'Recipient Email' in send_open_df.columns and 'Views' in send_open_df.columns:
            # Only count unique emails that have non-NULL Views
            opened_prospects = send_open_df[send_open_df['Views'].notna()]['Recipient Email'].nunique()
            st.metric("Opened Prospect Count", f"{opened_prospects:,}", help="Unique prospects with actual opens (non-NULL Views)")
        else:
            st.metric("Opened Prospect Count", "N/A", help="Send-Open data not available")
    
    with col5:
        # Prospect Opened: Opened Prospect Count / Total Prospect Count * 100
        if send_open_df is not None and send_df is not None and 'Recipient Email' in send_open_df.columns and 'Recipient Email' in send_df.columns and 'Views' in send_open_df.columns:
            # Count unique prospects with actual opens (non-NULL Views)
            opened_prospect_count = send_open_df[send_open_df['Views'].notna()]['Recipient Email'].nunique()
            total_prospect_count = send_df['Recipient Email'].nunique()
            prospect_opened_rate = (opened_prospect_count / total_prospect_count * 100) if total_prospect_count > 0 else 0
            st.metric("Prospect Opened", f"{prospect_opened_rate:.1f}%", help="% of unique prospects with actual opens (non-NULL Views)")
        else:
            st.metric("Prospect Opened", "N/A", help="Send or Send-Open data not available")
    
    # Third Row: Stage 3 (Final Data) KPIs
    col10, col11, col12 = st.columns(3)
    
    with col10:
        # Accounts Owned - unique Company URL ID count
        if 'Company URL ID' in final_data.columns:
            accounts_owned = final_data['Company URL ID'].nunique()
            st.metric("Accounts Owned", f"{accounts_owned:,}", help="From final filtered data (with contacts)")
        else:
            st.metric("Accounts Owned", "N/A", help="Company URL data not available")
    
    with col11:
        # Contact Match Rate: % of send-open records that matched with contacts
        if send_open_df is not None:
            contact_match_rate = (len(final_data) / len(send_open_df) * 100) if len(send_open_df) > 0 else 0
            st.metric("Contact Match", f"{contact_match_rate:.1f}%", help="% of Send-Open records matched with contacts")
        else:
            st.metric("Contact Match", "N/A", help="Send-Open data not available")
    
    with col12:
        # High Engagement Accounts Count - companies with views > 2x emails sent (from Stage 3: Final Data)
        high_engagement_count = calculate_high_engagement_accounts(final_data)
        st.metric("High Engagement", f"{high_engagement_count:,}", help="Companies with Views > 2× Emails sent (from Stage 3: Final Data)")
    
    # Commented out Pipeline Success KPI as requested
    # with col13:
    #     # Overall Pipeline Success Rate: Final records / Original sends (from Stage 3: Final Data)
    #     if send_df is not None:
    #         overall_success_rate = (len(final_data) / len(send_df) * 100) if len(send_df) > 0 else 0
    #         st.metric("Pipeline Success", f"{overall_success_rate:.1f}%", help="% of sends that completed full pipeline (from Stage 3: Final Data)")
    #     else:
    #         st.metric("Pipeline Success", "N/A", help="Send data not available")

# def calculate_filtered_opportunity_amount(data):
#     """
#     Calculate total opportunity amount based on current filters
#     - Works on unique Company URL records to avoid double counting
#     - Filters by Latest edit date within the selected date range
#     - Filters by Account Owner matching the selected account owner
#     - Each Company URL now has single opportunity amount (no pipe-separated values)
#     """
#     if 'Amount' not in data.columns or 'Latest edit date' not in data.columns or 'Company URL' not in data.columns:
#         return 0
#     
#     # Get current filter values from session state
#     date_range = st.session_state.get('date_range', None)
#     selected_account_owner = st.session_state.get('account_owner_filter', 'All')
#     
#     # Work with unique Company URL records only
#     unique_company_data = data.drop_duplicates(subset=['Company URL'], keep='first')
#     
#     total_amount = 0
#     
#     for idx, row in unique_company_data.iterrows():
#         # Skip rows without opportunity data
#         if pd.isna(row['Amount']) or row['Amount'] == '':
#             continue
#         
#         # Apply date range filter based on Latest edit date
#         date_matches = True
#         if date_range and len(date_range) == 2:
#             latest_edit_date = row.get('Latest edit date', '')
#             if latest_edit_date and latest_edit_date != '' and latest_edit_date != 'Company URL not found':
#                 try:
#                     # Handle different possible date formats from Latest edit date
#                     if isinstance(latest_edit_date, str):
#                         # Try pandas timestamp format first
#                         edit_date = pd.to_datetime(latest_edit_date, errors='coerce')
#                     else:
#                         edit_date = pd.to_datetime(latest_edit_date, errors='coerce')
#                     
#                     if pd.notna(edit_date):
#                         date_matches = (edit_date.date() >= date_range[0]) and (edit_date.date() <= date_range[1])
#                     else:
#                         date_matches = False
#                 except (ValueError, TypeError):
#                     date_matches = False
#         
#         # Apply account owner filter
#         account_owner_matches = True
#         if selected_account_owner != 'All':
#             account_owner_matches = (row.get('Account Owner', '') == selected_account_owner)
#         
#         # If both filters match, add the opportunity amount for this unique company
#         if date_matches and account_owner_matches:
#             try:
#                 amount = float(row['Amount']) if row['Amount'] and row['Amount'] != '' else 0
#                 total_amount += amount
#             except (ValueError, TypeError):
#                 # Skip invalid amounts
#                 continue
#                 
#     return total_amount

# def calculate_time_to_opportunity(data):
#     """
#     Calculate average time from Latest edit date to Created Date for records with opportunities
#     - Works on unique Company URL records to avoid double counting
#     - Filters by Latest edit date within the selected date range
#     - Filters by Account Owner matching the selected account owner
#     - Each Company URL now has single Created Date (no pipe-separated values)
#     """
#     if 'Amount' not in data.columns or 'Latest edit date' not in data.columns or 'Created Date' not in data.columns or 'Company URL' not in data.columns:
#         return 0
#     
#     # Get current filter values from session state
#     date_range = st.session_state.get('date_range', None)
#     selected_account_owner = st.session_state.get('account_owner_filter', 'All')
#     
#     # Work with unique Company URL records only
#     unique_company_data = data.drop_duplicates(subset=['Company URL'], keep='first')
#     
#     time_differences = []
#     
#     for idx, row in unique_company_data.iterrows():
#         # Skip rows without opportunity data
#         if pd.isna(row['Amount']) or row['Amount'] == '' or pd.isna(row['Created Date']) or row['Created Date'] == '':
#             continue
#         
#         # Apply date range filter based on Latest edit date
#         date_matches = True
#         if date_range and len(date_range) == 2:
#             latest_edit_date = row.get('Latest edit date', '')
#             if latest_edit_date and latest_edit_date != '' and latest_edit_date != 'Company URL not found':
#                 try:
#                     # Handle different possible date formats from Latest edit date
#                     if isinstance(latest_edit_date, str):
#                         edit_date = pd.to_datetime(latest_edit_date, errors='coerce')
#                     else:
#                         edit_date = pd.to_datetime(latest_edit_date, errors='coerce')
#                     
#                     if pd.notna(edit_date):
#                         date_matches = (edit_date.date() >= date_range[0]) and (edit_date.date() <= date_range[1])
#                     else:
#                         date_matches = False
#                 except (ValueError, TypeError):
#                     date_matches = False
#         
#         # Apply account owner filter
#         account_owner_matches = True
#         if selected_account_owner != 'All':
#             account_owner_matches = (row.get('Account Owner', '') == selected_account_owner)
#         
#         # If both filters match, calculate time difference for this unique company
#         if date_matches and account_owner_matches:
#             latest_edit_date = row.get('Latest edit date', '')
#             created_date = row.get('Created Date', '')
#             
#             # Parse Latest edit date and Created Date
#             try:
#                 if isinstance(latest_edit_date, str):
#                     edit_date = pd.to_datetime(latest_edit_date, errors='coerce')
#                 else:
#                     edit_date = pd.to_datetime(latest_edit_date, errors='coerce')
#                 
#                 if isinstance(created_date, str):
#                     created_dt = pd.to_datetime(created_date, errors='coerce')
#                 else:
#                     created_dt = pd.to_datetime(created_date, errors='coerce')
#                 
#                 if pd.notna(edit_date) and pd.notna(created_dt):
#                     # Calculate difference in days (Created Date - Latest edit date)
#                     time_diff = (created_dt - edit_date).days
#                     time_differences.append(time_diff)
#             except (ValueError, TypeError):
#                 continue
#     
#     # Return average time difference
#     if time_differences:
#         return sum(time_differences) / len(time_differences)
#     else:
#         return 0

def calculate_high_engagement_accounts(data):
    """
    Calculate count of high engagement accounts
    High engagement = companies where Total Views > 2 × Total Emails Sent
    - Respects current date range and account owner filters
    - Groups by Company URL to get company-level metrics
    - Handles NULL Views by treating them as 0
    """
    if 'Company URL' not in data.columns or 'Views' not in data.columns:
        return 0
    
    # Group by Company URL to get company-level aggregation
    company_engagement = data.groupby('Company URL').agg({
        'recipient_name': 'count',  # Total emails sent to this company
        'Views': lambda x: x.fillna(0).sum(),  # Total views (NULL treated as 0)
        'Clicks': lambda x: x.fillna(0).sum()  # Total clicks (NULL treated as 0)
    }).reset_index()
    
    company_engagement.columns = ['Company URL', 'Total_Emails', 'Total_Views', 'Total_Clicks']
    
    # Apply high engagement logic: Views > 2 × Emails
    high_engagement_companies = company_engagement[
        company_engagement['Total_Views'] > (2 * company_engagement['Total_Emails'])
    ]
    
    return len(high_engagement_companies)

def show_trend_charts(data, analysis_type, metric):
    st.markdown(f"<h3 id='csv-analytics-dashboard'>📊 {analysis_type} Analysis</h3>", unsafe_allow_html=True)
    
    # Group data by time period
    if analysis_type == "Week-on-Week":
        data['period'] = data['sent_date'].dt.to_period('W')
        period_format = 'W'
    else:
        data['period'] = data['sent_date'].dt.to_period('M')
        period_format = 'M'
    
    # Aggregate data
    trend_data = data.groupby('period').agg({
        'Views': 'sum',
        'Clicks': 'sum',
        'recipient_name': 'count'
    }).reset_index()
    
    trend_data.columns = ['period', 'Views', 'Clicks', 'total_sends']
    
    # Convert period to string for display, but keep original for date calculations
    trend_data['period_str'] = trend_data['period'].astype(str)
    trend_data['period_start'] = trend_data['period'].dt.start_time.dt.date
    trend_data['period_end'] = trend_data['period'].dt.end_time.dt.date
    
    # Create interactive bar chart
    fig = px.bar(
        trend_data,
        x='period_str',
        y=metric,
        title=f"{metric.replace('_', ' ').title()} Over Time (Click bars to filter)",
        hover_data={'period_start': True, 'period_end': True},
        color=metric,
        color_continuous_scale="Blues"
    )
    
    fig.update_layout(
        xaxis_title="Time Period",
        yaxis_title=metric.replace('_', ' ').title(),
        height=400,
        showlegend=False
    )
    
    # Display the chart and capture click events
    try:
        selected_data = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
    except TypeError:
        # Fallback for older Streamlit versions that don't support on_select
        selected_data = st.plotly_chart(fig, use_container_width=True)
    
    # Handle bar click events to update date range filter
    try:
        if selected_data and hasattr(selected_data, 'selection'):
            selection = selected_data.selection
            # Use selection directly without calling it as a function
            # This fixes the StreamlitAPIException in production
            
            # Check if selection exists and has the expected structure
            if selection and isinstance(selection, dict) and 'points' in selection:
                if len(selection['points']) > 0:
                    # Get the clicked bar index
                    clicked_point = selection['points'][0]
                    if isinstance(clicked_point, dict) and 'point_index' in clicked_point:
                        point_index = clicked_point['point_index']
                        
                        # Get the date range for the clicked period
                        clicked_period_start = trend_data.iloc[point_index]['period_start']
                        clicked_period_end = trend_data.iloc[point_index]['period_end']
                        
                        # Update session state with the new date range
                        st.session_state.clicked_date_range = (clicked_period_start, clicked_period_end)
                        
                        # Show selected period info
                        st.info(f"📅 Selected Period: {clicked_period_start} to {clicked_period_end}")
                        st.info("💡 The date range filter above has been updated! The page will refresh automatically to show filtered data.")
                        
                        # Trigger a rerun to apply the new filter
                        st.rerun()
    except (TypeError, AttributeError, KeyError, IndexError) as e:
        # Silently handle any issues with chart interaction - chart will still display normally
        pass
    
    # Check if we need to apply a clicked date range
    if 'clicked_date_range' in st.session_state:
        clicked_start, clicked_end = st.session_state.clicked_date_range
        st.warning(f"🎯 Currently showing data for period: {clicked_start} to {clicked_end}")
        st.write("To clear this filter, use the Reset Filters button above.")

def show_engagement_table(data):
    st.subheader("🔥 Company Engagement Analysis")
    
    if 'Company URL' not in data.columns or len(data) == 0:
        st.warning("No company data available for engagement analysis.")
        return
    
    # Group by Company URL to get company-level engagement metrics
    company_engagement = data.groupby('Company URL').agg({
        'recipient_name': 'count',  # Total emails sent
        'Views': 'sum',             # Total views
        'Clicks': 'sum'             # Total clicks
    }).reset_index()
    
    company_engagement.columns = ['Company URL', 'Total Emails', 'Total Views', 'Total Clicks']
    
    # Calculate engagement rate and high engagement flag
    company_engagement['Engagement Rate'] = (company_engagement['Total Views'] / company_engagement['Total Emails'] * 100).round(1)
    company_engagement['High Engagement'] = company_engagement['Total Views'] > (2 * company_engagement['Total Emails'])
    
    # Sort by engagement rate descending
    company_engagement = company_engagement.sort_values('Engagement Rate', ascending=False)
    
    # Display summary
    total_companies = len(company_engagement)
    high_engagement_count = company_engagement['High Engagement'].sum()
    st.info(f"📊 **{total_companies}** companies analyzed • **{high_engagement_count}** high engagement accounts (Views > 2× Emails)")
    
    # Display engagement table with expandable rows
    for idx, company_row in company_engagement.iterrows():
        company_url = company_row['Company URL']
        total_emails = company_row['Total Emails']
        total_views = company_row['Total Views']
        total_clicks = company_row['Total Clicks']
        engagement_rate = company_row['Engagement Rate']
        is_high_engagement = company_row['High Engagement']
        
        # Create expandable section for each company
        engagement_indicator = "🔥 HIGH" if is_high_engagement else "📊 Normal"
        
        # Create a well-formatted header with proper spacing and alignment
        header = f"""
        {engagement_indicator} | **{company_url}**  
        📧 {total_emails:>3} emails  │  👁️ {total_views:>4} views  │  🖱️ {total_clicks:>3} clicks  │  📊 {engagement_rate:>5.1f}% rate
        """
        
        with st.expander(header.strip()):
            # Get recipient-level data for this company
            company_data = data[data['Company URL'] == company_url].copy()
            
            if len(company_data) > 0:
                # Show individual emails (records) for this company
                # Each record represents one email sent
                individual_emails = company_data[['sent_date', 'Recipient Email', 'Views', 'Clicks']].copy()
                
                # Sort options
                col1, col2 = st.columns([1, 3])
                with col1:
                    sort_option = st.selectbox(
                        "Sort by:",
                        ['Views', 'Clicks', 'sent_date'],
                        key=f"sort_{company_url}"
                    )
                
                # Sort the data
                ascending = sort_option == 'sent_date'  # Only sent_date in ascending, others descending
                individual_emails = individual_emails.sort_values(sort_option, ascending=ascending)
                
                # Display individual emails table
                st.dataframe(
                    individual_emails[['sent_date', 'Recipient Email', 'Views', 'Clicks']],
                    use_container_width=True,
                    height=min(300, len(individual_emails) * 35 + 50)  # Dynamic height
                )
                
                # Show email summary for verification
                total_individual_emails = len(individual_emails)
                total_individual_views = individual_emails['Views'].sum()
                total_individual_clicks = individual_emails['Clicks'].sum()
                st.info(f"📧 **{total_individual_emails}** emails sent • **{total_individual_views}** total views • **{total_individual_clicks}** total clicks")
            else:
                st.warning("No recipient data available for this company.")

def show_send_open_join_data(data):
    st.subheader("📊 Send-Open Join Successful Records")
    
    # Calculate Send-Open join stats
    send_open_count = len(data)  # This represents all successful Send-Open joins (both successful and failed contacts)
    
    # Get failed contact records to calculate total Send-Open successful
    failed_data = st.session_state.get('failed_data', pd.DataFrame())
    contact_failures = failed_data[failed_data['failure_reason'] == 'Send email not found in contacts'] if 'failure_reason' in failed_data.columns else pd.DataFrame()
    
    total_send_open_successful = send_open_count + len(contact_failures)
    
    st.info(f"📈 **{total_send_open_successful:,}** records successfully joined Send Mails ↔ Open Mails data")
    st.write("This shows the intermediate table created after Send-Open join, before Contacts join:")
    
    # Combine successful final data + contact failures to show complete Send-Open successful data
    if len(contact_failures) > 0:
        # Combine final successful data with contact failures to show complete Send-Open join results
        all_send_open_data = pd.concat([data, contact_failures], ignore_index=True)
    else:
        all_send_open_data = data
    
    with st.expander("📋 View Send-Open Joined Data", expanded=False):
        # Show the complete Send-Open joined data
        st.dataframe(
            all_send_open_data.head(100),
            use_container_width=True,
            height=400
        )
        
        # Show summary metrics
        if 'Views' in all_send_open_data.columns and 'Clicks' in all_send_open_data.columns:
            total_views = all_send_open_data['Views'].sum()
            total_clicks = all_send_open_data['Clicks'].sum()
            avg_views = all_send_open_data['Views'].mean()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Send-Open Records", f"{len(all_send_open_data):,}")
            with col2:
                st.metric("Total Views", f"{total_views:,}")
            with col3:
                st.metric("Total Clicks", f"{total_clicks:,}")
            with col4:
                st.metric("Avg Views/Record", f"{avg_views:.1f}")
        
        # Show column structure
        st.write("**Columns in Send-Open Joined Table:**")
        columns_display = ', '.join([f"`{col}`" for col in all_send_open_data.columns.tolist()])
        st.write(columns_display)
        
        # Download button
        send_open_csv = all_send_open_data.to_csv(index=False)
        st.download_button(
            label="📊 Download Complete Send-Open Joined Data",
            data=send_open_csv,
            file_name=f"send_open_joined_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="complete_send_open_data"
        )

def show_data_table(data):
    st.subheader("📋 Data Table")
    
    # Show sample of processed data
    st.dataframe(
        data.head(100),
        use_container_width=True,
        height=300
    )
    
    # Download button
    csv = data.to_csv(index=False)
    st.download_button(
        label="Download Successful Matches",
        data=csv,
        file_name=f"successful_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def show_failed_records(failed_data):
    if len(failed_data) == 0:
        st.info("🎉 No failed records! All send records were successfully matched.")
        return
    
    st.subheader(f"❌ Failed Records ({len(failed_data):,} records)")
    
    # Show failure reason breakdown
    if 'failure_reason' in failed_data.columns:
        reason_counts = failed_data['failure_reason'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Failure Breakdown")
            for reason, count in reason_counts.items():
                st.metric(reason.replace('_', ' ').title(), f"{count:,}")
        
        with col2:
            # Show pie chart of failure reasons
            fig = px.pie(
                values=reason_counts.values,
                names=reason_counts.index,
                title="Failure Reasons Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Separate failures into categories
        send_open_failures = failed_data[
            failed_data['failure_reason'].isin([
                'no_open_records_for_email',
                'no_match_within_11_seconds', 
                'no_match_within_60_seconds'
            ]) | 
            failed_data['failure_reason'].str.contains('multiple_matches_at_plus_', na=False)
        ]
        
        contact_failures = failed_data[failed_data['failure_reason'] == 'Send email not found in contacts']
        
        # Show Send-Open Join Failures
        if len(send_open_failures) > 0:
            st.subheader("🔗 Send-Open Join Failures")
            st.info(f"📊 **{len(send_open_failures):,}** records failed to match between Send Mails and Open Mails data")
            
            # Show breakdown by specific failure type
            send_open_breakdown = send_open_failures['failure_reason'].value_counts()
            
            with st.expander("📋 View Send-Open Failure Details", expanded=True):
                for reason, count in send_open_breakdown.items():
                    if 'no_open_records' in reason:
                        st.write(f"📭 **No Open Records for Email**: {count:,} emails had no corresponding open records")
                    elif 'no_match_within_11' in reason:
                        st.write(f"⏱️ **No Match Within 11 Seconds**: {count:,} emails had no opens within 0-11 seconds")
                    elif 'no_match_within_60' in reason:
                        st.write(f"⏰ **No Match Within 60 Seconds**: {count:,} emails had no opens within 0-60 seconds")
                    elif 'multiple_matches' in reason:
                        st.write(f"🔄 **Multiple Matches Found**: {count:,} emails had multiple open records at the same time")
                
                st.dataframe(
                    send_open_failures.head(100),
                    use_container_width=True,
                    height=250
                )
                
                # Download button for send-open failures
                send_open_csv = send_open_failures.to_csv(index=False)
                st.download_button(
                    label="Download Send-Open Join Failures",
                    data=send_open_csv,
                    file_name=f"send_open_failures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="send_open_failures"
                )
        # Show Contacts Join Failures
        if len(contact_failures) > 0:
            st.subheader("👤 Contacts Join Failures")
            st.info(f"📧 **{len(contact_failures):,}** records successfully joined Send-Open data but failed to find matching contact information")
            
            # Domain Analysis for Contact Failures
            st.subheader("🌐 Domain Analysis for Failed Contact Records")
            
            # Extract unique recipient emails from contact failures
            if 'Recipient Email' in contact_failures.columns:
                unique_failed_emails = contact_failures['Recipient Email'].dropna().unique()
                
                # Extract domains from emails
                domain_counts = {}
                for email in unique_failed_emails:
                    if '@' in str(email):
                        domain = str(email).split('@')[1].lower().strip()
                        domain_counts[domain] = domain_counts.get(domain, 0) + 1
                
                # Sort domains by count (descending)
                sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Unique Failed Emails", f"{len(unique_failed_emails):,}")
                
                with col2:
                    st.metric("Unique Domains", f"{len(domain_counts):,}")
                
                with col3:
                    if sorted_domains:
                        st.metric("Top Domain", f"{sorted_domains[0][0]} ({sorted_domains[0][1]})")
                
                # Show domain breakdown
                if sorted_domains:
                    st.subheader("📊 Domain Breakdown")
                    
                    # Create domain analysis dataframe
                    domain_df = pd.DataFrame(sorted_domains, columns=['Domain', 'Count'])
                    
                    # Show top domains
                    st.dataframe(
                        domain_df,
                        use_container_width=True,
                        height=300
                    )
                    
                    # Show domain distribution chart
                    if len(sorted_domains) > 1:
                        # Show top 10 domains in chart
                        top_domains = sorted_domains[:10]
                        
                        fig = px.bar(
                            x=[d[1] for d in top_domains],
                            y=[d[0] for d in top_domains],
                            orientation='h',
                            title=f"Top {min(10, len(sorted_domains))} Domains in Failed Contact Records",
                            labels={'x': 'Email Count', 'y': 'Domain'}
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Download buttons for analysis
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Download unique emails
                        emails_df = pd.DataFrame({'Recipient Email': unique_failed_emails})
                        emails_csv = emails_df.to_csv(index=False)
                        st.download_button(
                            label="📧 Download Unique Failed Emails",
                            data=emails_csv,
                            file_name=f"failed_contact_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="failed_emails_list"
                        )
                    
                    with col2:
                        # Download domain analysis
                        domain_csv = domain_df.to_csv(index=False)
                        st.download_button(
                            label="🌐 Download Domain Analysis",
                            data=domain_csv,
                            file_name=f"failed_contact_domains_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="failed_domains_analysis"
                        )
                else:
                    st.warning("No valid email addresses found in failed contact records")
            else:
                st.error("Recipient Email column not found in contact failures")
            
            with st.expander("📋 View Contacts Failure Details", expanded=False):
                st.write("**Why this happens:**")
                st.write("- Email addresses in Send-Open data don't exist in the Contacts CSV")
                st.write("- Email format differences (e.g., case sensitivity, extra spaces)")
                st.write("- Missing or incomplete contact records")
                
                st.dataframe(
                    contact_failures.head(100),
                    use_container_width=True,
                    height=250
                )
                
                # Download button for contact failures
                contact_csv = contact_failures.to_csv(index=False)
                st.download_button(
                    label="Download Contacts Join Failures",
                    data=contact_csv,
                    file_name=f"contact_failures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="contact_failures"
                )
        
        # Show any other failure types
        other_failures = failed_data[
            ~failed_data['failure_reason'].isin([
                'no_open_records_for_email',
                'no_match_within_11_seconds', 
                'no_match_within_60_seconds',
                'Send email not found in contacts'
            ]) &
            ~failed_data['failure_reason'].str.contains('multiple_matches_at_plus_', na=False)
        ]
        
        if len(other_failures) > 0:
            st.subheader("📋 Other Processing Failures")
            st.info(f"⚠️ **{len(other_failures):,}** records failed for other reasons")
            
            with st.expander("📋 View Other Failure Details", expanded=True):
                other_breakdown = other_failures['failure_reason'].value_counts()
                for reason, count in other_breakdown.items():
                    st.write(f"• **{reason.replace('_', ' ').title()}**: {count:,} records")
                
                st.dataframe(
                    other_failures.head(100),
                    use_container_width=True,
                    height=250
                )
                
                # Download button for other failures
                other_csv = other_failures.to_csv(index=False)
                st.download_button(
                    label="Download Other Failures",
                    data=other_csv,
                    file_name=f"other_failures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="other_failures"
                )
    else:
        # Show all failed records table if no failure_reason column
        st.subheader("📋 Failed Records Details")
        st.dataframe(
            failed_data.head(100),
            use_container_width=True,
            height=300
        )
    
    # Download button for all failed records
    failed_csv = failed_data.to_csv(index=False)
    st.download_button(
        label="Download All Failed Records",
        data=failed_csv,
        file_name=f"all_failed_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="all_failures"
    )

def show_combined_dashboard():
    """Handle the combined email and calls analytics dashboard - reuses processed data from other tabs"""
    # Check what data is already available from other tabs
    email_processed = 'successful_data' in st.session_state and st.session_state.successful_data is not None
    calls_processed = 'calls_data' in st.session_state and st.session_state.calls_data is not None
    
    # Sidebar for demo/upload choice and data status
    with st.sidebar:
        st.header("📊 Combined Data")
        
        # Pre-processed vs using data from other tabs
        data_source = st.radio(
            "Choose data source:",
            ["📂 Use Pre-processed Data", "🔄 Use Data from Other Tabs"],
            index=0,  # Default to demo files
            key="combined_data_source"
        )
        
        if data_source == "📂 Use Pre-processed Data":
            st.success("✅ Using pre-processed data files")
            st.info("Includes pre-processed Email and Calls data")
            
            # Pre-processed data loading button
            if st.button("Load Pre-processed Data", type="primary", key="load_demo_combined"):
                load_demo_data_combined()
                
        else:  # Use data from other tabs
            st.header("📊 Combined Analytics Data")
            
            # Show data availability status
            st.subheader("📋 Available Data")
            
            email_status = "✅ Available" if email_processed else "❌ Not Available"
            calls_status = "✅ Available" if calls_processed else "❌ Not Available"
            
            st.markdown(f"""
            **From Other Tabs:**
            - 📧 **Email Analytics**: {email_status}
            - 📞 **Calls Analytics**: {calls_status}
            """)
            
            if email_processed:
                email_count = len(st.session_state.successful_data)
                st.info(f"📧 Email data: {email_count:,} processed records ready to use")
            
            if calls_processed:
                calls_count = len(st.session_state.calls_data)
                st.info(f"📞 Calls data: {calls_count:,} processed records ready to use")
            
            st.markdown("---")
            
            # Action based on availability
            if email_processed and calls_processed:
                # Both available - offer to combine
                st.success("🎉 Both Email and Calls data are available!")
                st.markdown("**Ready to create combined analytics**")
                
                if st.button("🚀 Create Combined Analytics", type="primary", key="create_combined"):
                    with st.spinner("Creating combined analytics from existing data..."):
                        try:
                            # Use existing processed data instead of reprocessing files
                            email_data = st.session_state.successful_data  # Final processed email data
                            calls_data = st.session_state.calls_data       # Processed calls data
                            email_failed = st.session_state.get('failed_data', pd.DataFrame())
                            
                            # Perform the email-calls join
                            joined_data, email_only_data, calls_only_data, join_stats = st.session_state.combined_processor.join_email_calls(
                                email_data, calls_data
                            )
                            
                            if joined_data is not None:
                                # Store joined data in combined session state
                                st.session_state.combined_joined_data = joined_data  # This is the main combined data
                                st.session_state.combined_email_only_data = email_only_data
                                st.session_state.combined_calls_only_data = calls_only_data
                                st.session_state.combined_join_stats = join_stats
                                st.session_state.combined_email_failed = email_failed
                                
                                # Create metadata from joined data
                                metadata = {
                                    'email_total': len(email_data) + len(email_failed),
                                    'email_successful': len(email_data),
                                    'email_failed': len(email_failed),
                                    'calls_total': len(calls_data),
                                    'joined_records': join_stats['joined_records'],
                                    'email_only_records': join_stats['email_only_records'],
                                    'calls_only_records': join_stats['calls_only_records'],
                                    'join_success_rate': join_stats['join_success_rate'],
                                    'processing_timestamp': datetime.now().isoformat(),
                                    'data_source': 'joined_from_other_tabs'
                                }
                                st.session_state.combined_metadata = metadata
                                
                                st.success("Combined analytics created successfully with email-calls join!")
                            
                                # Show join summary
                                st.info(f"🔗 **Email-Calls Join Results:**\n"
                                       f"- Email records with calls: {join_stats['joined_records']:,}\n"
                                       f"- Email only (no calls): {join_stats['email_only_records']:,}\n"
                                       f"- Calls only (no emails): {join_stats['calls_only_records']:,}\n"
                                       f"- Join success rate: {join_stats['join_success_rate']:.1f}%")
                                
                                st.info(f"📧 **Original Email Data:**\n"
                                       f"- Total email records: {len(email_data):,}\n"
                                       f"- Failed email records: {len(email_failed):,}")
                                
                                st.info(f"📞 **Original Calls Data:**\n"
                                       f"- Total call records: {len(calls_data):,}")
                                
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to join email and calls data: {join_stats.get('error', 'Unknown error')}")
                        
                        except Exception as e:
                            st.error(f"Error creating combined analytics: {str(e)}")
            
            elif email_processed:
                # Only email available
                st.warning("📧 Email data available, but Calls data needed")
                st.markdown("**Go to Calls Analytics tab to process calls data first**")
                
            elif calls_processed:
                # Only calls available  
                st.warning("📞 Calls data available, but Email data needed")
                st.markdown("**Go to Email Analytics tab to process email data first**")
                
            else:
                # Neither available
                st.info("ℹ️ **No data available yet**")
                st.markdown("""
                **To use Combined Analytics:**
                1. Process data in **📧 Email Analytics** tab first
                2. Process data in **📞 Calls Analytics** tab  
                3. Return here to see combined insights
                """)
    
    
    # Main combined dashboard content
    if 'combined_joined_data' in st.session_state:
        show_combined_analytics()
    else:
        show_combined_welcome()

def show_combined_analytics():
    """Display the combined email and calls analytics - same format as Email Analytics tab"""
    st.header("📊 Combined Email & Calls Analytics")
    st.markdown("---")
    
    # Get joined data from session state
    joined_data = st.session_state.combined_joined_data
    join_stats = st.session_state.combined_join_stats
    metadata = st.session_state.combined_metadata
    
    # Display join summary KPIs
    st.subheader("🔗 Join Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Email Records", f"{join_stats['total_email_records']:,}")
    
    with col2:
        st.metric("Email-Calls Matches", f"{join_stats['joined_records']:,}")
    
    with col3:
        st.metric("Join Success Rate", f"{join_stats['join_success_rate']:.1f}%")
    
    with col4:
        st.metric("Email Only", f"{join_stats['email_only_records']:,}")
    
    st.markdown("---")
    
    # Add filters for combined data
    st.subheader("🔍 Filters")
    
    # Check if SDR data is available
    has_sdr_data = 'SDR_Name' in joined_data.columns and joined_data['SDR_Name'].nunique() > 1
    
    if has_sdr_data:
        # 3 columns with SDR filter
        col1, col2, col3 = st.columns([3, 3, 4])
    else:
        # 2 columns without SDR filter
        col1, col2 = st.columns([4, 6])
    
    with col1:
        # Date range selector
        min_date = joined_data['sent_date'].min().date()
        max_date = joined_data['sent_date'].max().date()
        
        date_range = st.date_input(
            "📅 Sent Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="combined_date_range"
        )
    
    with col2:
        if has_sdr_data:
            # SDR filter
            sdr_names = ['All'] + sorted(joined_data['SDR_Name'].unique().tolist())
            selected_sdr = st.selectbox(
                "👤 SDR Name",
                sdr_names,
                index=0,
                key="combined_sdr_filter"
            )
        else:
            selected_sdr = 'All'
    
    if has_sdr_data:
        with col3:
            # Reset filters button
            if st.button("🔄 Reset Filters", key="combined_reset_filters"):
                st.session_state.combined_date_range = (min_date, max_date)
                st.session_state.combined_sdr_filter = 'All'
                st.rerun()
    else:
        # Reset filters button (2 column layout)
        if st.button("🔄 Reset Filters", key="combined_reset_filters"):
            st.session_state.combined_date_range = (min_date, max_date)
            st.rerun()
    
    # Apply filters
    filtered_data = joined_data.copy()
    
    # Apply date range filter
    if len(date_range) == 2:
        start_date = pd.Timestamp(date_range[0])
        end_date = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        filtered_data = filtered_data[
            (filtered_data['sent_date'] >= start_date) & 
            (filtered_data['sent_date'] <= end_date)
        ]
    
    # Apply SDR filter
    if has_sdr_data and selected_sdr != 'All':
        filtered_data = filtered_data[filtered_data['SDR_Name'] == selected_sdr]
    
    # Show filter summary and KPIs for filtered data
    if len(filtered_data) != len(joined_data):
        st.info(f"📊 Showing **{len(filtered_data):,} records** (filtered from {len(joined_data):,} total)")
    
    # Display KPIs for filtered data
    if len(filtered_data) > 0:
        st.subheader("📊 Filtered Data KPIs")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_emails = len(filtered_data)
            st.metric("Total Emails", f"{total_emails:,}")
        
        with col2:
            total_views = filtered_data['Views'].sum() if 'Views' in filtered_data.columns else 0
            st.metric("Total Views", f"{total_views:,}")
        
        with col3:
            total_clicks = filtered_data['Clicks'].sum() if 'Clicks' in filtered_data.columns else 0
            st.metric("Total Clicks", f"{total_clicks:,}")
        
        with col4:
            records_with_calls = len(filtered_data[filtered_data['Total_Calls'] > 0]) if 'Total_Calls' in filtered_data.columns else 0
            st.metric("Records with Calls", f"{records_with_calls:,}")
        
        with col5:
            total_calls = filtered_data['Total_Calls'].sum() if 'Total_Calls' in filtered_data.columns else 0
            st.metric("Total Calls Made", f"{total_calls:,}")
    
    st.markdown("---")
    
    # Main data display - similar to Email Analytics tab
    st.subheader("📋 Combined Email & Calls Records")
    
    if len(filtered_data) > 0:
        # Show summary of what columns were added from calls
        calls_columns_added = [col for col in ['Total_Calls', 'Connected_Calls', 'Total_Call_Duration', 'Latest_Call_Date'] if col in filtered_data.columns]
        if calls_columns_added:
            st.info(f"📞 **Calls data added**: {', '.join(calls_columns_added)}")
        
        # Display the filtered data table
        st.dataframe(filtered_data, use_container_width=True)
        st.caption(f"Showing {len(filtered_data)} combined email-calls records")
        
        # Download option for filtered data
        csv_data = filtered_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data",
            data=csv_data,
            file_name=f"combined_email_calls_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_combined"
        )
        
    else:
        st.warning("No combined data available")
    
    st.markdown("---")
    
    # High Engagement Accounts Analysis - Enhanced with Call Data (using filtered data)
    show_combined_engagement_table(filtered_data)
    
    # Show email-only and calls-only data if they exist
    if 'combined_email_only_data' in st.session_state and len(st.session_state.combined_email_only_data) > 0:
        st.markdown("---")
        st.subheader("📧 Email Only Records (No Matching Calls)")
        email_only_data = st.session_state.combined_email_only_data
        st.dataframe(email_only_data, use_container_width=True)
        st.caption(f"Showing {len(email_only_data)} email records with no matching calls")
    
    if 'combined_calls_only_data' in st.session_state and len(st.session_state.combined_calls_only_data) > 0:
        st.markdown("---")
        st.subheader("📞 Calls Only Records (No Matching Emails)")
        calls_only_data = st.session_state.combined_calls_only_data
        st.dataframe(calls_only_data, use_container_width=True)
        st.caption(f"Showing {len(calls_only_data)} call records with no matching emails")

def show_combined_engagement_table(data):
    """Display high engagement accounts with enhanced call data display"""
    st.subheader("🔥 Company Engagement Analysis (with Call Data)")
    
    if 'Company URL' not in data.columns or len(data) == 0:
        st.warning("No company data available for engagement analysis.")
        return
    
    # Group by Company URL to get company-level engagement metrics (same logic as Email Analytics)
    company_engagement = data.groupby('Company URL').agg({
        'recipient_name': 'count',  # Total emails sent
        'Views': 'sum',             # Total views
        'Clicks': 'sum'             # Total clicks
    }).reset_index()
    
    company_engagement.columns = ['Company URL', 'Total Emails', 'Total Views', 'Total Clicks']
    
    # Calculate engagement rate and high engagement flag (same logic)
    company_engagement['Engagement Rate'] = (company_engagement['Total Views'] / company_engagement['Total Emails'] * 100).round(1)
    company_engagement['High Engagement'] = company_engagement['Total Views'] > (2 * company_engagement['Total Emails'])
    
    # Sort by engagement rate descending
    company_engagement = company_engagement.sort_values('Engagement Rate', ascending=False)
    
    # Display summary
    total_companies = len(company_engagement)
    high_engagement_count = company_engagement['High Engagement'].sum()
    st.info(f"📊 **{total_companies}** companies analyzed • **{high_engagement_count}** high engagement accounts (Views > 2× Emails)")
    
    # Display engagement table with expandable rows - ENHANCED with call data
    for idx, company_row in company_engagement.iterrows():
        company_url = company_row['Company URL']
        total_emails = company_row['Total Emails']
        total_views = company_row['Total Views']
        total_clicks = company_row['Total Clicks']
        engagement_rate = company_row['Engagement Rate']
        is_high_engagement = company_row['High Engagement']
        
        # Get company data to calculate call metrics
        company_data = data[data['Company URL'] == company_url].copy()
        
        # Calculate call metrics for this company - COUNT UNIQUE CALLS, NOT SUM AGGREGATED COLUMNS
        if 'Total_Calls' in company_data.columns:
            # Get unique email addresses in this company and sum their call counts (avoid double counting)
            unique_email_calls = company_data.groupby('Recipient Email').agg({
                'Total_Calls': 'first',        # Take first value (all rows for same email have same Total_Calls)
                'Connected_Calls': 'first'     # Take first value (all rows for same email have same Connected_Calls)  
            })
            total_calls = unique_email_calls['Total_Calls'].sum()
            connected_calls = unique_email_calls['Connected_Calls'].sum()
        else:
            total_calls = 0
            connected_calls = 0
        
        # Create expandable section for each company - ENHANCED header
        engagement_indicator = "🔥 HIGH" if is_high_engagement else "📊 Normal"
        
        # Enhanced header with call data
        header = f"""
        {engagement_indicator} | **{company_url}**  
        📧 {total_emails:>3} emails  │  👁️ {total_views:>4} views  │  🖱️ {total_clicks:>3} clicks  │  📊 {engagement_rate:>5.1f}% rate  │  📞 {total_calls:>3} calls  │  ✅ {connected_calls:>3} connected
        """
        
        with st.expander(header.strip()):
            if len(company_data) > 0:
                # Show individual emails with COMPLETE RECORDS (email + call data)
                # Select all relevant columns for display including new aggregated call metrics
                display_columns = ['sent_date', 'Recipient Email', 'Views', 'Clicks']
                
                # Add new aggregated call columns if they exist
                call_columns = ['Total_Calls', 'Connected_Calls', 'Total_Call_Duration', 'Latest_Call_Date']
                available_call_columns = [col for col in call_columns if col in company_data.columns]
                display_columns.extend(available_call_columns)
                
                # Create enhanced display data
                individual_emails = company_data[display_columns].copy()
                
                # Sort options
                col1, col2 = st.columns([1, 3])
                with col1:
                    sort_options = ['Views', 'Clicks', 'sent_date', 'Total_Calls', 'Connected_Calls']
                    sort_option = st.selectbox(
                        "Sort by:",
                        sort_options,
                        key=f"combined_sort_{company_url}"
                    )
                
                # Sort the data
                ascending = sort_option == 'sent_date'  # Only sent_date in ascending
                individual_emails = individual_emails.sort_values(sort_option, ascending=ascending)
                
                # Display enhanced individual emails table with complete records including call metrics
                st.dataframe(
                    individual_emails,
                    use_container_width=True,
                    height=min(400, len(individual_emails) * 35 + 50)  # Increased height for more columns
                )
                
                # Enhanced summary with call data using new aggregated columns
                total_individual_emails = len(individual_emails)
                total_individual_views = individual_emails['Views'].sum()
                total_individual_clicks = individual_emails['Clicks'].sum()
                # Calculate unique call counts to avoid double counting
                if 'Total_Calls' in individual_emails.columns:
                    unique_calls_summary = individual_emails.groupby('Recipient Email').agg({
                        'Total_Calls': 'first',
                        'Connected_Calls': 'first'
                    })
                    total_individual_calls = unique_calls_summary['Total_Calls'].sum()
                    total_connected_calls = unique_calls_summary['Connected_Calls'].sum()
                else:
                    total_individual_calls = 0
                    total_connected_calls = 0
                
                st.info(f"📧 **{total_individual_emails}** emails • **{total_individual_views}** views • **{total_individual_clicks}** clicks • **{total_individual_calls}** calls • **{total_connected_calls}** connected")
            else:
                st.warning("No recipient data available for this company.")

def show_combined_welcome():
    """Show welcome message for combined dashboard"""
    st.header("📊 Combined Email & Calls Analytics")
    st.markdown("---")
    
    st.markdown("""
    Upload and process the files in **Email Analytics** and **Calls Analytics** tabs first, then click on **Create Combined Analytics** to see the joined data.
    """)

if __name__ == "__main__":
    main()