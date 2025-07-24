import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from src.data_processor import DataProcessor
from src.database import DatabaseManager

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

def main():
    st.title("📊 CSV Analytics Dashboard")
    st.markdown("Upload your CSV files and analyze trends across different time periods")
    
    # Sidebar for file uploads
    with st.sidebar:
        st.header("📁 File Upload")
        
        # File uploaders
        send_file = st.file_uploader("Upload Send Mails CSV", type=['csv'], key='send_mails')
        open_file = st.file_uploader("Upload Open Mails CSV", type=['csv'], key='open_mails')
        account_history_file = st.file_uploader("Upload Account History CSV", type=['csv'], key='account_history')
        contact_file = st.file_uploader("Upload Contact CSV (Optional)", type=['csv'], key='contact')
        account_file = st.file_uploader("Upload Account CSV (Optional)", type=['csv'], key='account')
        
        # Process files button
        if st.button("Process Files", type="primary"):
            if send_file and open_file and account_history_file:
                with st.spinner("Processing files..."):
                    try:
                        # Save uploaded files
                        files = {
                            'send_mails': send_file,
                            'open_mails': open_file,
                            'account_history': account_history_file,
                            'contact': contact_file,
                            'account': account_file
                        }
                        
                        # Process the data
                        successful_data, failed_data = st.session_state.data_processor.process_files(files)
                        
                        if successful_data is not None:
                            # Store in session state
                            st.session_state.successful_data = successful_data
                            st.session_state.failed_data = failed_data
                            
                            # Show summary
                            total_processed = len(successful_data) + len(failed_data)
                            success_rate = len(successful_data) / total_processed * 100 if total_processed > 0 else 0
                            
                            st.success(f"Files processed successfully!")
                            st.info(f"📊 **Processing Summary:**\n"
                                   f"- Total records: {total_processed:,}\n"
                                   f"- Successful matches: {len(successful_data):,} ({success_rate:.1f}%)\n"
                                   f"- Failed matches: {len(failed_data):,} ({100-success_rate:.1f}%)")
                            st.rerun()
                        else:
                            st.error("Error processing files")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please upload Send Mails, Open Mails, and Account History CSV files")
    
    # Main dashboard
    if 'successful_data' in st.session_state:
        show_dashboard()
    else:
        show_welcome_message()

def show_welcome_message():
    st.info("👆 Upload your CSV files using the sidebar to get started")
    
    # Show expected file formats
    with st.expander("📋 Expected CSV File Formats"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Send Mails CSV")
            st.code("""
recipient_name,sent_date,domain,campaign_id
john@example.com,02/07/2025 19:34:57,example.com,CAMP001
jane@test.com,02/07/2025 19:35:12,test.com,CAMP002
            """)
        
        with col2:
            st.subheader("Open Mails CSV")
            st.code("""
recipient_name,sent_date,Views,Clicks
john@example.com,02/07/2025 19:35:02,1,2
jane@test.com,02/07/2025 19:35:15,0,0
            """)

def show_dashboard():
    successful_data = st.session_state.successful_data
    failed_data = st.session_state.failed_data
    
    # Add tabs for successful and failed data
    tab1, tab2 = st.tabs(["✅ Successful Matches", "❌ Failed Records"])
    
    with tab1:
        show_successful_dashboard(successful_data)
    
    with tab2:
        show_failed_records(failed_data)

def show_successful_dashboard(data):
    if len(data) == 0:
        st.warning("No successful matches found.")
        return
    
    # Dashboard controls
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Week-on-Week", "Month-on-Month"],
            key="analysis_type"
        )
    
    with col2:
        # Date range selector
        min_date = data['sent_date'].min().date()
        max_date = data['sent_date'].max().date()
        
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_range"
        )
    
    with col3:
        # Metric selector
        metric = st.selectbox(
            "Primary Metric",
            ["Views", "Clicks", "total_sends"],
            key="metric"
        )
    
    # Filter data based on date range
    if len(date_range) == 2:
        filtered_data = data[
            (data['sent_date'].dt.date >= date_range[0]) & 
            (data['sent_date'].dt.date <= date_range[1])
        ]
    else:
        filtered_data = data
    
    # Create dashboard sections
    show_kpi_cards(filtered_data)
    show_trend_charts(filtered_data, analysis_type, metric)
    show_data_table(filtered_data)

def show_kpi_cards(data):
    st.subheader("📈 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_sends = len(data)
        st.metric("Total Sends", f"{total_sends:,}")
    
    with col2:
        total_views = data['Views'].sum()
        st.metric("Total Views", f"{total_views:,}")
    
    with col3:
        total_clicks = data['Clicks'].sum()
        st.metric("Total Clicks", f"{total_clicks:,}")
    
    with col4:
        view_rate = (total_views / total_sends * 100) if total_sends > 0 else 0
        st.metric("View Rate", f"{view_rate:.1f}%")
    
    with col5:
        # Open Rate based on last_opened column
        if 'last_opened' in data.columns:
            # Count records with date/time format (not "Not read yet")
            opened_records = data[data['last_opened'] != 'Not read yet'].shape[0]
            open_rate = (opened_records / total_sends * 100) if total_sends > 0 else 0
            st.metric("Open Rate", f"{open_rate:.1f}%")
        else:
            st.metric("Open Rate", "N/A")

def show_trend_charts(data, analysis_type, metric):
    st.subheader(f"📊 {analysis_type} Analysis")
    
    # Group data by time period
    if analysis_type == "Week-on-Week":
        data['period'] = data['sent_date'].dt.to_period('W')
    else:
        data['period'] = data['sent_date'].dt.to_period('M')
    
    # Aggregate data
    trend_data = data.groupby('period').agg({
        'Views': 'sum',
        'Clicks': 'sum',
        'recipient_name': 'count'
    }).reset_index()
    
    trend_data.columns = ['period', 'Views', 'Clicks', 'total_sends']
    trend_data['period'] = trend_data['period'].astype(str)
    
    # Create trend chart
    fig = px.line(
        trend_data,
        x='period',
        y=metric,
        title=f"{metric.replace('_', ' ').title()} Over Time",
        markers=True
    )
    
    fig.update_layout(
        xaxis_title="Time Period",
        yaxis_title=metric.replace('_', ' ').title(),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

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
    
    # Show failed records table
    st.subheader("📋 Failed Records Details")
    st.dataframe(
        failed_data.head(100),
        use_container_width=True,
        height=300
    )
    
    # Download button for failed records
    failed_csv = failed_data.to_csv(index=False)
    st.download_button(
        label="Download Failed Records",
        data=failed_csv,
        file_name=f"failed_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()