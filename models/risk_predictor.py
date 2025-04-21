import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict
import numpy as np
import pandas as pd
from prophet import Prophet
from datetime import datetime, timedelta
import requests
from core.config import TRELLO_BOARD_ID, TRELLO_API_KEY, TRELLO_TOKEN, RISK_THRESHOLD
from core.logger import configure_logger

logger = configure_logger(__name__)

class RiskPredictor:
    def __init__(self):
        self.model = Prophet(
            changepoint_range=0.8,
            n_changepoints=15,
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        self._trained = False
        logger.info("Prophet model initialized")

    def _fetch_trello_data(self):
        """Fetch and process Trello data with enhanced error handling"""
        try:
            url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/cards"
            params = {
                "key": TRELLO_API_KEY,
                "token": TRELLO_TOKEN,
                "checklists": "all",
                "fields": "dateLastActivity,checklists"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            logger.info(f"Found {len(response.json())} cards")
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=60)
            daily_tasks = defaultdict(int)
            
            for card in response.json():
                try:
                    if not card.get('dateLastActivity') or not card.get('checklists'):
                        continue
                        
                    card_date = pd.to_datetime(card['dateLastActivity']).date()
                    tasks = sum(len(cl['checkItems']) for cl in card['checklists'])
                    
                    if start_date <= card_date <= end_date:
                        daily_tasks[card_date] += tasks
                except Exception as e:
                    logger.warning(f"Skipping card {card.get('id')}: {str(e)}")
            
            df = pd.DataFrame([
                {"ds": pd.Timestamp(date), "y": count}
                for date, count in daily_tasks.items()
            ]).sort_values('ds')
            
            if df.empty or len(df) < 7:
                logger.warning("Using enhanced mock data")
                return self._generate_fallback_data()
                
            return df
            
        except Exception as e:
            logger.error(f"Trello API Error: {str(e)}")
            return self._generate_fallback_data()

    def _generate_fallback_data(self):
        """Generate realistic sprint simulation data"""
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        np.random.seed(42)  # For reproducible results
        base_pattern = 10 * np.sin(np.linspace(0, 4*np.pi, 60))  # 2-week cycle
        noise = np.random.normal(0, 2, 60)
        return pd.DataFrame({
            'ds': dates,
            'y': np.clip(base_pattern + noise + 15, 0, None)  # Offset to prevent negative values
        })

    def train(self):
        try:
            df = self._fetch_trello_data()
            
            if len(df) < 7:
                raise ValueError("Insufficient historical data")
                
            self.model.fit(df)
            self._trained = True
            logger.info(f"Model trained with {len(df)} data points")
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            self._trained = False

    def predict_risk(self, days=7):
        if not self._trained:
            self.train()
            
        try:
            future = self.model.make_future_dataframe(periods=days)
            forecast = self.model.predict(future)
            
            forecast['ds'] = pd.to_datetime(forecast['ds']).dt.tz_localize(None)
            forecast['yhat'] = forecast['yhat'].clip(0, None).round(1)
            forecast['yhat_upper'] = forecast['yhat_upper'].clip(0, None).round(1)
            forecast['risk'] = forecast['yhat_upper'] > RISK_THRESHOLD

            risk_days = forecast[forecast['risk']]
            if not risk_days.empty:
                logger.warning(f"Risk predicted on {len(risk_days)} days")
                forecast['recommendation'] = forecast.apply(
                    lambda row: f"Reduce scope by {int(row['yhat_upper'] - RISK_THRESHOLD)} tasks" 
                    if row['risk'] else "", axis=1)
            
            return forecast[['ds', 'yhat', 'yhat_upper', 'risk', 'recommendation']].tail(days)
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return pd.DataFrame()

if __name__ == "__main__":
    try:
        predictor = RiskPredictor()
        forecast = predictor.predict_risk()
        print("SUCCESS! Risk Forecast:")
        print(forecast.to_markdown(index=False))
    except Exception as e:
        logger.error(f"Critical failure: {str(e)}")
        exit(1)