import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Database
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def generate_mock_sprints():
    db = Database()
    
    # Mock predictions
    dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
    df = pd.DataFrame({
        'ds': dates,
        'yhat': np.random.randint(5, 20, 60),
        'yhat_upper': np.random.randint(15, 30, 60),
        'risk': np.random.choice([True, False], 60)
    })
    db.save_prediction(df)
    
    # Mock tasks with ALL required columns
    tasks = pd.DataFrame({
        'id': [f"task_{i}" for i in range(30)],
        'title': [f"Task {i}" for i in range(30)],
        'due_date': [datetime.now() + timedelta(days=np.random.randint(1,14)) 
                    for _ in range(30)],
        'checklists': np.random.randint(1, 10, 30),
        'priority': np.random.uniform(0, 1, 30).round(2)  # Add priority column
    })
    
    db.save_tasks(tasks)

if __name__ == "__main__":
    generate_mock_sprints()