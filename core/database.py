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
        self._create_tables()
        
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # Add database versioning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Get current version
        cursor.execute("SELECT MAX(version) FROM schema_version")
        current_version = cursor.fetchone()[0] or 0
        
        # Apply migrations
        if current_version < 1:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    date TEXT PRIMARY KEY,
                    predicted_tasks REAL,
                    upper_bound REAL,
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
            
        if current_version < 2:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_predictions_date 
                ON predictions(date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_priority 
                ON tasks(priority)
            ''')
            cursor.execute("INSERT INTO schema_version (version) VALUES (2)")
        
        self.conn.commit()
        logger.info(f"Database version {current_version} → 2")

    def save_prediction(self, forecast):
        """Store prediction results"""
        forecast.to_sql('predictions', self.conn, if_exists='replace', index=False)
        
    def get_tasks(self):
        """Retrieve tasks for prioritization"""
        return pd.read_sql('SELECT * FROM tasks', self.conn)
    
def initialize_database():
    Database()._create_tables()

if __name__ == "__main__":
    initialize_database()