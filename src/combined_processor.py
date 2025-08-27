import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging
from .data_processor import DataProcessor
from .calls_processor import CallsProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CombinedProcessor:
    """
    Combined Email and Calls Data Processor
    Handles both email analytics and calls data independently, then provides combined insights
    """
    
    def __init__(self):
        # Initialize individual processors
        self.email_processor = DataProcessor()
        self.calls_processor = CallsProcessor()
        
        logger.info("CombinedProcessor initialized with independent email and calls processors")
    
    def process_combined_files(self, files):
        """
        Process both email and calls files independently
        
        Args:
            files: Dictionary containing all uploaded files
                - send_mails: Send Mails CSV file
                - open_mails: Open Mails CSV file  
                - contacts: Contacts CSV (usually 'data/contacts.csv')
                - calls: Calls Record CSV file
                
        Returns:
            tuple: (is_valid, combined_result)
            where combined_result contains:
            - email_data: Processed email analytics data
            - calls_data: Processed calls data
            - email_failed: Failed email records
            - calls_failed: Failed calls records (empty for now)
            - validation_errors: List of all validation errors
            - metadata: Processing metadata
        """
        logger.info("Starting combined files processing...")
        
        all_validation_errors = []
        
        try:
            # Process email files first
            logger.info("Processing email files...")
            email_files = {
                'send_mails': files.get('send_mails'),
                'open_mails': files.get('open_mails'),
                'contacts': files.get('contacts', 'data/contacts.csv')
            }
            
            email_result = self.email_processor.process_files(email_files)
            
            # Handle different email result formats
            if len(email_result) == 6:
                successful_email_data, failed_email_data, email_validation_errors, original_send_count, send_df, send_open_df = email_result
            elif len(email_result) == 4:
                successful_email_data, failed_email_data, email_validation_errors, original_send_count = email_result
                send_df, send_open_df = None, None
            elif len(email_result) == 3:
                successful_email_data, failed_email_data, email_validation_errors = email_result
                original_send_count = len(successful_email_data) if successful_email_data is not None else 0
                send_df, send_open_df = None, None
            else:
                successful_email_data, failed_email_data = email_result
                email_validation_errors = []
                original_send_count = len(successful_email_data) if successful_email_data is not None else 0
                send_df, send_open_df = None, None
            
            # Add email validation errors to combined list
            if email_validation_errors:
                all_validation_errors.extend([f"📧 Email: {error}" for error in email_validation_errors])
            
            # Process calls file
            logger.info("Processing calls file...")
            calls_file = files.get('calls')
            
            if calls_file is None:
                all_validation_errors.append("📞 Calls: Missing Calls Record CSV file")
                calls_success, calls_errors, calls_data = False, ["Missing calls file"], None
            else:
                calls_success, calls_errors, calls_data = self.calls_processor.process_calls_file(calls_file)
                
                # Add calls validation errors to combined list
                if calls_errors:
                    all_validation_errors.extend([f"📞 Calls: {error}" for error in calls_errors])
            
            # Check if both processing succeeded
            email_success = successful_email_data is not None and len(all_validation_errors) == 0
            
            if email_success and calls_success:
                # Both processing succeeded
                logger.info(f"Combined processing successful: {len(successful_email_data)} email records, {len(calls_data)} call records")
                
                # Create metadata
                metadata = {
                    'email_total': len(successful_email_data) + len(failed_email_data),
                    'email_successful': len(successful_email_data),
                    'email_failed': len(failed_email_data),
                    'calls_total': len(calls_data),
                    'original_send_count': original_send_count,
                    'processing_timestamp': datetime.now().isoformat()
                }
                
                combined_result = {
                    'email_data': successful_email_data,
                    'calls_data': calls_data,
                    'email_failed': failed_email_data,
                    'calls_failed': pd.DataFrame(),  # No failed calls for now
                    'validation_errors': [],
                    'metadata': metadata,
                    'intermediate_data': {
                        'send_df': send_df,
                        'send_open_df': send_open_df
                    }
                }
                
                return True, combined_result
                
            else:
                # One or both processing failed
                logger.error(f"Combined processing failed with {len(all_validation_errors)} validation errors")
                
                combined_result = {
                    'email_data': successful_email_data if email_success else None,
                    'calls_data': calls_data if calls_success else None,
                    'email_failed': failed_email_data if email_success else None,
                    'calls_failed': pd.DataFrame(),
                    'validation_errors': all_validation_errors,
                    'metadata': {'processing_timestamp': datetime.now().isoformat()},
                    'intermediate_data': None
                }
                
                return False, combined_result
                
        except Exception as e:
            logger.error(f"Error in combined processing: {str(e)}")
            
            error_result = {
                'email_data': None,
                'calls_data': None,
                'email_failed': None,
                'calls_failed': None,
                'validation_errors': [f"❌ **Processing Error**: {str(e)}"],
                'metadata': {'processing_timestamp': datetime.now().isoformat()},
                'intermediate_data': None
            }
            
            return False, error_result
    
    def join_email_calls(self, email_data, calls_data):
        """
        Join final email output with calls data by adding aggregated call metrics as columns
        
        Args:
            email_data: Final processed email DataFrame (with Recipient Email column)
            calls_data: Processed calls DataFrame (with Email column)
            
        Returns:
            tuple: (joined_data, email_only_data, calls_only_data, join_stats)
        """
        try:
            if email_data is None or calls_data is None or len(email_data) == 0 or len(calls_data) == 0:
                return None, email_data, calls_data, {'error': 'No data available'}
            
            logger.info(f"Adding aggregated call metrics to email data")
            
            # Clean and normalize email addresses for matching
            email_data_clean = email_data.copy()
            calls_data_clean = calls_data.copy()
            
            # Normalize email addresses (lowercase, strip whitespace)
            email_data_clean['email_clean'] = email_data_clean['Recipient Email'].str.lower().str.strip()
            calls_data_clean['email_clean'] = calls_data_clean['Email'].str.lower().str.strip()
            
            # Create aggregated call metrics per email address
            logger.info(f"Aggregating call metrics for {calls_data_clean['email_clean'].nunique()} unique email addresses")
            
            call_metrics = calls_data_clean.groupby('email_clean').agg({
                'Email': 'count',  # Total calls count
                'Call Disposition': lambda x: (x.str.strip().str.lower() == 'connected').sum(),  # Connected calls count
                'Assigned': lambda x: x.notna().sum(),  # Alternative total calls count (using non-null Assigned values)
                'Call Duration (seconds)': lambda x: x.sum() if 'Call Duration (seconds)' in calls_data_clean.columns else 0,
                'Date': 'max'  # Latest call date
            }).reset_index()
            
            # Rename aggregated columns
            call_metrics.columns = ['email_clean', 'Total_Calls', 'Connected_Calls', 'Total_Calls_Alt', 'Total_Call_Duration', 'Latest_Call_Date']
            
            # Use Total_Calls_Alt if it's more reliable (based on Assigned column)
            call_metrics['Total_Calls'] = call_metrics[['Total_Calls', 'Total_Calls_Alt']].max(axis=1)
            call_metrics = call_metrics.drop('Total_Calls_Alt', axis=1)
            
            logger.info(f"Created aggregated metrics for {len(call_metrics)} unique email addresses")
            
            # Left join email data with aggregated call metrics
            joined_data = pd.merge(
                email_data_clean,
                call_metrics,
                on='email_clean',
                how='left'
            )
            
            # Fill NaN values for emails with no calls
            joined_data['Total_Calls'] = joined_data['Total_Calls'].fillna(0).astype(int)
            joined_data['Connected_Calls'] = joined_data['Connected_Calls'].fillna(0).astype(int)
            joined_data['Total_Call_Duration'] = joined_data['Total_Call_Duration'].fillna(0)
            
            # Remove the temporary clean column
            joined_data = joined_data.drop('email_clean', axis=1)
            
            # Separate records based on call data presence
            has_call_data = joined_data['Total_Calls'] > 0
            email_only_data = joined_data[~has_call_data].copy()
            joined_with_calls = joined_data[has_call_data].copy()
            
            # Find calls-only records (calls with emails not in email data)
            email_addresses_in_data = set(email_data['Recipient Email'].str.lower().str.strip())
            calls_only_data = calls_data[~calls_data['Email'].str.lower().str.strip().isin(email_addresses_in_data)]
            
            # Calculate join statistics
            unique_emails_with_calls = joined_data[joined_data['Total_Calls'] > 0]['Recipient Email'].nunique()
            
            join_stats = {
                'total_email_records': len(email_data),
                'total_calls_records': len(calls_data),
                'joined_records': len(joined_with_calls),
                'email_only_records': len(email_only_data),
                'calls_only_records': len(calls_only_data),
                'unique_emails_with_calls': unique_emails_with_calls,
                'join_success_rate': (len(joined_with_calls) / len(email_data) * 100) if len(email_data) > 0 else 0.0,
                'calls_join_rate': (unique_emails_with_calls / calls_data['Email'].nunique() * 100) if calls_data['Email'].nunique() > 0 else 0.0,
                'calls_columns_added': ['Total_Calls', 'Connected_Calls', 'Total_Call_Duration', 'Latest_Call_Date']
            }
            
            logger.info(f"Email-Calls aggregation complete: {len(joined_with_calls)} email records with call data")
            logger.info(f"Aggregation stats: {join_stats}")
            
            return joined_data, email_only_data, calls_only_data, join_stats
            
        except Exception as e:
            logger.error(f"Error joining email and calls data: {str(e)}")
            return None, email_data, calls_data, {'error': str(e)}

    def analyze_overlap(self, email_data, calls_data):
        """
        Analyze overlap between email and calls data
        
        Args:
            email_data: Processed email DataFrame
            calls_data: Processed calls DataFrame
            
        Returns:
            dict: Overlap analysis results
        """
        try:
            if email_data is None or calls_data is None or len(email_data) == 0 or len(calls_data) == 0:
                return {
                    'overlap_contacts': 0,
                    'email_only_contacts': 0,
                    'calls_only_contacts': 0,
                    'total_unique_contacts': 0,
                    'overlap_percentage': 0.0
                }
            
            # Get contact sets
            email_contacts = set()
            if 'Recipient Email' in email_data.columns:
                email_contacts = set(email_data['Recipient Email'].dropna().str.lower())
            
            call_contacts = set()
            if 'Contact' in calls_data.columns:
                # Assume Contact column contains email addresses
                call_contacts = set(calls_data['Contact'].dropna().str.lower())
            
            # Calculate overlap
            overlap_contacts = email_contacts.intersection(call_contacts)
            email_only = email_contacts - call_contacts
            calls_only = call_contacts - email_contacts
            total_unique = email_contacts.union(call_contacts)
            
            overlap_percentage = (len(overlap_contacts) / len(total_unique) * 100) if len(total_unique) > 0 else 0.0
            
            analysis = {
                'overlap_contacts': len(overlap_contacts),
                'email_only_contacts': len(email_only),
                'calls_only_contacts': len(calls_only),
                'total_unique_contacts': len(total_unique),
                'overlap_percentage': overlap_percentage,
                'overlap_contact_list': list(overlap_contacts)[:100]  # First 100 for display
            }
            
            logger.info(f"Overlap analysis: {len(overlap_contacts)} overlapping contacts ({overlap_percentage:.1f}%)")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in overlap analysis: {str(e)}")
            return {
                'overlap_contacts': 0,
                'email_only_contacts': 0,
                'calls_only_contacts': 0,
                'total_unique_contacts': 0,
                'overlap_percentage': 0.0,
                'error': str(e)
            }
    
    def get_combined_metrics(self, email_data, calls_data):
        """
        Calculate combined metrics across both channels
        
        Args:
            email_data: Processed email DataFrame
            calls_data: Processed calls DataFrame
            
        Returns:
            dict: Combined metrics
        """
        try:
            metrics = {
                'total_outreach': 0,
                'email_sends': 0,
                'total_calls': 0,
                'email_views': 0,
                'email_clicks': 0,
                'connected_calls': 0,
                'unique_contacts_reached': 0,
                'cross_channel_contacts': 0
            }
            
            # Email metrics
            if email_data is not None and len(email_data) > 0:
                metrics['email_sends'] = len(email_data)
                if 'Views' in email_data.columns:
                    metrics['email_views'] = email_data['Views'].sum()
                if 'Clicks' in email_data.columns:
                    metrics['email_clicks'] = email_data['Clicks'].sum()
            
            # Calls metrics
            if calls_data is not None and len(calls_data) > 0:
                metrics['total_calls'] = len(calls_data)
                if 'Call Disposition' in calls_data.columns:
                    connected = calls_data['Call Disposition'].str.strip().str.lower() == 'connected'
                    metrics['connected_calls'] = connected.sum()
            
            # Combined metrics
            metrics['total_outreach'] = metrics['email_sends'] + metrics['total_calls']
            
            # Analyze overlap for cross-channel metrics
            overlap_analysis = self.analyze_overlap(email_data, calls_data)
            metrics['unique_contacts_reached'] = overlap_analysis['total_unique_contacts']
            metrics['cross_channel_contacts'] = overlap_analysis['overlap_contacts']
            
            logger.info(f"Combined metrics calculated: {metrics['total_outreach']} total outreach activities")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating combined metrics: {str(e)}")
            return {
                'total_outreach': 0,
                'email_sends': 0,
                'total_calls': 0,
                'email_views': 0,
                'email_clicks': 0,
                'connected_calls': 0,
                'unique_contacts_reached': 0,
                'cross_channel_contacts': 0,
                'error': str(e)
            }