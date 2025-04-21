import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        return pd.DataFrame({
            'id': [f"task_{i}" for i in range(30)],
            'title': [f"Feature {i+1}" for i in range(30)],
            'due_date': [base_date + timedelta(days=np.random.randint(1, 21)) 
                       for _ in range(30)],
            'checklists': np.random.randint(1, 6, 30)
        })
    
    def get_tasks(self):
        return self.tasks.copy()

class TaskPrioritizer:
    def __init__(self):
        self.db = Database()
        self.model = RandomForestRegressor(n_estimators=15, random_state=42)
        
    def _generate_features(self, tasks):
        """Create features from task data"""
        tasks = tasks.copy()
        
        # Convert due_date to datetime
        if not pd.api.types.is_datetime64_any_dtype(tasks['due_date']):
            tasks['due_date'] = pd.to_datetime(tasks['due_date'])
            
        # Calculate days until due (handle negative values)
        tasks['days_until_due'] = (tasks['due_date'] - pd.Timestamp.now()).dt.days
        tasks['days_until_due'] = tasks['days_until_due'].clip(lower=0)
        
        # Calculate complexity
        tasks['complexity'] = np.log1p(tasks['checklists'])
        
        return tasks

    def prioritize(self):
        """Generate priority scores with fallback"""
        try:
            # Get and preprocess tasks first
            tasks = self.db.get_tasks()
            tasks = self._generate_features(tasks)
            
            # Validate columns
            required_cols = ['days_until_due', 'checklists']
            if not all(col in tasks.columns for col in required_cols):
                missing = [col for col in required_cols if col not in tasks.columns]
                raise ValueError(f"Missing columns: {missing}")
            
            if len(tasks) < 5:
                logger.warning("Using fallback heuristic")
                tasks['priority'] = (tasks['checklists'] * 0.6 + 
                                    (1 / (tasks['days_until_due'] + 0.01)))
            else:
                # ML prediction
                X = tasks[['days_until_due', 'complexity']]
                y = (tasks['checklists'] * 0.5 + 
                    np.random.uniform(0, 0.5, len(tasks)) + 
                    1 / (tasks['days_until_due'] + 0.01))
                
                self.model.fit(X, y)
                tasks['priority'] = self.model.predict(X)
            
            return tasks[['title', 'due_date', 'checklists', 'priority']].sort_values('priority', ascending=False).round(2)
            
        except Exception as e:
            logger.error(f"Prioritization failed: {str(e)}")
            return pd.DataFrame(columns=['title', 'due_date', 'checklists', 'priority'])

if __name__ == "__main__":
    try:
        prioritizer = TaskPrioritizer()
        prioritized = prioritizer.prioritize()
        
        if not prioritized.empty:
            print("TASK PRIORITIES:")
            prioritized['due_date'] = prioritized['due_date'].dt.strftime('%Y-%m-%d')
            print(prioritized[['title', 'due_date', 'checklists', 'priority']]
                  .head(10)
                  .to_markdown(index=False))
        else:
            print("⚠️ No tasks prioritized - check logs for errors")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        exit(1)