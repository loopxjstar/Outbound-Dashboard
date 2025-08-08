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
        # self.required_account_history_columns = ['Edit Date', 'Company URL', 'New Value', 'Account Owner']
        self.required_contacts_columns = ['Email']
        # self.required_opportunity_details_columns = ['Company URL', 'Amount', 'Created Date']
        
        # Column mapping rules for different file types
        self.column_mappings = {
            'send_mails': {
                'Recipient Name': 'recipient_name',
                'Date': 'sent_date',
                'recipient_email': 'Recipient Email',  # Lowercase mapping to system column
                'recipient_name': 'recipient_name',    # Direct mapping
                'sent_date': 'sent_date'               # Direct mapping
            },
            'open_mails': {
                'Recipient': 'recipient_name',     # User's "Recipient" → system's "recipient_name"
                'Sent': 'sent_date',               # User's "Sent" → system's "sent_date"
                'Opens': 'Views',                  # User's "Opens" → system's "Views"
                'Clicks': 'Clicks',               # Keep as-is
                'Last Opened': 'last_opened'      # User's "Last Opened" → system's "last_opened"
            },
            'contacts': {
                'Email': 'Email'  # Keep as is - will add more mappings as needed
            },
            # 'account_history': {
            #     'Edit Date': 'Edit Date',  # Keep as is - will add more mappings as needed
            #     'Company URL': 'Company URL',
            #     'New Value': 'New Value',
            #     'Account Owner': 'Account Owner'
            # }
        }
    
    def sheets_validator(self, files):
        """
        Comprehensive validation function for all uploaded CSV files.
        Validates headers, applies column mappings, and checks data integrity.
        
        Returns:
            tuple: (is_valid, error_messages, mapped_dataframes)
        """
        error_messages = []
        mapped_dataframes = {}
        
        logger.info("Starting comprehensive sheets validation...")
        
        # File type definitions with their requirements
        file_definitions = {
            'send_mails': {
                'display_name': 'Send Mails CSV',
                'required_columns': self.required_send_columns,
                'mapping': self.column_mappings['send_mails']
            },
            'open_mails': {
                'display_name': 'Open Mails CSV', 
                'required_columns': self.required_open_columns,
                'mapping': self.column_mappings['open_mails']
            },
            'contacts': {
                'display_name': 'Contacts CSV',
                'required_columns': self.required_contacts_columns,
                'mapping': self.column_mappings['contacts']
            },
            # 'account_history': {
            #     'display_name': 'Account History CSV',
            #     'required_columns': self.required_account_history_columns,
            #     'mapping': self.column_mappings['account_history']
            # }
        }
        
        # Validate each file
        for file_key, file_obj in files.items():
            if file_obj is None:
                error_messages.append(f"❌ **Missing File**: {file_definitions.get(file_key, {}).get('display_name', file_key)} is required but not uploaded.")
                continue
                
            if file_key not in file_definitions:
                continue  # Skip unknown file types
                
            file_def = file_definitions[file_key]
            
            try:
                # Load the CSV - handle both file paths and uploaded files
                if isinstance(file_obj, str):
                    # File path (like 'data/contacts.csv')
                    if not os.path.exists(file_obj):
                        error_messages.append(f"❌ **File Not Found**: {file_def['display_name']} file not found at {file_obj}")
                        continue
                    df = pd.read_csv(file_obj)
                    logger.info(f"Loaded {file_def['display_name']} from file path: {file_obj}")
                else:
                    # Uploaded file object
                    df = pd.read_csv(file_obj)
                    logger.info(f"Loaded {file_def['display_name']} from uploaded file")
                logger.info(f"Validating {file_def['display_name']}: {len(df)} rows, {len(df.columns)} columns")
                
                # Validation Rule 1: Check if file is empty
                if len(df) == 0:
                    error_messages.append(f"❌ **Empty File**: {file_def['display_name']} contains no data rows.")
                    continue
                
                # Validation Rule 2: Check available columns
                available_columns = list(df.columns)
                logger.info(f"Available columns in {file_def['display_name']}: {available_columns}")
                
                # Validation Rule 3: Apply column mapping and check for required columns
                mapped_columns = {}
                missing_columns = []
                
                for user_column, system_column in file_def['mapping'].items():
                    if user_column in available_columns:
                        mapped_columns[user_column] = system_column
                        logger.info(f"✅ Mapped '{user_column}' → '{system_column}' in {file_def['display_name']}")
                    else:
                        # Check if the system column exists directly (backward compatibility)
                        if system_column in available_columns:
                            mapped_columns[system_column] = system_column
                            logger.info(f"✅ Found direct match '{system_column}' in {file_def['display_name']}")
                        else:
                            missing_columns.append(f"'{user_column}' (maps to '{system_column}')")
                
                # Report missing columns
                if missing_columns:
                    error_messages.append(f"❌ **Missing Columns** in {file_def['display_name']}: {', '.join(missing_columns)}")
                    error_messages.append(f"📋 **Available Columns in the uploaded sheet**: {', '.join(available_columns)}")
                    continue
                
                # Validation Rule 4: Apply the mapping to rename columns
                df_mapped = df.copy()
                rename_dict = {user_col: sys_col for user_col, sys_col in mapped_columns.items() if user_col != sys_col}
                if rename_dict:
                    df_mapped = df_mapped.rename(columns=rename_dict)
                    logger.info(f"Applied column renaming in {file_def['display_name']}: {rename_dict}")
                
                # Validation Rule 5: Check for required columns after mapping
                final_columns = list(df_mapped.columns)
                missing_required = [col for col in file_def['required_columns'] if col not in final_columns]
                if missing_required:
                    error_messages.append(f"❌ **Missing Required Columns** in {file_def['display_name']} after mapping: {', '.join(missing_required)}")
                    continue
                
                # Validation Rule 6: Data type and content validation
                validation_result = self._validate_data_content(df_mapped, file_key, file_def['display_name'])
                if not validation_result['is_valid']:
                    error_messages.extend(validation_result['errors'])
                    continue
                
                # Validation Rule 7: Apply file-specific filtering rules
                df_filtered, filter_info = self._apply_filtering_rules(df_mapped, file_key, file_def['display_name'])
                if filter_info['filtered_count'] > 0:
                    logger.info(f"📝 {file_def['display_name']}: {filter_info['message']}")
                
                # If all validations pass, store the filtered dataframe
                mapped_dataframes[file_key] = df_filtered
                logger.info(f"✅ {file_def['display_name']} validation passed successfully")
                
            except Exception as e:
                error_messages.append(f"❌ **File Processing Error** in {file_def['display_name']}: {str(e)}")
                logger.error(f"Error processing {file_def['display_name']}: {str(e)}")
        
        # Final validation: Check if all required files passed validation
        required_files = ['send_mails', 'open_mails', 'contacts']  # Removed 'account_history'
        validated_files = list(mapped_dataframes.keys())
        
        is_valid = len(error_messages) == 0 and all(f in validated_files for f in required_files)
        
        if is_valid:
            logger.info("🎉 All sheets validation passed successfully!")
        else:
            logger.error(f"❌ Sheets validation failed with {len(error_messages)} errors")
            
        return is_valid, error_messages, mapped_dataframes
    
    def _validate_data_content(self, df, file_key, display_name):
        """
        Validate the actual data content within each file
        """
        errors = []
        
        try:
            # Date format validation for files with date columns
            if file_key in ['send_mails', 'open_mails']:
                if 'sent_date' in df.columns:
                    # Check if sent_date can be parsed
                    date_errors = 0
                    for idx, date_val in df['sent_date'].head(10).items():  # Check first 10 rows
                        if pd.isna(date_val):
                            date_errors += 1
                            continue
                        try:
                            pd.to_datetime(date_val, format='%d/%m/%Y %H:%M:%S', errors='raise')
                        except:
                            try:
                                pd.to_datetime(date_val, errors='raise')  # Try general parsing
                            except:
                                date_errors += 1
                    
                    if date_errors > 0:
                        errors.append(f"❌ **Date Format Error** in {display_name}: {date_errors} rows have invalid date format in 'sent_date'. Expected: DD/MM/YYYY HH:MM:SS")
            
            # elif file_key == 'account_history':
            #     if 'Edit Date' in df.columns:
            #         # Check Edit Date format
            #         date_errors = 0
            #         for idx, date_val in df['Edit Date'].head(10).items():
            #             if pd.isna(date_val):
            #                 date_errors += 1
            #                 continue
            #             try:
            #                 pd.to_datetime(date_val, format='%d/%m/%Y %H:%M:%S', errors='raise')
            #             except:
            #                 try:
            #                     pd.to_datetime(date_val, errors='raise')
            #                 except:
            #                     date_errors += 1
            #         
            #         if date_errors > 0:
            #             errors.append(f"❌ **Date Format Error** in {display_name}: {date_errors} rows have invalid date format in 'Edit Date'. Expected: DD/MM/YYYY HH:MM:SS")
            
            # Email format validation
            if file_key == 'send_mails' and 'Recipient Email' in df.columns:
                invalid_emails = 0
                for idx, email_val in df['Recipient Email'].head(10).items():
                    if pd.isna(email_val) or '@' not in str(email_val):
                        invalid_emails += 1
                
                if invalid_emails > 0:
                    errors.append(f"❌ **Email Format Error** in {display_name}: {invalid_emails} rows have invalid email format in 'Recipient Email'")
            
            elif file_key == 'contacts' and 'Email' in df.columns:
                invalid_emails = 0
                for idx, email_val in df['Email'].head(10).items():
                    if pd.isna(email_val) or '@' not in str(email_val):
                        invalid_emails += 1
                
                if invalid_emails > 0:
                    errors.append(f"❌ **Email Format Error** in {display_name}: {invalid_emails} rows have invalid email format in 'Email'")
            
            # Numeric validation for open_mails
            if file_key == 'open_mails':
                for col in ['Views', 'Clicks']:
                    if col in df.columns:
                        non_numeric = 0
                        for idx, val in df[col].head(10).items():
                            if pd.isna(val):
                                continue
                            try:
                                float(val)
                            except:
                                non_numeric += 1
                        
                        if non_numeric > 0:
                            errors.append(f"❌ **Numeric Format Error** in {display_name}: {non_numeric} rows have non-numeric values in '{col}'")
            
            return {'is_valid': len(errors) == 0, 'errors': errors}
            
        except Exception as e:
            return {'is_valid': False, 'errors': [f"❌ **Data Validation Error** in {display_name}: {str(e)}"]}
    
    def _apply_filtering_rules(self, df, file_key, display_name):
        """
        Apply file-specific filtering rules to clean data before processing
        """
        original_count = len(df)
        filtered_count = 0
        filter_messages = []
        
        try:
            # Send Mails CSV filtering rules
            if file_key == 'send_mails':
                # Rule 1: Remove records with "loopwork.co" in Domain column
                if 'Domain' in df.columns:
                    before_filter = len(df)
                    # Case-insensitive filtering for "loopwork.co"
                    df = df[~df['Domain'].str.lower().str.contains('loopwork.co', na=False)]
                    after_filter = len(df)
                    loopwork_filtered = before_filter - after_filter
                    
                    if loopwork_filtered > 0:
                        filtered_count += loopwork_filtered
                        filter_messages.append(f"Removed {loopwork_filtered} records with 'loopwork.co' domain")
                        logger.info(f"📝 {display_name}: Filtered out {loopwork_filtered} 'loopwork.co' records")
                else:
                    logger.warning(f"📝 {display_name}: 'Domain' column not found, skipping loopwork.co filtering")
                
                # Rule 2: Keep sent_date as-is (no time adjustment)
                if 'sent_date' in df.columns:
                    try:
                        # Convert to datetime if not already (for validation only)
                        df['sent_date'] = pd.to_datetime(df['sent_date'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                        
                        # Count valid dates
                        valid_dates = df['sent_date'].notna().sum()
                        
                        if valid_dates > 0:
                            filter_messages.append(f"Validated {valid_dates} sent_date values (no time adjustment)")
                            logger.info(f"📝 {display_name}: Validated {valid_dates} sent_date values (keeping original timestamps)")
                        else:
                            logger.warning(f"📝 {display_name}: No valid dates found in sent_date column")
                            
                    except Exception as e:
                        logger.error(f"📝 {display_name}: Error validating sent_date: {str(e)}")
                        filter_messages.append(f"Failed to validate sent_date: {str(e)}")
                else:
                    logger.warning(f"📝 {display_name}: 'sent_date' column not found, skipping date validation")
                
                # Rule 3: Keep recipient_name as-is (no cleaning)
                if 'recipient_name' in df.columns:
                    try:
                        # Just trim whitespace for basic cleaning
                        df['recipient_name'] = df['recipient_name'].str.strip()
                        
                        # Count processed values
                        processed_count = df['recipient_name'].notna().sum()
                        
                        filter_messages.append(f"Validated {processed_count} recipient_name values (no format cleaning)")
                        logger.info(f"📝 {display_name}: Validated {processed_count} recipient_name values (keeping original format)")
                        
                    except Exception as e:
                        logger.error(f"📝 {display_name}: Error validating recipient_name: {str(e)}")
                        filter_messages.append(f"Failed to validate recipient_name: {str(e)}")
                else:
                    logger.warning(f"📝 {display_name}: 'recipient_name' column not found, skipping recipient name validation")
            
            # Open Mails CSV filtering rules
            elif file_key == 'open_mails':
                # Rule 1: Split recipient_name by comma and take first value
                if 'recipient_name' in df.columns:
                    try:
                        # Store original values for comparison
                        original_sample = df['recipient_name'].dropna().head(3).tolist()
                        
                        # Clean the recipient_name column by splitting on comma and taking first part
                        def clean_recipient_comma_split(value):
                            if pd.isna(value):
                                return value
                            
                            value_str = str(value).strip()
                            
                            if ',' in value_str:
                                # Split by ',' and take the first part
                                # Example: "Breanna Hughes,Bailee Cooper,Harshit Gupta" -> "Breanna Hughes"
                                first_part = value_str.split(',', 1)[0]
                                # Trim spaces from the first part
                                first_part = first_part.strip()
                                return first_part
                            else:
                                # No ',' found, return the original value
                                # Example: "John Doe" -> "John Doe"
                                return value_str
                        
                        # Apply the cleaning function
                        df['recipient_name'] = df['recipient_name'].apply(clean_recipient_comma_split)
                        
                        # Get cleaned sample for comparison
                        cleaned_sample = df['recipient_name'].dropna().head(3).tolist()
                        
                        # Count how many values were processed
                        processed_count = df['recipient_name'].notna().sum()
                        
                        filter_messages.append(f"Split and extracted first names from {processed_count} recipient_name values")
                        logger.info(f"📝 {display_name}: Split {processed_count} recipient_name values by comma")
                        
                        # Log before/after examples for verification
                        if len(original_sample) > 0 and len(cleaned_sample) > 0:
                            logger.info(f"📝 {display_name}: Recipient name comma-split examples:")
                            for i, (orig, cleaned) in enumerate(zip(original_sample, cleaned_sample)):
                                # Check if value was changed
                                change_indicator = " (✂️ SPLIT)" if orig != cleaned else " (✅ NO CHANGE NEEDED)"
                                logger.info(f"📝   Example {i+1}: '{orig}' → '{cleaned}'{change_indicator}")
                        
                    except Exception as e:
                        logger.error(f"📝 {display_name}: Error splitting recipient_name: {str(e)}")
                        filter_messages.append(f"Failed to split recipient_name: {str(e)}")
                else:
                    logger.warning(f"📝 {display_name}: 'recipient_name' column not found, skipping recipient name splitting")
                
                # Rule 2: Convert sent_date format from "Jul 3, 2025, 02:14:21" to "DD/MM/YYYY HH:MM:SS"
                if 'sent_date' in df.columns:
                    try:
                        # Store original values for comparison
                        original_sample = df['sent_date'].dropna().head(3).tolist()
                        
                        # Convert date format
                        def convert_date_format(value):
                            if pd.isna(value):
                                return value
                            
                            value_str = str(value).strip()
                            
                            try:
                                # Parse the original format: "Jul 3, 2025, 02:14:21"
                                # This handles various month name formats
                                parsed_date = pd.to_datetime(value_str, errors='raise')
                                
                                # Convert to DD/MM/YYYY HH:MM:SS format
                                formatted_date = parsed_date.strftime('%d/%m/%Y %H:%M:%S')
                                return formatted_date
                                
                            except Exception as parse_error:
                                logger.warning(f"📝 {display_name}: Could not parse date '{value_str}': {str(parse_error)}")
                                return value_str  # Return original if parsing fails
                        
                        # Apply the conversion function
                        df['sent_date'] = df['sent_date'].apply(convert_date_format)
                        
                        # Get converted sample for comparison
                        converted_sample = df['sent_date'].dropna().head(3).tolist()
                        
                        # Count how many values were processed
                        processed_count = df['sent_date'].notna().sum()
                        
                        filter_messages.append(f"Converted {processed_count} sent_date values to DD/MM/YYYY HH:MM:SS format")
                        logger.info(f"📝 {display_name}: Converted {processed_count} sent_date values to standard format")
                        
                        # Log before/after examples for verification
                        if len(original_sample) > 0 and len(converted_sample) > 0:
                            logger.info(f"📝 {display_name}: Date format conversion examples:")
                            for i, (orig, converted) in enumerate(zip(original_sample, converted_sample)):
                                # Check if value was changed
                                change_indicator = " (🔄 CONVERTED)" if orig != converted else " (✅ ALREADY CORRECT)"
                                logger.info(f"📝   Example {i+1}: '{orig}' → '{converted}'{change_indicator}")
                        
                    except Exception as e:
                        logger.error(f"📝 {display_name}: Error converting sent_date format: {str(e)}")
                        filter_messages.append(f"Failed to convert sent_date format: {str(e)}")
                else:
                    logger.warning(f"📝 {display_name}: 'sent_date' column not found, skipping date format conversion")
                
                # Rule 3: Convert empty Views/Clicks values to 0
                for col in ['Views', 'Clicks']:
                    if col in df.columns:
                        try:
                            # Count null/empty values before conversion
                            null_count_before = df[col].isna().sum()
                            empty_count_before = (df[col] == '').sum() if df[col].dtype == 'object' else 0
                            
                            if null_count_before > 0 or empty_count_before > 0:
                                # Convert empty strings to NaN first, then fill NaN with 0
                                df[col] = df[col].replace('', pd.NA)  # Convert empty strings to NaN
                                df[col] = df[col].fillna(0)          # Convert NaN to 0
                                
                                # Convert to numeric to ensure proper data type
                                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                                
                                total_converted = null_count_before + empty_count_before
                                filter_messages.append(f"Converted {total_converted} empty '{col}' values to 0")
                                logger.info(f"📝 {display_name}: Converted {total_converted} empty '{col}' values to 0")
                            else:
                                # Still ensure numeric data type even if no nulls
                                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                                logger.info(f"📝 {display_name}: Validated '{col}' column (no empty values found)")
                                
                        except Exception as e:
                            logger.error(f"📝 {display_name}: Error converting empty '{col}' values: {str(e)}")
                            filter_messages.append(f"Failed to convert empty '{col}' values: {str(e)}")
                    else:
                        logger.warning(f"📝 {display_name}: '{col}' column not found")
            
            # Future: Add filtering rules for other file types here
            # elif file_key == 'contacts':
            #     # Add Contacts filtering rules
            # elif file_key == 'account_history':
            #     # Add Account History filtering rules
            
            # Prepare filter info
            total_filtered = original_count - len(df)
            if total_filtered > 0:
                message = f"Filtered out {total_filtered} records total. Details: {'; '.join(filter_messages)}"
            else:
                message = "No records filtered"
                
            filter_info = {
                'original_count': original_count,
                'final_count': len(df),
                'filtered_count': total_filtered,
                'message': message,
                'details': filter_messages
            }
            
            return df, filter_info
            
        except Exception as e:
            logger.error(f"Error applying filtering rules to {display_name}: {str(e)}")
            # Return original dataframe if filtering fails
            return df, {
                'original_count': original_count,
                'final_count': len(df), 
                'filtered_count': 0,
                'message': f"Filtering failed: {str(e)}",
                'details': []
            }
    
    def process_files(self, files):
        """
        Process uploaded CSV files and return joined data with failed records
        """
        try:
            # Step 1: Comprehensive validation and column mapping
            is_valid, error_messages, mapped_dataframes = self.sheets_validator(files)
            
            if not is_valid:
                logger.error("Files validation failed. Returning error messages.")
                # Return error messages instead of None to display to user
                return None, None, error_messages, 0
            
            # Step 2: Extract validated and mapped dataframes
            send_df = mapped_dataframes['send_mails']
            open_df = mapped_dataframes['open_mails']
            contacts_df = mapped_dataframes['contacts']
            # account_history_df = mapped_dataframes['account_history']
            
            # Store original Send Mails count for KPI calculations
            original_send_count = len(send_df)
            logger.info(f"Original Send Mails count: {original_send_count}")
            
            logger.info("All files validated successfully. Proceeding with data processing...")
            
            # Clean and prepare data
            send_df = self._clean_data(send_df, 'send')
            open_df = self._clean_data(open_df, 'open')
            contacts_df = self._clean_data(contacts_df, 'contacts')
            # account_history_df = self._clean_data(account_history_df, 'account_history')
            # opportunity_details_df = self._clean_data(opportunity_details_df, 'opportunity_details')
            
            # Perform incremental datetime join (send + open)
            send_open_successful, send_open_failed = self._join_send_open(send_df, open_df)
            
            if send_open_successful is None:
                return None, None, ["❌ **Join Error**: Failed to join Send Mails and Open Mails data"], original_send_count
            
            # Join send-open data with contacts
            contacts_result = self._join_with_contacts(send_open_successful, contacts_df)
            
            # Check if contacts join returned an error (no matches)
            if len(contacts_result) == 3:
                # Error case: returned (None, None, error_messages)
                error_result = contacts_result + [original_send_count]  # Add original send count to error
                return error_result  # Pass through the error with original send count
            else:
                # Success case: returned (successful_df, failed_df)
                contacts_successful, contacts_failed = contacts_result
            
            # Combine all failed records
            all_failed = []
            if len(send_open_failed) > 0:
                all_failed.extend(send_open_failed.to_dict('records'))
            if len(contacts_failed) > 0:
                all_failed.extend(contacts_failed.to_dict('records'))
            
            final_failed_df = pd.DataFrame(all_failed) if all_failed else pd.DataFrame()
            
            # Integrate Account History data - COMMENTED OUT
            # if len(contacts_successful) > 0:
            #     contacts_successful = self._integrate_account_history(contacts_successful, account_history_df)
            
            # Integrate Opportunity Details data (final step) - COMMENTED OUT
            # if len(contacts_successful) > 0:
            #     contacts_successful = self._integrate_opportunity_details(contacts_successful, opportunity_details_df)
            
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
            return successful_df, final_failed_df, [], original_send_count  # Add original send count
            
        except Exception as e:
            logger.error(f"Error processing files: {str(e)}")
            return None, None, [f"❌ **Processing Error**: {str(e)}"], 0  # Return 0 for original count on error
    
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
        
        # if 'Edit Date' in df.columns:
        #     df['Edit Date'] = pd.to_datetime(df['Edit Date'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
            
        if 'Created Date' in df.columns:
            df['Created Date'] = pd.to_datetime(df['Created Date'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        
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
        elif file_type == 'opportunity_details':
            if 'Amount' in df.columns:
                df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
        
        # Remove rows with null key columns
        if file_type == 'send':
            df = df.dropna(subset=['recipient_name', 'sent_date'])
        elif file_type == 'open':
            df = df.dropna(subset=['recipient_name', 'sent_date'])
        # elif file_type == 'account_history':
        #     df = df.dropna(subset=['Edit Date', 'Company URL'])
        elif file_type == 'contacts':
            df = df.dropna(subset=['Email'])
        elif file_type == 'opportunity_details':
            df = df.dropna(subset=['Company URL', 'Amount', 'Created Date'])
        
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
        
        # Calculate success rate safely (avoid division by zero)
        if len(send_open_df) > 0:
            success_rate = (len(successful_df) / len(send_open_df) * 100)
            logger.info(f"Contacts join success rate: {success_rate:.1f}%")
        else:
            logger.warning("No send-open records to join with contacts")
            
        # Check if no records matched with contacts
        if len(successful_df) == 0:
            logger.error("❌ No records matched with contacts sheet")
            # Return error message for user display
            return None, None, ["❌ **No records matched with contacts sheet**: No emails from Send-Open data found in Contacts CSV"]
        
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
    
    # def _integrate_account_history(self, successful_df, account_history_df):
    #     """Integrate Account History data with successful send-open joins"""
    #     logger.info(f"Integrating Account History data with {len(successful_df)} successful records")
    #     
    #     # Check if Company URL column exists
    #     if 'Company URL' not in successful_df.columns:
    #         logger.error(f"Company URL column not found in successful records. Available columns: {list(successful_df.columns)}")
    #         # Add placeholder columns for missing Company URL data
    #         successful_df['Latest edit date'] = 'Company URL column not found'
    #         successful_df['Account Owner'] = 'Company URL column not found'  
    #         successful_df['New Value'] = 'Company URL column not found'
    #         return successful_df
    #     
    #     logger.info(f"Using Company URL column for Account History matching")
    #     
    #     # Group by Company URL to find latest account history for each
    #     company_url_to_account_info = {}
    #     
    #     for company_url in successful_df['Company URL'].unique():
    #         # Skip NaN values
    #         if pd.isna(company_url):
    #             continue
    #             
    #         # Find matching records in account history (exact match, case insensitive)
    #         matching_accounts = account_history_df[
    #             account_history_df['Company URL'] == company_url
    #         ]
    #         
    #         if len(matching_accounts) == 0:
    #             # No match found
    #             company_url_to_account_info[company_url] = {
    #                 'Latest edit date': 'Company URL not found',
    #                 'Account Owner': 'Company URL not found', 
    #                 'New Value': 'Company URL not found'
    #             }
    #         else:
    #             # Sort by Edit Date to ensure we get the latest (handle NaT values)
    #             matching_accounts = matching_accounts.copy()
    #             matching_accounts = matching_accounts.dropna(subset=['Edit Date'])
    #             
    #             if len(matching_accounts) == 0:
    #                 company_url_to_account_info[company_url] = {
    #                     'Latest edit date': 'invalid date in account history',
    #                     'Account Owner': 'invalid date in account history',
    #                     'New Value': 'invalid date in account history'
    #                 }
    #             else:
    #                 # Sort by Edit Date descending and take the first (latest)
    #                 latest_record = matching_accounts.sort_values('Edit Date', ascending=False).iloc[0]
    #                 
    #                 logger.info(f"Company URL '{company_url}': Found {len(matching_accounts)} records, latest date: {latest_record['Edit Date']}")
    #                 
    #                 company_url_to_account_info[company_url] = {
    #                     'Latest edit date': latest_record['Edit Date'],
    #                     'Account Owner': latest_record['Account Owner'],
    #                     'New Value': latest_record['New Value']
    #                 }
    #     
    #     # Add new columns to successful_df
    #     successful_df['Latest edit date'] = successful_df['Company URL'].map(
    #         lambda x: company_url_to_account_info.get(x, {}).get('Latest edit date', 'Company URL not found') if pd.notna(x) else 'Company URL is NaN'
    #     )
    #     
    #     successful_df['Account Owner'] = successful_df['Company URL'].map(
    #         lambda x: company_url_to_account_info.get(x, {}).get('Account Owner', 'Company URL not found') if pd.notna(x) else 'Company URL is NaN'
    #     )
    #     
    #     successful_df['New Value'] = successful_df['Company URL'].map(
    #         lambda x: company_url_to_account_info.get(x, {}).get('New Value', 'Company URL not found') if pd.notna(x) else 'Company URL is NaN'
    #     )
    #     
    #     # Log statistics
    #     company_urls_found = sum(1 for info in company_url_to_account_info.values() 
    #                            if info['Latest edit date'] != 'Company URL not found')
    #     company_urls_not_found = len(company_url_to_account_info) - company_urls_found
    #     
    #     logger.info(f"Account History integration complete:")
    #     logger.info(f"  Company URLs found: {company_urls_found}")
    #     logger.info(f"  Company URLs not found: {company_urls_not_found}")
    #     
    #     return successful_df
    
    # def _integrate_opportunity_details(self, successful_df, opportunity_details_df):
    #     """Integrate Opportunity Details data with the final successful records"""
    #     logger.info(f"Integrating Opportunity Details data with {len(successful_df)} successful records")
    #     
    #     # Check if Company URL column exists
    #     if 'Company URL' not in successful_df.columns:
    #         logger.error(f"Company URL column not found in successful records. Available columns: {list(successful_df.columns)}")
    #         # Add placeholder columns for missing Company URL data
    #         for col_name in opportunity_details_df.columns:
    #             if col_name != 'Company URL':  # Don't duplicate the join key
    #                 successful_df[col_name] = 'Company URL column not found'
    #         return successful_df
    #     
    #     logger.info(f"Using Company URL column for Opportunity Details matching")
    #     
    #     # First, deduplicate opportunity_details_df by keeping only latest Created Date for each Company URL
    #     logger.info(f"Deduplicating Opportunity Details: {len(opportunity_details_df)} records before deduplication")
    #     
    #     # Sort by Created Date descending and keep first (latest) for each Company URL
    #     deduplicated_opportunities = opportunity_details_df.sort_values('Created Date', ascending=False).drop_duplicates(subset=['Company URL'], keep='first')
    #     
    #     duplicates_removed = len(opportunity_details_df) - len(deduplicated_opportunities)
    #     logger.info(f"Removed {duplicates_removed} duplicate records, keeping {len(deduplicated_opportunities)} unique Company URLs with latest Created Date")
    #     
    #     # Create lookup dictionary for opportunity details (now guaranteed one record per Company URL)
    #     opportunity_lookup = {}
    #     
    #     for idx, opp_record in deduplicated_opportunities.iterrows():
    #         company_url = opp_record['Company URL']
    #         if pd.notna(company_url):
    #             opportunity_lookup[company_url] = opp_record  # Single record, not a list
    #     
    #     logger.info(f"Created opportunity lookup with {len(opportunity_lookup)} unique Company URLs")
    #     
    #     # Get all opportunity columns except Company URL (join key)
    #     opportunity_columns = [col for col in deduplicated_opportunities.columns if col != 'Company URL']
    #     
    #     # Initialize all opportunity columns with empty values for all records
    #     for col_name in opportunity_columns:
    #         successful_df[col_name] = ''
    #     
    #     # Track statistics
    #     matched_companies = 0
    #     
    #     # Iterate through each successful record and try to match opportunities
    #     for idx in successful_df.index:
    #         company_url = successful_df.loc[idx, 'Company URL']
    #         
    #         if pd.notna(company_url) and company_url in opportunity_lookup:
    #             # Found matching opportunity (single record now)
    #             opportunity_record = opportunity_lookup[company_url]
    #             matched_companies += 1
    #             
    #             # Attach opportunity fields for this Company URL
    #             for col_name in opportunity_columns:
    #                 if pd.notna(opportunity_record[col_name]):
    #                     successful_df.loc[idx, col_name] = opportunity_record[col_name]
    #                 else:
    #                     successful_df.loc[idx, col_name] = ''
    #     
    #     # Log statistics
    #     unique_company_urls = successful_df['Company URL'].nunique()
    #     companies_not_found = unique_company_urls - matched_companies
    #     
    #     logger.info(f"Opportunity Details integration complete:")
    #     logger.info(f"  Unique Company URLs in final data: {unique_company_urls}")
    #     logger.info(f"  Company URLs with opportunities: {matched_companies}")
    #     logger.info(f"  Company URLs without opportunities: {companies_not_found}")
    #     logger.info(f"  Total opportunities attached: {matched_companies} (1:1 mapping)")
    #     
    #     return successful_df
    
    def _join_contact(self, merged_df, contact_df):
        """Join contact data (placeholder for future implementation)"""
        logger.info("Contact data processing not yet implemented")
        return merged_df
    
    def _join_account(self, merged_df, account_df):
        """Join account data (placeholder for future implementation)"""
        logger.info("Account data processing not yet implemented")
        return merged_df