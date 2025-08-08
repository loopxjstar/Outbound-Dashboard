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
        # account_history_file = st.file_uploader("Upload Account History CSV", type=['csv'], key='account_history')
        
        # Contacts file info
        st.info("📋 **Contacts CSV**: Using internal contacts database from `data/contacts.csv`")
        # opportunity_details_file = st.file_uploader("Upload Opportunity Details CSV", type=['csv'], key='opportunity_details')
        # contact_file = st.file_uploader("Upload Contact CSV (Optional)", type=['csv'], key='contact')
        # account_file = st.file_uploader("Upload Account CSV (Optional)", type=['csv'], key='account')
        
        # Process files button
        if st.button("Process Files", type="primary"):
            if send_file and open_file:
                # Commented out: and opportunity_details_file
                with st.spinner("Processing files..."):
                    try:
                        # Save uploaded files
                        files = {
                            'send_mails': send_file,
                            'open_mails': open_file,
                            'contacts': 'data/contacts.csv'  # Internal contacts file
                            # 'account_history': account_history_file,
                            # 'opportunity_details': opportunity_details_file,
                            # 'contact': contact_file,
                            # 'account': account_file
                        }
                        
                        # Process the data
                        result = st.session_state.data_processor.process_files(files)
                        
                        if len(result) == 4:
                            # New format: successful_data, failed_data, validation_errors, original_send_count
                            successful_data, failed_data, validation_errors, original_send_count = result
                        elif len(result) == 3:
                            # Old format: successful_data, failed_data, validation_errors
                            successful_data, failed_data, validation_errors = result
                            original_send_count = len(successful_data) if successful_data is not None else 0
                        else:
                            # Backward compatibility
                            successful_data, failed_data = result
                            validation_errors = []
                            original_send_count = len(successful_data) if successful_data is not None else 0
                        
                        if successful_data is not None:
                            # Store in session state
                            st.session_state.successful_data = successful_data
                            st.session_state.failed_data = failed_data
                            st.session_state.original_send_count = original_send_count  # Store original send count
                            
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
                            # Show validation errors
                            if validation_errors:
                                st.error("**File Validation Failed**")
                                for error in validation_errors:
                                    st.error(error)
                            else:
                                st.error("Error processing files")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please upload Send Mails and Open Mails CSV files")
                # Commented out: and Account History and Opportunity Details
    
    # Main dashboard
    if 'successful_data' in st.session_state:
        show_dashboard()
    else:
        show_welcome_message()

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
    
    # Dashboard filters
    st.subheader("📊 Dashboard Filters")
    col1, col2, col3, col4 = st.columns([3, 3, 3, 3])
    
    with col1:
        # Date range selector
        min_date = data['sent_date'].min().date()
        max_date = data['sent_date'].max().date()
        
        date_range = st.date_input(
            "Sent Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_range"
        )
    
    # with col2:
    #     # Account Owner filter - REMOVED
    #     account_owners = ['All'] + sorted(data['Account Owner'].dropna().unique().tolist())
    #     selected_account_owner = st.selectbox(
    #         "Account Owner",
    #         account_owners,
    #         key="account_owner_filter"
    #     )
    
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
            st.rerun()
    
    # Apply filters
    filtered_data = data.copy()
    
    # Filter by date range
    if len(date_range) == 2:
        filtered_data = filtered_data[
            (filtered_data['sent_date'].dt.date >= date_range[0]) & 
            (filtered_data['sent_date'].dt.date <= date_range[1])
        ]
    
    # Filter by Account Owner - REMOVED
    # if selected_account_owner != 'All':
    #     filtered_data = filtered_data[filtered_data['Account Owner'] == selected_account_owner]
    
    # Show filter summary
    st.info(f"📈 Showing {len(filtered_data):,} records (filtered from {len(data):,} total records)")
    
    # Create dashboard sections
    show_kpi_cards(filtered_data, original_send_count)
    show_trend_charts(filtered_data, analysis_type, metric)
    show_engagement_table(filtered_data)
    show_data_table(filtered_data)

def show_kpi_cards(data, original_send_count):
    st.subheader("📈 Key Performance Indicators")
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1:
        total_sends = original_send_count
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
    
    with col6:
        # Accounts Owned - unique Company URL ID count
        if 'Company URL ID' in data.columns:
            accounts_owned = data['Company URL ID'].nunique()
            st.metric("Accounts Owned", f"{accounts_owned:,}")
        else:
            st.metric("Accounts Owned", "N/A")
    
    # with col7:
    #     # Total Opportunity Amount - filtered by Latest edit date and account owner
    #     total_opportunity_amount = calculate_filtered_opportunity_amount(data)
    #     st.metric("Total Opp. Amount", f"${total_opportunity_amount:,.0f}")
    # 
    # with col8:
    #     # Time to Opportunity - average days from Latest edit date to Created Date
    #     avg_time_to_opportunity = calculate_time_to_opportunity(data)
    #     st.metric("Time to Opp.", f"{avg_time_to_opportunity:.1f} days")
    
    with col7:
        # High Engagement Accounts Count - companies with views > 2x emails sent
        high_engagement_count = calculate_high_engagement_accounts(data)
        st.metric("High Engagement", f"{high_engagement_count:,}")

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
    """
    if 'Company URL' not in data.columns or 'Views' not in data.columns:
        return 0
    
    # Group by Company URL to get company-level aggregation
    company_engagement = data.groupby('Company URL').agg({
        'recipient_name': 'count',  # Total emails sent to this company
        'Views': 'sum',             # Total views from this company
        'Clicks': 'sum'             # Total clicks from this company
    }).reset_index()
    
    company_engagement.columns = ['Company URL', 'Total_Emails', 'Total_Views', 'Total_Clicks']
    
    # Apply high engagement logic: Views > 2 × Emails
    high_engagement_companies = company_engagement[
        company_engagement['Total_Views'] > (2 * company_engagement['Total_Emails'])
    ]
    
    return len(high_engagement_companies)

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

if __name__ == "__main__":
    main()