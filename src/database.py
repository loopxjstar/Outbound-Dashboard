import sqlite3
import pandas as pd
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="data/analytics.db"):
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create processed_data table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS processed_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recipient_email TEXT NOT NULL,
                        domain TEXT,
                        date_sent DATE NOT NULL,
                        open_count INTEGER DEFAULT 0,
                        clicks INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_batch TEXT
                    )
                ''')
                
                # Create index for faster queries
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_email_date 
                    ON processed_data (recipient_email, date_sent)
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    def save_processed_data(self, df, batch_id=None):
        """Save processed data to database"""
        try:
            if batch_id is None:
                batch_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Add batch ID to dataframe
            df_copy = df.copy()
            df_copy['file_batch'] = batch_id
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                df_copy.to_sql('processed_data', conn, if_exists='append', index=False)
                logger.info(f"Saved {len(df_copy)} records to database with batch ID: {batch_id}")
                
            return batch_id
            
        except Exception as e:
            logger.error(f"Error saving data to database: {str(e)}")
            return None
    
    def get_processed_data(self, start_date=None, end_date=None, batch_id=None):
        """Retrieve processed data from database"""
        try:
            query = "SELECT * FROM processed_data WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date_sent >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date_sent <= ?"
                params.append(end_date)
                
            if batch_id:
                query += " AND file_batch = ?"
                params.append(batch_id)
            
            query += " ORDER BY date_sent DESC"
            
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn, params=params)
                
            # Convert date column
            if not df.empty:
                df['date_sent'] = pd.to_datetime(df['date_sent'])
                
            logger.info(f"Retrieved {len(df)} records from database")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving data from database: {str(e)}")
            return pd.DataFrame()
    
    def get_batch_history(self):
        """Get list of all file batches"""
        try:
            query = '''
                SELECT 
                    file_batch,
                    COUNT(*) as record_count,
                    MIN(date_sent) as earliest_date,
                    MAX(date_sent) as latest_date,
                    MAX(created_at) as uploaded_at
                FROM processed_data 
                GROUP BY file_batch 
                ORDER BY uploaded_at DESC
            '''
            
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn)
                
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving batch history: {str(e)}")
            return pd.DataFrame()
    
    def delete_batch(self, batch_id):
        """Delete a specific batch from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM processed_data WHERE file_batch = ?", (batch_id,))
                deleted_count = cursor.rowcount
                conn.commit()
                
            logger.info(f"Deleted {deleted_count} records from batch: {batch_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting batch {batch_id}: {str(e)}")
            return 0