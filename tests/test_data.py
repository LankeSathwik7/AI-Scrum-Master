# test_data.py
import numpy as np
from core.database import Database
import pandas as pd
from datetime import datetime, timedelta

db = Database()

# Mock tasks
tasks = pd.DataFrame({
    'id': [f"task_{i}" for i in range(20)],
    'title': [f"Feature {i}" for i in range(20)],
    'due_date': [datetime.now() + timedelta(days=np.random.randint(1,14)) for _ in range(20)],
    'checklists': np.random.randint(1, 5, 20)
})

db.conn.execute('DELETE FROM tasks')
tasks.to_sql('tasks', db.conn, if_exists='append', index=False)