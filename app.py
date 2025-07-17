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
        send_file = st.file_uploader("Upload Send CSV", type=['csv'], key='send')
        open_file = st.file_uploader("Upload Open CSV", type=['csv'], key='open')
        contact_file = st.file_uploader("Upload Contact CSV", type=['csv'], key='contact')
        account_file = st.file_uploader("Upload Account CSV", type=['csv'], key='account')
        
        # Process files button
        if st.button("Process Files", type="primary"):
            if send_file and open_file:
                with st.spinner("Processing files..."):
                    try:
                        # Save uploaded files
                        files = {
                            'send': send_file,
                            'open': open_file,
                            'contact': contact_file,
                            'account': account_file
                        }
                        
                        # Process the data
                        processed_data = st.session_state.data_processor.process_files(files)
                        
                        if processed_data is not None:
                            # Store in session state
                            st.session_state.processed_data = processed_data
                            st.success("Files processed successfully!")
                            st.rerun()
                        else:
                            st.error("Error processing files")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please upload at least Send and Open CSV files")
    
    # Main dashboard
    if 'processed_data' in st.session_state:
        show_dashboard()
    else:
        show_welcome_message()

def show_welcome_message():
    st.info("👆 Upload your CSV files using the sidebar to get started")
    
    # Show expected file formats
    with st.expander("📋 Expected CSV File Formats"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Send CSV")
            st.code("""
recipient_email,domain,date_sent
user@example.com,example.com,2024-01-01
user2@test.com,test.com,2024-01-02
            """)
        
        with col2:
            st.subheader("Open CSV")
            st.code("""
recipient_email,date_sent,open_count,clicks
user@example.com,2024-01-01,1,2
user2@test.com,2024-01-02,0,0
            """)

def show_dashboard():
    data = st.session_state.processed_data
    
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
        min_date = data['date_sent'].min()
        max_date = data['date_sent'].max()
        
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
            ["open_count", "clicks", "total_sends"],
            key="metric"
        )
    
    # Filter data based on date range
    if len(date_range) == 2:
        filtered_data = data[
            (data['date_sent'] >= pd.Timestamp(date_range[0])) & 
            (data['date_sent'] <= pd.Timestamp(date_range[1]))
        ]
    else:
        filtered_data = data
    
    # Create dashboard sections
    show_kpi_cards(filtered_data)
    show_trend_charts(filtered_data, analysis_type, metric)
    show_data_table(filtered_data)

def show_kpi_cards(data):
    st.subheader("📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sends = len(data)
        st.metric("Total Sends", f"{total_sends:,}")
    
    with col2:
        total_opens = data['open_count'].sum()
        st.metric("Total Opens", f"{total_opens:,}")
    
    with col3:
        total_clicks = data['clicks'].sum()
        st.metric("Total Clicks", f"{total_clicks:,}")
    
    with col4:
        open_rate = (total_opens / total_sends * 100) if total_sends > 0 else 0
        st.metric("Open Rate", f"{open_rate:.1f}%")

def show_trend_charts(data, analysis_type, metric):
    st.subheader(f"📊 {analysis_type} Analysis")
    
    # Group data by time period
    if analysis_type == "Week-on-Week":
        data['period'] = data['date_sent'].dt.to_period('W')
    else:
        data['period'] = data['date_sent'].dt.to_period('M')
    
    # Aggregate data
    trend_data = data.groupby('period').agg({
        'open_count': 'sum',
        'clicks': 'sum',
        'recipient_email': 'count'
    }).reset_index()
    
    trend_data.columns = ['period', 'open_count', 'clicks', 'total_sends']
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
        label="Download Processed Data",
        data=csv,
        file_name=f"processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()