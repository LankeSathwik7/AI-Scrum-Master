import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
import requests
from core.config import TRELLO_API_KEY, TRELLO_BOARD_ID, TRELLO_TOKEN
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from core.logger import configure_logger

logger = configure_logger(__name__)

class Database:
    """Temporary database mock until proper DB setup"""
    def __init__(self):
        self.tasks = self._mock_tasks()
        
    def _mock_tasks(self):
        """Generate realistic mock tasks"""
        np.random.seed(42)
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        features = [
            "User Authentication Flow",
            "Payment Gateway Integration",
            "Mobile Responsive Design",
            "API Rate Limiting",
            "Dashboard Analytics",
            "Notification System",
            "Search Optimization",
            "Database Sharding",
            "CI/CD Pipeline",
            "Error Monitoring"
        ]

        return pd.DataFrame({
            'id': [f"task_{uuid.uuid4().hex[:6]}" for _ in range(30)],
            'title': np.random.choice(features, 30),
            'due_date': [base_date + timedelta(days=np.random.randint(1, 21)) 
                       for _ in range(30)],
            'checklists': np.random.randint(1, 9, 30)
        })
    
    def get_tasks(self):
        """Retrieve real tasks from Trello"""
        try:
            url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/cards"
            params = {
                "key": TRELLO_API_KEY,
                "token": TRELLO_TOKEN,
                "fields": "name,due,checklists",
                "checklists": "all"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            cards = response.json()
            tasks = pd.DataFrame([{
                'id': card['id'],
                'title': card['name'],
                'due_date': card.get('due'),
                'checklists': sum(len(cl['checkItems']) + sum(1 for item in cl['checkItems'] if item['state'] == 'complete')
                for cl in card.get('checklists', [])
            )
            } for card in cards])
            
            logger.debug(f"Fetched {len(tasks)} tasks from Trello")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to fetch Trello tasks: {str(e)}")
            return self._mock_tasks()  # Fallback to mock data

class TaskPrioritizer:
    def __init__(self):
        self.db = Database()
        self.model = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_split=5, random_state=42)
        self.features = ['checklists', 'days_until_due']
        
    def _generate_features(self, tasks):
        """Create features from task data with NaN handling"""
        tasks = tasks.copy()

        # Ensure ID exists
        tasks['id'] = tasks.get('id', [f"task_{i}" for i in range(len(tasks))])
        
        # Handle missing due dates by setting them 1 year in the future
        default_due_date = pd.Timestamp.now() + pd.DateOffset(weeks=2)
        tasks['due_date'] = pd.to_datetime(
            tasks['due_date'].fillna(default_due_date)
        )
        
        # Calculate days until due with NaN protection
        tasks['days_until_due'] = (tasks['due_date'] - pd.Timestamp.now()).dt.days
        tasks['days_until_due'] = tasks['days_until_due'].clip(lower=0).fillna(365)

        tasks['weeks_until_due'] = tasks['days_until_due'] / 7
        
        # Handle missing checklists
        tasks['checklists'] = tasks['checklists'].fillna(0).astype(int)
        
        # Calculate complexity with zero protection
        tasks['complexity'] = np.log1p(tasks['checklists'].replace(0, 1))
        
        return tasks
    
    def _safe_normalize(self, series):
        """Handle zero-division in normalization"""
        if series.nunique() == 1:
            return pd.Series([0.5]*len(series))  # Default neutral priority
        return (series - series.min()) / (series.max() - series.min())

    def _heuristic_priority(self, tasks):
        """Fallback when insufficient data"""
        return (1 / (tasks['days_until_due'] + 1)) * 0.7 + \
               (tasks['checklists'] * 0.3)
    
    def _calculate_target(self, tasks):
        """Calculate target variable for ML model"""
        return (
            tasks['checklists'] * 0.8 + 
            np.random.uniform(0, 0.2, len(tasks)) + 
            1 / (tasks['days_until_due']/7 + 0.1)
        )

    def _calculate_priority(self, tasks):
        """Synthetic priority scoring until real labels exist"""
        # Mock business value = f(checklists, days_until_due)
        X = tasks[self.features]
        y = (tasks['checklists'] * 0.6 + 
             (1 / (tasks['days_until_due'] + 1) * 0.4))
        return y

    def prioritize(self):
        """Generate priority scores with fallback"""
        try:
            # Get and preprocess tasks first
            tasks = self.db.get_tasks()
            tasks = self._generate_features(tasks)

            # Validate mandatory fields
            if 'id' not in tasks.columns:
                tasks['id'] = [f"task_{i}" for i in range(len(tasks))]
                
            if tasks[['days_until_due', 'checklists']].isnull().any().any():
                raise ValueError("Missing values in critical columns")

            # Choose strategy based on data size
            if len(tasks) < 3:
                logger.warning("Insufficient tasks for ML, using heuristic")
                tasks['priority'] = self._heuristic_priority(tasks)
            else:
                # Machine learning approach
                X = tasks[['days_until_due', 'complexity']]
                y = self._calculate_target(tasks)
                
                self.model.fit(X, y)
                #tasks['priority'] = self.model.predict(X)
                tasks['priority'] = self._calculate_priority(tasks)
                tasks['priority'] = self._safe_normalize(tasks['priority'])

            return tasks[['id', 'title', 'due_date', 'checklists', 'priority']].sort_values('priority', ascending=False).round(2)
            
        except Exception as e:
            logger.error(f"Prioritization failed: {str(e)}")
            return pd.DataFrame(columns=['id', 'title', 'due_date', 'checklists', 'priority'])

if __name__ == "__main__":
    try:
        prioritizer = TaskPrioritizer()
        prioritized = prioritizer.prioritize()
        
        if not prioritized.empty:
            print("TASK PRIORITIES:")
            print(prioritized.head(10).to_markdown(index=False))
            
            # Save to database
            from core.database import Database
            db = Database()
            db.save_tasks(prioritized[['id', 'title', 'due_date', 'checklists', 'priority']])
            print("\n✅ Successfully saved to database")
        else:
            print("⚠️ No tasks prioritized - check logs")
            
    except Exception as e:
        logger.error(f"Task prioritization failed: {str(e)}")
        exit(1)