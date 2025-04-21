import pandas as pd
from datetime import datetime, timedelta
import json
from models.risk_predictor import RiskPredictor
from bots.trello_integration import fetch_trello_data
from core.config import *
from core.logger import configure_logger

logger = configure_logger(__name__)

def create_sprint_report():
    """Generate comprehensive sprint report with error handling"""
    try:
        # Get data sources
        risk_data = RiskPredictor().predict_risk(days=7)
        if risk_data.empty:
            raise ValueError("Empty risk prediction data")
        
        trello_data = fetch_trello_data()
        
        if not isinstance(trello_data, list) or len(trello_data) == 0:
            return "# No Task Data Available\nTrello integration not working"
            
        # Generate metrics
        report = {
            "sprint_start": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "sprint_end": datetime.now().strftime("%Y-%m-%d"),
            "total_tasks": len(trello_data),
            "completed_tasks": sum(1 for c in trello_data if c.get('closed', False)),
            "blockers": sum(1 for c in trello_data if 'blocker' in c.get('name', '').lower()),
            "risk_forecast": json.loads(risk_data.to_json(orient='records'))
        }
        
        # Format as markdown
        md_report = f"""## Sprint Report ({report['sprint_start']} to {report['sprint_end']})

**Tasks Overview**
- Total Tasks: {report['total_tasks']}
- Completed: {report['completed_tasks']} ({report['completed_tasks']/report['total_tasks']:.0%})
- Active Blockers: {report['blockers']}

**Risk Forecast**
{risk_data.to_markdown()}

**Recommendations**
{generate_recommendations(report)}"""
        
        return md_report
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        return f"# Error Generating Report\n{str(e)}"

def generate_recommendations(report):
    """Generate actionable insights with fallbacks"""
    try:
        if report['blockers'] > 3:
            return "🚨 Immediate attention needed: Multiple blockers detected"
        if report['risk_forecast'] and report['risk_forecast'][-1]['risk']:
            return "⚠️ High risk predicted: Consider scope adjustment"
        return "✅ Stable trajectory: Maintain current pace"
    except:
        return "⚠️ Could not generate recommendations"