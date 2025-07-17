import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.required_send_columns = ['recipient_email', 'domain', 'date_sent']
        self.required_open_columns = ['recipient_email', 'date_sent', 'open_count', 'clicks']
    
    def process_files(self, files):
        """
        Process uploaded CSV files and return joined data
        """
        try:
            # Load CSV files
            send_df = self._load_csv(files['send'], 'send')
            open_df = self._load_csv(files['open'], 'open')
            
            if send_df is None or open_df is None:
                return None
            
            # Validate required columns
            if not self._validate_columns(send_df, self.required_send_columns, 'send'):
                return None
            
            if not self._validate_columns(open_df, self.required_open_columns, 'open'):
                return None
            
            # Clean and prepare data
            send_df = self._clean_data(send_df, 'send')
            open_df = self._clean_data(open_df, 'open')
            
            # Perform join
            merged_df = self._join_send_open(send_df, open_df)
            
            # Process contact and account files if provided
            if files.get('contact'):
                contact_df = self._load_csv(files['contact'], 'contact')
                if contact_df is not None:
                    merged_df = self._join_contact(merged_df, contact_df)
            
            if files.get('account'):
                account_df = self._load_csv(files['account'], 'account')
                if account_df is not None:
                    merged_df = self._join_account(merged_df, account_df)
            
            logger.info(f"Successfully processed {len(merged_df)} records")
            return merged_df
            
        except Exception as e:
            logger.error(f"Error processing files: {str(e)}")
            return None
    
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
        
        # Convert date columns
        if 'date_sent' in df.columns:
            df['date_sent'] = pd.to_datetime(df['date_sent'], errors='coerce')
        
        # Clean email addresses
        if 'recipient_email' in df.columns:
            df['recipient_email'] = df['recipient_email'].str.lower().str.strip()
        
        # Handle numeric columns
        if file_type == 'open':
            df['open_count'] = pd.to_numeric(df['open_count'], errors='coerce').fillna(0)
            df['clicks'] = pd.to_numeric(df['clicks'], errors='coerce').fillna(0)
        
        # Remove rows with null key columns
        if file_type == 'send':
            df = df.dropna(subset=['recipient_email', 'date_sent'])
        elif file_type == 'open':
            df = df.dropna(subset=['recipient_email', 'date_sent'])
        
        logger.info(f"Cleaned {file_type} data: {len(df)} rows remaining")
        return df
    
    def _join_send_open(self, send_df, open_df):
        """Join send and open dataframes"""
        try:
            # Aggregate open data in case of duplicates
            open_agg = open_df.groupby(['recipient_email', 'date_sent']).agg({
                'open_count': 'sum',
                'clicks': 'sum'
            }).reset_index()
            
            # Add other columns from open_df (excluding aggregated ones)
            other_open_cols = [col for col in open_df.columns 
                             if col not in ['recipient_email', 'date_sent', 'open_count', 'clicks']]
            
            if other_open_cols:
                open_other = open_df.groupby(['recipient_email', 'date_sent'])[other_open_cols].first().reset_index()
                open_agg = open_agg.merge(open_other, on=['recipient_email', 'date_sent'], how='left')
            
            # Perform LEFT JOIN
            merged_df = send_df.merge(
                open_agg,
                on=['recipient_email', 'date_sent'],
                how='left'
            )
            
            # Fill NaN values for open metrics
            merged_df['open_count'] = merged_df['open_count'].fillna(0)
            merged_df['clicks'] = merged_df['clicks'].fillna(0)
            
            logger.info(f"Joined send and open data: {len(merged_df)} rows")
            return merged_df
            
        except Exception as e:
            logger.error(f"Error joining send and open data: {str(e)}")
            return None
    
    def _join_contact(self, merged_df, contact_df):
        """Join contact data (placeholder for future implementation)"""
        logger.info("Contact data processing not yet implemented")
        return merged_df
    
    def _join_account(self, merged_df, account_df):
        """Join account data (placeholder for future implementation)"""
        logger.info("Account data processing not yet implemented")
        return merged_df