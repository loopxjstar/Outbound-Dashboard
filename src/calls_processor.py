import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CallsProcessor:
    """
    Simple Calls Data Processor - Single CSV file with basic validation
    """
    
    def __init__(self):
        # Required columns for calls record CSV
        self.required_columns = [
            'Assigned', 
            'Call Disposition', 
            'Date', 
            'Company / Account', 
            'Contact', 
            'Call Duration (seconds)',
            'Email',
            'Full Comments'
        ]
    
    def validate_calls_file(self, file_obj):
        """
        Simple validation - just check for required headers
        
        Args:
            file_obj: Uploaded CSV file
            
        Returns:
            tuple: (is_valid, error_messages, dataframe)
        """
        error_messages = []
        
        try:
            # Load the CSV with automatic encoding detection
            df = self._load_csv_with_encoding(file_obj)
            logger.info(f"Loaded calls CSV: {len(df)} rows, {len(df.columns)} columns")
            
            # Check if file is empty
            if len(df) == 0:
                error_messages.append("❌ **Empty File**: Calls CSV contains no data rows.")
                return False, error_messages, None
            
            # Check for required columns
            available_columns = list(df.columns)
            missing_columns = [col for col in self.required_columns if col not in available_columns]
            
            if missing_columns:
                error_messages.append(f"❌ **Missing Required Columns**: {', '.join(missing_columns)}")
                error_messages.append(f"📋 **Available Columns**: {', '.join(available_columns)}")
                return False, error_messages, None
            
            logger.info(f"✅ Calls CSV validation passed: All required columns present")
            return True, [], df
            
        except Exception as e:
            error_messages.append(f"❌ **File Processing Error**: {str(e)}")
            return False, error_messages, None
    
    def _load_csv_with_encoding(self, file_obj):
        """
        Load CSV file with automatic encoding detection
        Tries common encodings: utf-8, latin-1, cp1252, iso-8859-1
        """
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
        
        for encoding in encodings:
            try:
                # Reset file pointer to beginning
                file_obj.seek(0)
                df = pd.read_csv(file_obj, encoding=encoding)
                logger.info(f"Successfully loaded CSV with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                logger.warning(f"Failed to load CSV with {encoding} encoding, trying next...")
                continue
            except Exception as e:
                logger.error(f"Error loading CSV with {encoding} encoding: {str(e)}")
                continue
        
        # If all encodings fail, try with error handling
        try:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, encoding='utf-8', encoding_errors='ignore')
            logger.warning("Loaded CSV with UTF-8 encoding, ignoring invalid characters")
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV with all attempted encodings: {str(e)}")
            raise Exception(f"Unable to read file with any supported encoding. Please save your CSV file as UTF-8.")
    
    def process_calls_file(self, file_obj):
        """
        Simple processing - just validate and return the data as-is
        
        Args:
            file_obj: Uploaded CSV file
            
        Returns:
            tuple: (is_valid, error_messages, dataframe)
        """
        try:
            # Validate file
            is_valid, error_messages, df = self.validate_calls_file(file_obj)
            
            if not is_valid:
                return False, error_messages, None
            
            # Convert Date column to datetime for filtering (but keep original data intact)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Convert Call Duration to numeric if needed
            if 'Call Duration (seconds)' in df.columns:
                df['Call Duration (seconds)'] = pd.to_numeric(df['Call Duration (seconds)'], errors='coerce').fillna(0)
            
            logger.info(f"Successfully processed {len(df)} call records")
            return True, [], df
            
        except Exception as e:
            error_messages = [f"❌ **Processing Error**: {str(e)}"]
            return False, error_messages, None