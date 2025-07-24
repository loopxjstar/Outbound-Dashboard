import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.required_send_columns = ['recipient_name', 'sent_date', 'Recipient Email']
        self.required_open_columns = ['recipient_name', 'sent_date', 'Views', 'Clicks']
        self.required_account_history_columns = ['Edit Date', 'Company URL', 'New Value', 'Account Owner']
        self.required_contacts_columns = ['Email']
    
    def process_files(self, files):
        """
        Process uploaded CSV files and return joined data with failed records
        """
        try:
            # Load CSV files
            send_df = self._load_csv(files.get('send_mails') or files.get('send'), 'send_mails')
            open_df = self._load_csv(files.get('open_mails') or files.get('open'), 'open_mails')
            contacts_df = self._load_csv(files.get('contacts'), 'contacts')
            account_history_df = self._load_csv(files.get('account_history'), 'account_history')
            
            if send_df is None or open_df is None or contacts_df is None or account_history_df is None:
                return None, None
            
            # Validate required columns
            if not self._validate_columns(send_df, self.required_send_columns, 'send_mails'):
                return None, None
            
            if not self._validate_columns(open_df, self.required_open_columns, 'open_mails'):
                return None, None
            
            if not self._validate_columns(contacts_df, self.required_contacts_columns, 'contacts'):
                return None, None
                
            if not self._validate_columns(account_history_df, self.required_account_history_columns, 'account_history'):
                return None, None
            
            # Clean and prepare data
            send_df = self._clean_data(send_df, 'send')
            open_df = self._clean_data(open_df, 'open')
            contacts_df = self._clean_data(contacts_df, 'contacts')
            account_history_df = self._clean_data(account_history_df, 'account_history')
            
            # Perform incremental datetime join (send + open)
            send_open_successful, send_open_failed = self._join_send_open(send_df, open_df)
            
            if send_open_successful is None:
                return None, None
            
            # Join send-open data with contacts
            contacts_successful, contacts_failed = self._join_with_contacts(send_open_successful, contacts_df)
            
            # Combine all failed records
            all_failed = []
            if len(send_open_failed) > 0:
                all_failed.extend(send_open_failed.to_dict('records'))
            if len(contacts_failed) > 0:
                all_failed.extend(contacts_failed.to_dict('records'))
            
            final_failed_df = pd.DataFrame(all_failed) if all_failed else pd.DataFrame()
            
            # Integrate Account History data
            if len(contacts_successful) > 0:
                contacts_successful = self._integrate_account_history(contacts_successful, account_history_df)
            
            successful_df = contacts_successful
            
            # Save output files
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            
            # Save successful matches
            if len(successful_df) > 0:
                successful_filename = f"successful_joins_{timestamp}.csv"
                successful_path = os.path.join('outputs', successful_filename)
                os.makedirs('outputs', exist_ok=True)
                successful_df.to_csv(successful_path, index=False)
                logger.info(f"Saved {len(successful_df)} successful matches to {successful_path}")
            
            # Save failed records
            if len(final_failed_df) > 0:
                failed_filename = f"failed_records_{timestamp}.csv"
                failed_path = os.path.join('outputs', failed_filename)
                os.makedirs('outputs', exist_ok=True)
                final_failed_df.to_csv(failed_path, index=False)
                logger.info(f"Saved {len(final_failed_df)} failed records to {failed_path}")
            
            logger.info(f"Successfully processed files: {len(successful_df)} successful, {len(final_failed_df)} failed")
            return successful_df, final_failed_df
            
        except Exception as e:
            logger.error(f"Error processing files: {str(e)}")
            return None, None
    
    def _load_csv(self, file, file_type):
        """Load CSV file with error handling"""
        try:
            if file is None:
                return None
            
            df = pd.read_csv(file)
            logger.info(f"Loaded {file_type} CSV: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error loading {file_type} CSV: {str(e)}")
            return None
    
    def _validate_columns(self, df, required_columns, file_type):
        """Validate that required columns exist"""
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing columns in {file_type} CSV: {missing_columns}")
            return False
        
        return True
    
    def _clean_data(self, df, file_type):
        """Clean and standardize data"""
        df = df.copy()
        
        # Convert date columns with correct format DD/MM/YYYY HH:MM:SS
        if 'sent_date' in df.columns:
            df['sent_date'] = pd.to_datetime(df['sent_date'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        
        if 'Edit Date' in df.columns:
            df['Edit Date'] = pd.to_datetime(df['Edit Date'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        
        # Clean recipient names
        if 'recipient_name' in df.columns:
            df['recipient_name'] = df['recipient_name'].str.strip()
        
        # Clean Company URLs (case insensitive matching)
        if 'Company URL' in df.columns:
            df['Company URL'] = df['Company URL'].str.lower().str.strip()
        
        # Clean Email column in contacts
        if 'Email' in df.columns:
            df['Email'] = df['Email'].str.strip()
        
        # Handle numeric columns
        if file_type == 'open':
            if 'Views' in df.columns:
                df['Views'] = pd.to_numeric(df['Views'], errors='coerce').fillna(0)
            if 'Clicks' in df.columns:
                df['Clicks'] = pd.to_numeric(df['Clicks'], errors='coerce').fillna(0)
        
        # Remove rows with null key columns
        if file_type == 'send':
            df = df.dropna(subset=['recipient_name', 'sent_date'])
        elif file_type == 'open':
            df = df.dropna(subset=['recipient_name', 'sent_date'])
        elif file_type == 'account_history':
            df = df.dropna(subset=['Edit Date', 'Company URL'])
        elif file_type == 'contacts':
            df = df.dropna(subset=['Email'])
        
        logger.info(f"Cleaned {file_type} data: {len(df)} rows remaining")
        return df
    
    def _join_send_open(self, send_df, open_df):
        """Join send and open dataframes with incremental datetime matching"""
        try:
            return self._incremental_datetime_join(send_df, open_df)
            
        except Exception as e:
            logger.error(f"Error joining send and open data: {str(e)}")
            return None
    
    def _incremental_datetime_join(self, send_df, open_df):
        """
        Two-phase incremental datetime matching:
        Phase 1: 0-11 seconds (fast & safe)
        Phase 2: 12-60 seconds (on failed records only)
        """
        logger.info("Starting two-phase incremental datetime matching")
        
        # Phase 1: 0-11 seconds matching
        logger.info("Phase 1: Attempting 0-11 second matches")
        phase1_successful, phase1_failed, used_open_indices = self._phase1_matching(send_df, open_df)
        
        phase1_success_count = len(phase1_successful)
        phase1_fail_count = len(phase1_failed)
        phase1_success_rate = (phase1_success_count / len(send_df) * 100) if len(send_df) > 0 else 0
        
        logger.info(f"Phase 1 Results: {phase1_success_count} successful ({phase1_success_rate:.1f}%), {phase1_fail_count} failed")
        
        # Phase 2: 12-60 seconds matching on failed records only
        phase2_successful = []
        final_failed = phase1_failed.copy()
        
        if phase1_fail_count > 0:
            logger.info(f"Phase 2: Attempting 12-60 second matches on {phase1_fail_count} failed records")
            phase2_successful, final_failed = self._phase2_matching(phase1_failed, open_df, used_open_indices)
            
            phase2_success_count = len(phase2_successful)
            logger.info(f"Phase 2 Results: {phase2_success_count} additional successful matches")
        
        # Combine results from both phases
        all_successful = phase1_successful + phase2_successful
        
        # Create final DataFrames
        successful_df = pd.DataFrame(all_successful) if all_successful else pd.DataFrame()
        failed_df = pd.DataFrame(final_failed) if final_failed else pd.DataFrame()
        
        # Views column is already correct, no renaming needed
        
        # Log final statistics
        total_processed = len(send_df)
        total_successful = len(successful_df)
        total_failed = len(failed_df)
        final_success_rate = (total_successful / total_processed * 100) if total_processed > 0 else 0
        
        logger.info(f"Final Results:")
        logger.info(f"  Total processed: {total_processed}")
        logger.info(f"  Total successful: {total_successful} ({final_success_rate:.1f}%)")
        logger.info(f"  Total failed: {total_failed} ({100-final_success_rate:.1f}%)")
        
        return successful_df, failed_df
    
    def _phase1_matching(self, send_df, open_df):
        """Phase 1: 0-11 second incremental matching"""
        successful_matches = []
        failed_records = []
        used_open_indices = set()  # Track which open records were matched
        match_stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 'no_match': 0, 'multiple_match': 0}
        
        # Get fields to add from open_df (exclude join keys)
        open_fields_to_add = [col for col in open_df.columns 
                            if col not in ['recipient_name', 'sent_date']]
        
        # Create email-based lookup for performance
        open_by_email = {}
        for email in open_df['recipient_name'].unique():
            open_by_email[email] = open_df[open_df['recipient_name'] == email].copy()
        
        logger.info(f"Phase 1: Processing {len(send_df)} send records (0-11 seconds)")
        
        # Process each send record individually
        for idx, send_record in send_df.iterrows():
            email = send_record['recipient_name']
            base_datetime = send_record['sent_date']
            
            # Get open records for this email
            if email not in open_by_email:
                # No open records for this email at all
                failed_records.append({
                    **send_record.to_dict(),
                    'failure_reason': 'no_open_records_for_email'
                })
                match_stats['no_match'] += 1
                continue
            
            email_opens = open_by_email[email]
            match_found = False
            
            # Try incremental matching: 0, +1, +2, +3, +4, +5, +6, +7, +8, +9, +10, +11 seconds
            for increment in range(12):
                search_datetime = base_datetime + pd.Timedelta(seconds=increment)
                
                # Find matches for this datetime
                matches = email_opens[email_opens['sent_date'] == search_datetime]
                
                if len(matches) == 1:
                    # Successful unique match
                    matched_record = matches.iloc[0]
                    matched_index = matches.index[0]
                    
                    # Track which open record was used
                    used_open_indices.add(matched_index)
                    
                    # Create final record: send_record + open_fields
                    final_record = send_record.to_dict()
                    for field in open_fields_to_add:
                        final_record[field] = matched_record[field]
                    
                    successful_matches.append(final_record)
                    match_stats[increment] += 1
                    match_found = True
                    break
                    
                elif len(matches) > 1:
                    # Multiple matches - add to failed records
                    failed_records.append({
                        **send_record.to_dict(),
                        'failure_reason': f'multiple_matches_at_plus_{increment}_seconds',
                        'match_count': len(matches)
                    })
                    match_stats['multiple_match'] += 1
                    match_found = True
                    break
            
            # No matches found in any increment
            if not match_found:
                failed_records.append({
                    **send_record.to_dict(),
                    'failure_reason': 'no_match_within_11_seconds'
                })
                match_stats['no_match'] += 1
        
        # Log Phase 1 statistics
        logger.info(f"Phase 1 match breakdown by time increment:")
        for i in range(12):
            if match_stats[i] > 0:
                logger.info(f"  +{i} seconds: {match_stats[i]} matches")
        
        if match_stats['no_match'] > 0:
            logger.info(f"  No matches: {match_stats['no_match']}")
        if match_stats['multiple_match'] > 0:
            logger.info(f"  Multiple matches: {match_stats['multiple_match']}")
        
        return successful_matches, failed_records, used_open_indices
    
    def _phase2_matching(self, failed_records, open_df, used_open_indices):
        """Phase 2: 12-60 second matching on failed records with unused open records"""
        phase2_successful = []
        final_failed = []
        match_stats = {}
        
        # Create subset of unused open records
        unused_open_df = open_df[~open_df.index.isin(used_open_indices)].copy()
        
        if len(unused_open_df) == 0:
            logger.info("Phase 2: No unused open records available")
            return [], failed_records
        
        logger.info(f"Phase 2: Using {len(unused_open_df)} unused open records")
        
        # Get fields to add from open_df (exclude join keys)
        open_fields_to_add = [col for col in open_df.columns 
                            if col not in ['recipient_name', 'sent_date']]
        
        # Create email-based lookup for unused opens
        unused_opens_by_email = {}
        for email in unused_open_df['recipient_name'].unique():
            unused_opens_by_email[email] = unused_open_df[unused_open_df['recipient_name'] == email].copy()
        
        # Process each failed record
        for failed_record in failed_records:
            email = failed_record['recipient_name']
            base_datetime = pd.to_datetime(failed_record['sent_date'])
            
            # Skip if this email has no unused open records
            if email not in unused_opens_by_email:
                final_failed.append(failed_record)
                continue
            
            email_opens = unused_opens_by_email[email]
            match_found = False
            
            # Try incremental matching: +12, +13, ..., +60 seconds
            for increment in range(12, 61):
                search_datetime = base_datetime + pd.Timedelta(seconds=increment)
                
                # Find matches for this datetime
                matches = email_opens[email_opens['sent_date'] == search_datetime]
                
                if len(matches) == 1:
                    # Successful unique match
                    matched_record = matches.iloc[0]
                    
                    # Create final record: failed_record + open_fields
                    final_record = failed_record.copy()
                    
                    # Remove failure-related fields
                    final_record.pop('failure_reason', None)
                    final_record.pop('match_count', None)
                    
                    # Add open fields
                    for field in open_fields_to_add:
                        final_record[field] = matched_record[field]
                    
                    phase2_successful.append(final_record)
                    
                    # Track statistics
                    if increment not in match_stats:
                        match_stats[increment] = 0
                    match_stats[increment] += 1
                    
                    match_found = True
                    break
                    
                elif len(matches) > 1:
                    # Multiple matches - keep as failed (as per requirement)
                    failed_record['failure_reason'] = f'multiple_matches_at_plus_{increment}_seconds_phase2'
                    failed_record['match_count'] = len(matches)
                    final_failed.append(failed_record)
                    match_found = True
                    break
            
            # No matches found in Phase 2
            if not match_found:
                failed_record['failure_reason'] = 'no_match_within_60_seconds'
                final_failed.append(failed_record)
        
        # Log Phase 2 statistics
        if match_stats:
            logger.info(f"Phase 2 match breakdown by time increment:")
            for increment in sorted(match_stats.keys()):
                logger.info(f"  +{increment} seconds: {match_stats[increment]} matches")
        
        return phase2_successful, final_failed
    
    def _join_with_contacts(self, send_open_df, contacts_df):
        """Join send-open data with contacts on recipient_email = Email (one-to-one)"""
        logger.info(f"Joining {len(send_open_df)} send-open records with contacts data")
        
        # Create lookup dictionary for faster contact matching
        contacts_lookup = {}
        for idx, contact_record in contacts_df.iterrows():
            email = contact_record['Email']
            if pd.notna(email) and email not in contacts_lookup:
                # Take first occurrence of each email
                contacts_lookup[email] = contact_record
        
        logger.info(f"Created contacts lookup with {len(contacts_lookup)} unique emails")
        
        successful_records = []
        failed_records = []
        
        # Iterate through each send-open record
        for idx, send_record in send_open_df.iterrows():
            recipient_email = send_record['Recipient Email']
            
            if pd.notna(recipient_email) and recipient_email in contacts_lookup:
                # Found matching contact - merge all contact fields
                contact_record = contacts_lookup[recipient_email]
                
                # Create merged record: send_record + contact fields
                merged_record = send_record.to_dict()
                
                # Add all contact fields
                for col in contacts_df.columns:
                    merged_record[col] = contact_record[col]
                
                successful_records.append(merged_record)
            else:
                # No matching contact found
                failed_record = send_record.to_dict()
                failed_record['failure_reason'] = 'Send email not found in contacts'
                failed_records.append(failed_record)
        
        # Convert to DataFrames
        successful_df = pd.DataFrame(successful_records) if successful_records else pd.DataFrame()
        failed_df = pd.DataFrame(failed_records) if failed_records else pd.DataFrame()
        
        # Add unique IDs to Company URL values in successful records
        if len(successful_df) > 0 and 'Company URL' in successful_df.columns:
            successful_df = self._add_company_url_ids(successful_df)
        
        # Verify record count
        total_output = len(successful_df) + len(failed_df)
        logger.info(f"Contacts join results: {len(successful_df)} successful, {len(failed_df)} failed")
        logger.info(f"Input records: {len(send_open_df)}, Output records: {total_output}")
        logger.info(f"Contacts join success rate: {(len(successful_df) / len(send_open_df) * 100):.1f}%")
        
        return successful_df, failed_df
    
    def _add_company_url_ids(self, df):
        """Add unique incremental IDs to Company URL values"""
        logger.info(f"Adding unique IDs to Company URL values")
        
        # Get unique Company URL values
        unique_company_urls = df['Company URL'].dropna().unique()
        
        # Create mapping of Company URL to unique ID (starting from 1)
        company_url_to_id = {url: idx + 1 for idx, url in enumerate(unique_company_urls)}
        
        # Add Company URL ID column
        df['Company URL ID'] = df['Company URL'].map(company_url_to_id)
        
        logger.info(f"Created {len(unique_company_urls)} unique Company URL IDs")
        for url, url_id in list(company_url_to_id.items())[:5]:  # Show first 5 mappings
            logger.info(f"  Company URL ID {url_id}: {url}")
        
        if len(unique_company_urls) > 5:
            logger.info(f"  ... and {len(unique_company_urls) - 5} more")
        
        return df
    
    def _integrate_account_history(self, successful_df, account_history_df):
        """Integrate Account History data with successful send-open joins"""
        logger.info(f"Integrating Account History data with {len(successful_df)} successful records")
        
        # Check if Company URL column exists
        if 'Company URL' not in successful_df.columns:
            logger.error(f"Company URL column not found in successful records. Available columns: {list(successful_df.columns)}")
            # Add placeholder columns for missing Company URL data
            successful_df['Latest edit date'] = 'Company URL column not found'
            successful_df['Account Owner'] = 'Company URL column not found'  
            successful_df['New Value'] = 'Company URL column not found'
            return successful_df
        
        logger.info(f"Using Company URL column for Account History matching")
        
        # Group by Company URL to find latest account history for each
        company_url_to_account_info = {}
        
        for company_url in successful_df['Company URL'].unique():
            # Skip NaN values
            if pd.isna(company_url):
                continue
                
            # Find matching records in account history (exact match, case insensitive)
            matching_accounts = account_history_df[
                account_history_df['Company URL'] == company_url
            ]
            
            if len(matching_accounts) == 0:
                # No match found
                company_url_to_account_info[company_url] = {
                    'Latest edit date': 'Company URL not found',
                    'Account Owner': 'Company URL not found', 
                    'New Value': 'Company URL not found'
                }
            else:
                # Sort by Edit Date to ensure we get the latest (handle NaT values)
                matching_accounts = matching_accounts.copy()
                matching_accounts = matching_accounts.dropna(subset=['Edit Date'])
                
                if len(matching_accounts) == 0:
                    company_url_to_account_info[company_url] = {
                        'Latest edit date': 'invalid date in account history',
                        'Account Owner': 'invalid date in account history',
                        'New Value': 'invalid date in account history'
                    }
                else:
                    # Sort by Edit Date descending and take the first (latest)
                    latest_record = matching_accounts.sort_values('Edit Date', ascending=False).iloc[0]
                    
                    logger.info(f"Company URL '{company_url}': Found {len(matching_accounts)} records, latest date: {latest_record['Edit Date']}")
                    
                    company_url_to_account_info[company_url] = {
                        'Latest edit date': latest_record['Edit Date'],
                        'Account Owner': latest_record['Account Owner'],
                        'New Value': latest_record['New Value']
                    }
        
        # Add new columns to successful_df
        successful_df['Latest edit date'] = successful_df['Company URL'].map(
            lambda x: company_url_to_account_info.get(x, {}).get('Latest edit date', 'Company URL not found') if pd.notna(x) else 'Company URL is NaN'
        )
        
        successful_df['Account Owner'] = successful_df['Company URL'].map(
            lambda x: company_url_to_account_info.get(x, {}).get('Account Owner', 'Company URL not found') if pd.notna(x) else 'Company URL is NaN'
        )
        
        successful_df['New Value'] = successful_df['Company URL'].map(
            lambda x: company_url_to_account_info.get(x, {}).get('New Value', 'Company URL not found') if pd.notna(x) else 'Company URL is NaN'
        )
        
        # Log statistics
        company_urls_found = sum(1 for info in company_url_to_account_info.values() 
                               if info['Latest edit date'] != 'Company URL not found')
        company_urls_not_found = len(company_url_to_account_info) - company_urls_found
        
        logger.info(f"Account History integration complete:")
        logger.info(f"  Company URLs found: {company_urls_found}")
        logger.info(f"  Company URLs not found: {company_urls_not_found}")
        
        return successful_df
    
    def _join_contact(self, merged_df, contact_df):
        """Join contact data (placeholder for future implementation)"""
        logger.info("Contact data processing not yet implemented")
        return merged_df
    
    def _join_account(self, merged_df, account_df):
        """Join account data (placeholder for future implementation)"""
        logger.info("Account data processing not yet implemented")
        return merged_df