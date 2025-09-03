#!/usr/bin/env python3
"""
Pre-process SDR email and calls data files for dashboard.
Run this script to generate processed data files for production dashboard.

Usage:
    python preprocess_data.py

Input Files (in data/ folder):
- Email: {sdr_name}_send.csv, {sdr_name}_open.csv (e.g., himanshu_send.csv, himanshu_open.csv)
- Calls: calls_data.csv
- Contacts: contacts.csv

Output Files (in data/processed_files/):
- processed_email_data.csv
- contacts_failed_records.csv  
- processed_calls_data.csv
- preprocessing_metadata.json
"""

import pandas as pd
import os
import glob
import json
from datetime import datetime
from src.data_processor import DataProcessor
from src.calls_processor import CallsProcessor
from src.combined_processor import CombinedProcessor
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scan_sdr_files():
    """
    Scan data/ folder for SDR files with naming convention: {sdr_name}_send.csv, {sdr_name}_open.csv
    
    Returns:
        list: List of dicts with SDR configurations
              [{'name': 'himanshu', 'send_file': 'data/himanshu_send.csv', 'open_file': 'data/himanshu_open.csv'}]
    """
    logger.info("Scanning for SDR files in data/ folder...")
    
    # Find all send files
    send_files = glob.glob('data/*_send.csv')
    sdr_configs = []
    
    for send_file in send_files:
        # Extract SDR name from filename
        filename = os.path.basename(send_file)
        sdr_name = filename.replace('_send.csv', '')
        
        # Check if corresponding open file exists
        open_file = f'data/{sdr_name}_open.csv'
        
        if os.path.exists(open_file):
            sdr_configs.append({
                'name': sdr_name,
                'send_file': send_file,
                'open_file': open_file
            })
            logger.info(f"  ✅ Found SDR: {sdr_name}")
        else:
            logger.warning(f"  ⚠️  Found {send_file} but missing {open_file}")
    
    logger.info(f"Found {len(sdr_configs)} complete SDR file pairs")
    return sdr_configs

def process_email_data():
    """
    Process email data using existing multi-SDR logic
    
    Returns:
        tuple: (successful_df, failed_df, processing_stats)
    """
    logger.info("=" * 60)
    logger.info("PROCESSING EMAIL DATA")
    logger.info("=" * 60)
    
    # Scan for SDR files
    sdr_configs = scan_sdr_files()
    
    if not sdr_configs:
        logger.error("No SDR files found! Please ensure files follow naming convention: {sdr_name}_send.csv, {sdr_name}_open.csv")
        return None, None, None
    
    processor = DataProcessor()
    all_send_open_successful = []
    all_send_open_failed = []
    sdr_stats = {}
    
    # Step 1: Process each SDR individually (Send-Open join only)
    logger.info(f"Step 1: Processing {len(sdr_configs)} SDRs individually...")
    
    for config in sdr_configs:
        sdr_name = config['name']
        logger.info(f"Processing SDR: {sdr_name}")
        
        # Process this SDR's Send-Open join
        send_open_successful, send_open_failed, errors = processor.process_single_sdr(
            config['send_file'],
            config['open_file'], 
            sdr_name
        )
        
        if send_open_successful is not None:
            all_send_open_successful.append(send_open_successful)
            if send_open_failed is not None and len(send_open_failed) > 0:
                all_send_open_failed.append(send_open_failed)
            
            # Store stats for this SDR
            sdr_stats[sdr_name] = {
                'total_send': len(send_open_successful) + (len(send_open_failed) if send_open_failed is not None else 0),
                'joined': len(send_open_successful),
                'failed': len(send_open_failed) if send_open_failed is not None else 0
            }
            
            logger.info(f"  ✅ {sdr_name}: {len(send_open_successful)} Send-Open joined, {len(send_open_failed) if send_open_failed is not None else 0} failed")
        else:
            logger.error(f"  ❌ {sdr_name}: Failed - {', '.join(errors)}")
            sdr_stats[sdr_name] = {'error': ', '.join(errors)}
    
    # Step 2: Combine all SDRs' Send-Open data
    if not all_send_open_successful:
        logger.error("No SDR Send-Open joins were successful")
        return None, None, sdr_stats
    
    combined_send_open = pd.concat(all_send_open_successful, ignore_index=True)
    combined_send_open_failed = pd.concat(all_send_open_failed, ignore_index=True) if all_send_open_failed else pd.DataFrame()
    
    logger.info(f"Step 2: Combined {len(all_send_open_successful)} SDRs into {len(combined_send_open)} total Send-Open records")
    
    # Step 3: Join combined data with contacts
    logger.info("Step 3: Joining combined data with contacts...")
    
    final_successful, contacts_failed, errors = processor.process_multi_sdr_combined(combined_send_open)
    
    if final_successful is not None:
        logger.info(f"  ✅ Contacts join: {len(final_successful)} successful, {len(contacts_failed) if contacts_failed is not None else 0} failed")
        
        # Prepare processing stats
        processing_stats = {
            'send_open_join_stats': sdr_stats,
            'contacts_join_stats': {
                'total_send_open_records': len(combined_send_open),
                'successful_contacts_join': len(final_successful),
                'failed_contacts_join': len(contacts_failed) if contacts_failed is not None else 0
            }
        }
        
        return final_successful, contacts_failed, processing_stats
    else:
        logger.error(f"Failed to join with contacts: {', '.join(errors)}")
        return None, None, sdr_stats

def process_combined_data(email_data, calls_data):
    """
    Process combined email and calls data by joining them
    
    Returns:
        tuple: (combined_df, processing_stats)
    """
    logger.info("=" * 60)
    logger.info("PROCESSING COMBINED DATA")
    logger.info("=" * 60)
    
    if email_data is None or calls_data is None:
        logger.error("Cannot create combined data: Email or Calls data is missing")
        return None, {'error': 'Missing email or calls data'}
    
    logger.info(f"Combining {len(email_data)} email records with {len(calls_data)} call records...")
    
    processor = CombinedProcessor()
    
    try:
        # Use the join_email_calls method to combine data
        joined_data, email_only_data, calls_only_data, join_stats = processor.join_email_calls(email_data, calls_data)
        
        if joined_data is not None:
            logger.info(f"  ✅ Combined data created: {len(joined_data)} records")
            logger.info(f"  📧 Records with calls data: {join_stats.get('joined_records', 0)}")
            logger.info(f"  📧 Records without calls: {join_stats.get('email_only_records', 0)}")
            
            stats = {
                'total_combined_records': len(joined_data),
                'records_with_calls': join_stats.get('joined_records', 0),
                'records_without_calls': join_stats.get('email_only_records', 0),
                'emails_with_call_data': join_stats.get('emails_with_calls', 0),
                'success_rate': join_stats.get('join_success_rate', 0)
            }
            
            return joined_data, stats
        else:
            logger.error("Failed to create combined data")
            return None, {'error': 'Join failed'}
            
    except Exception as e:
        logger.error(f"Error processing combined data: {str(e)}")
        return None, {'error': str(e)}

def process_calls_data():
    """
    Process calls data using existing CallsProcessor logic
    
    Returns:
        tuple: (calls_df, processing_stats)
    """
    logger.info("=" * 60)
    logger.info("PROCESSING CALLS DATA")
    logger.info("=" * 60)
    
    calls_file = 'data/calls_data.csv'
    
    if not os.path.exists(calls_file):
        logger.warning(f"Calls file not found: {calls_file}")
        return None, {'error': 'calls_data.csv not found'}
    
    logger.info(f"Processing calls file: {calls_file}")
    
    processor = CallsProcessor()
    
    try:
        with open(calls_file, 'rb') as f:
            calls_success, calls_errors, calls_data = processor.process_calls_file(f)
        
        if calls_success and calls_data is not None:
            logger.info(f"  ✅ Processed {len(calls_data)} call records successfully")
            
            stats = {
                'total_records': len(calls_data),
                'successful': True,
                'errors': calls_errors if calls_errors else []
            }
            
            return calls_data, stats
        else:
            logger.error(f"  ❌ Calls processing failed: {calls_errors}")
            return None, {'error': calls_errors}
            
    except Exception as e:
        logger.error(f"Error processing calls file: {str(e)}")
        return None, {'error': str(e)}

def create_output_directory():
    """Create output directory if it doesn't exist"""
    output_dir = 'data/processed_files'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    return output_dir

def save_results(email_successful, email_failed, email_stats, calls_data, calls_stats, combined_data, combined_stats):
    """
    Save all processed results to output files
    """
    logger.info("=" * 60)
    logger.info("SAVING RESULTS")
    logger.info("=" * 60)
    
    output_dir = create_output_directory()
    
    # Save email data
    if email_successful is not None:
        email_file = os.path.join(output_dir, 'processed_email_data.csv')
        email_successful.to_csv(email_file, index=False)
        logger.info(f"✅ Saved {len(email_successful)} email records to {email_file}")
    
    # Save email contacts failures
    if email_failed is not None and len(email_failed) > 0:
        failed_file = os.path.join(output_dir, 'contacts_failed_records.csv')
        email_failed.to_csv(failed_file, index=False)
        logger.info(f"📝 Saved {len(email_failed)} contacts failed records to {failed_file}")
    
    # Save calls data
    if calls_data is not None:
        calls_file = os.path.join(output_dir, 'processed_calls_data.csv')
        calls_data.to_csv(calls_file, index=False)
        logger.info(f"✅ Saved {len(calls_data)} call records to {calls_file}")
    
    # Save combined data
    if combined_data is not None:
        combined_file = os.path.join(output_dir, 'processed_combined_data.csv')
        combined_data.to_csv(combined_file, index=False)
        logger.info(f"✅ Saved {len(combined_data)} combined records to {combined_file}")
    
    # Save metadata
    metadata = {
        'processing_date': datetime.now().isoformat(),
        'email_processing': email_stats,
        'calls_processing': calls_stats,
        'combined_processing': combined_stats,
        'output_files': {
            'email_data': 'processed_email_data.csv' if email_successful is not None else None,
            'contacts_failed': 'contacts_failed_records.csv' if email_failed is not None and len(email_failed) > 0 else None,
            'calls_data': 'processed_calls_data.csv' if calls_data is not None else None,
            'combined_data': 'processed_combined_data.csv' if combined_data is not None else None
        }
    }
    
    metadata_file = os.path.join(output_dir, 'preprocessing_metadata.json')
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"📊 Saved processing metadata to {metadata_file}")

def main():
    """Main preprocessing function"""
    print("\n" + "=" * 60)
    print("SDR DATA PREPROCESSING SCRIPT")
    print("=" * 60)
    print("\nThis script will process:")
    print("- Email data: {sdr_name}_send.csv + {sdr_name}_open.csv files")
    print("- Calls data: calls_data.csv")
    print("\nOutput will be saved to data/processed_files/")
    print("\nStarting preprocessing automatically...")
    
    try:
        # Process email data
        email_successful, email_failed, email_stats = process_email_data()
        
        # Process calls data
        calls_data, calls_stats = process_calls_data()
        
        # Process combined data
        combined_data = None
        combined_stats = {}
        if email_successful is not None and calls_data is not None:
            combined_data, combined_stats = process_combined_data(email_successful, calls_data)
        
        # Save results
        save_results(email_successful, email_failed, email_stats, calls_data, calls_stats, combined_data, combined_stats)
        
        # Summary
        print("\n" + "=" * 60)
        print("PREPROCESSING COMPLETE")
        print("=" * 60)
        
        if email_successful is not None:
            print(f"✅ Email Processing: {len(email_successful)} successful records")
        else:
            print("❌ Email Processing: Failed")
        
        if calls_data is not None:
            print(f"✅ Calls Processing: {len(calls_data)} records")
        else:
            print("❌ Calls Processing: Failed")
        
        if combined_data is not None:
            print(f"✅ Combined Processing: {len(combined_data)} records")
        else:
            print("❌ Combined Processing: Failed or skipped")
        
        print(f"\nOutput files saved to: data/processed_files/")
        
    except Exception as e:
        logger.error(f"Preprocessing failed with error: {str(e)}")
        print(f"\n❌ Preprocessing failed: {str(e)}")

if __name__ == "__main__":
    main()