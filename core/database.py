import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
from core.logger import configure_logger

logger = configure_logger(__name__)

class Database:
    def __init__(self, db_name='sprints.db'):
        self.conn = sqlite3.connect(db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        self._create_tables()
        
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # Database versioning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Get current version
        cursor.execute("SELECT MAX(version) FROM schema_version")
        current_version = cursor.fetchone()[0] or 0
        
        # Version 1: Initial schema
        if current_version < 1:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    ds TEXT PRIMARY KEY,
                    yhat REAL,
                    yhat_upper REAL,
                    risk BOOLEAN,
                    recommendation TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    due_date TEXT,
                    checklists INTEGER,
                    priority REAL
                )
            ''')
            cursor.execute("INSERT INTO schema_version (version) VALUES (1)")
            
        # Version 2: Add indexes
        if current_version < 2:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_predictions_ds 
                ON predictions(ds)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_priority 
                ON tasks(priority)
            ''')
            cursor.execute("INSERT INTO schema_version (version) VALUES (2)")

        # Version 3: Add retrospectives table
        if current_version < 3:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retrospectives (
                    id INTEGER PRIMARY KEY,
                    sentiment_score REAL,
                    key_phrases TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute("INSERT INTO schema_version (version) VALUES (3)")

        # Version 4: Add team capacity
        if current_version < 4:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS team_capacity (
                    member TEXT PRIMARY KEY,
                    available_hours INTEGER
                )
            ''')
            cursor.execute("INSERT INTO schema_version (version) VALUES (4)")
        
        self.conn.commit()

    def save_prediction(self, forecast):
        """Store prediction results with explicit transaction"""
        forecast['ds'] = forecast['ds'].dt.strftime('%Y-%m-%d')
        try:
            with self.conn:
                forecast.to_sql('predictions', self.conn, 
                              if_exists='replace', index=False,
                              dtype={'ds': 'TIMESTAMP'})
                logger.info(f"Saved {len(forecast)} predictions")
        except Exception as e:
            logger.error(f"Save failed: {str(e)}")
            raise

    def get_predictions(self):
        """Retrieve predictions with proper date formatting"""
        try:
            df = pd.read_sql('SELECT * FROM predictions', self.conn)
            if not df.empty:
                df['ds'] = pd.to_datetime(df['ds'])
            return df
        except Exception as e:
            logger.error(f"Failed to load predictions: {str(e)}")
            return pd.DataFrame()

    def save_tasks(self, tasks):
        """Store prioritized tasks with transaction"""
        try:
            # Convert due_date and validate checklists
            tasks = tasks.copy()
            if 'due_date' in tasks.columns:
                tasks['due_date'] = pd.to_datetime(tasks['due_date'], errors='coerce')
            
            # Validate checklists are numeric
            tasks['checklists'] = pd.to_numeric(tasks['checklists'], errors='coerce')
            
            # Filter valid records
            valid_tasks = tasks.dropna(subset=['priority', 'checklists'])
            
            with self.conn:
                valid_tasks.to_sql('tasks', self.conn, 
                                if_exists='replace', index=False,
                                dtype={'due_date': 'TIMESTAMP'})
                logger.info(f"Saved {len(valid_tasks)} valid tasks")
        except Exception as e:
            logger.error(f"Task save failed: {str(e)}")
            raise

    def get_tasks(self):
        """Retrieve tasks for prioritization"""
        try:
            return pd.read_sql('SELECT * FROM tasks', self.conn)
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {str(e)}")
            return pd.DataFrame()
        
    def get_prioritized_tasks(self):
        """Retrieve tasks with proper formatting"""
        try:
            tasks = pd.read_sql('''
                SELECT title, due_date, checklists, priority 
                FROM tasks 
                ORDER BY priority DESC 
                LIMIT 10
            ''', self.conn)
            
            if not tasks.empty and 'due_date' in tasks.columns:
                tasks['due_date'] = pd.to_datetime(tasks['due_date']).dt.strftime('%Y-%m-%d')
            return tasks
        except Exception as e:
            logger.error(f"Failed to load tasks: {str(e)}")
            return pd.DataFrame()

def initialize_database():
    Database()._create_tables()

if __name__ == "__main__":
    initialize_database()