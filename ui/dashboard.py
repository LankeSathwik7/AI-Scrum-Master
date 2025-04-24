import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
import os
import logging
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import (
    CRITICAL_THRESHOLD,
    POSITIVE_THRESHOLD,
    RISK_THRESHOLD,
    TRELLO_LIST_ID,
    TRELLO_API_KEY,
    TRELLO_TOKEN,
    SLACK_BOT_TOKEN
)
from models.risk_predictor import RiskPredictor
from bots.retrospective import RetrospectiveAnalyzer
from models.task_prioritizer import TaskPrioritizer
from core.database import Database
from core.logger import configure_logger

logger = configure_logger(__name__)

def fetch_trello_cards(list_id):
    """Fetch cards from Trello list with retries and better error handling"""
    try:
        response = requests.get(
            f"https://api.trello.com/1/lists/{list_id}/cards",
            params={"key": TRELLO_API_KEY, "token": TRELLO_TOKEN},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Trello API Error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching Trello cards: {str(e)}")
        return []

def check_slack_connection():
    """Verify Slack API connectivity"""
    try:
        WebClient(token=SLACK_BOT_TOKEN).auth_test()
        return True
    except SlackApiError as e:
        logger.error(f"Slack connection failed: {e.response['error']}")
        return False
    except Exception as e:
        logger.error(f"Slack connection error: {str(e)}")
        return False

def check_trello_connection():
    """Verify Trello API connectivity"""
    try:
        response = requests.get(
            f"https://api.trello.com/1/members/me",
            params={"key": TRELLO_API_KEY, "token": TRELLO_TOKEN},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Trello connection error: {str(e)}")
        return False

# def display_connection_status():
#     """Show API connection status"""
#     with st.expander("🔌 Connection Status", expanded=True):
#         cols = st.columns(3)
#         with cols[0]:
#             if check_trello_connection():
#                 st.success("✅ Trello Connected")
#             else:
#                 st.error("❌ Trello Connection Failed")
#         with cols[1]:
#             if check_slack_connection():
#                 st.success("✅ Slack Connected")
#             else:
#                 st.error("❌ Slack Connection Failed")
#         with cols[2]:
#             try:
#                 db = Database()
#                 if db.get_tasks() is not None:
#                     st.success("✅ Database Connected")
#                 else:
#                     st.error("❌ Database Error")
#             except Exception as e:
#                 st.error(f"❌ Database Error: {str(e)}")

def show_blockers_section():
    """Display current blockers from Trello"""
    st.header("🚧 Active Blockers", divider="red")
    with st.spinner("Fetching Trello cards..."):
        cards = fetch_trello_cards(TRELLO_LIST_ID)
    
    if not cards:
        st.warning("No cards found in the specified list")
        return

    blocker_count = 0
    cols = st.columns(3)
    
    for card in cards:
        blocker_triggers = ['blocker', 'blocked', 'stuck', 'help needed', 'urgent', 'critical']
        is_blocker = any(trigger in card.get('name', '').lower() or 
                       trigger in card.get('desc', '').lower()
                       for trigger in blocker_triggers)
        
        if is_blocker:
            with cols[blocker_count % 3]:
                with st.expander(f"🔴 {card['name'][:30]}", expanded=True):
                    st.markdown(f"**Description**\n{card.get('desc', 'No description')}")
                    
                    metadata = []
                    if card.get('due'):
                        try:
                            due_date = pd.to_datetime(card['due']).strftime('%Y-%m-%d')
                            metadata.append(f"📅 Due: {due_date}")
                        except Exception:
                            pass
                    
                    if card.get('labels'):
                        labels = [l['name'] for l in card['labels'] if l['name']]
                        if labels:
                            metadata.append(f"🏷️ {', '.join(labels)}")
                    
                    if metadata:
                        st.markdown("\n".join(metadata))
                    
                    last_activity = card.get('dateLastActivity', datetime.now().isoformat())
                    st.caption(f"Last updated: {pd.to_datetime(last_activity).strftime('%Y-%m-%d %H:%M')}")
            
            blocker_count += 1

    if blocker_count == 0:
        st.success("🎉 No active blockers detected!")

def show_analytics_section():
    """Display predictive analytics section"""
    tab1, tab2 = st.tabs(["Risk Forecast", "Task Priorities"])
    
    with tab1:
        st.header("📈 Sprint Analytics", divider="blue")
        db = Database()
        actual_tasks = db.get_tasks()
        st.caption(f"Total tasks in system: {len(actual_tasks)}")
        
        try:
            predictor = RiskPredictor()
            forecast = predictor.predict_risk()
            
            if not forecast.empty:
                forecast['ds'] = pd.to_datetime(forecast['ds'])
                fig = px.line(forecast, x="ds", y="yhat", 
                            title="AI-Predicted Burndown Trend",
                            labels={"ds": "Date", "yhat": "Predicted Tasks"})
                fig.add_hline(y=RISK_THRESHOLD, line_dash="dot",
                            annotation_text="Risk Threshold", line_color="red")
                fig.update_layout(height=400, xaxis=dict(rangeslider=dict(visible=True)))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No forecast data available")
        except Exception as e:
            st.error(f"Prediction failed: {str(e)}")
            logger.exception("Analytics section error")

    with tab2:
        st.header("⚠️ Risk Alerts", divider="orange")
        if 'forecast' in locals() and not forecast.empty:
            try:
                max_risk = forecast.loc[forecast['risk'].idxmax()]
                st.metric("Highest Risk Day", 
                        value=max_risk['ds'].strftime('%a, %b %d'),
                        delta=f"{max_risk['yhat_upper']:.1f} tasks")
                st.progress(min(100, int(max_risk['yhat_upper'] * 10)))
                st.markdown("""
                **Recommended Actions**
                - Review scope with product owner
                - Pair programming sessions
                - Expedite blocker resolution
                """)
            except Exception:
                st.warning("Error processing risk data")
        else:
            st.warning("No risk predictions available")
    
    st_autorefresh(interval=60*1000, key="analytics_refresh")

def show_capacity_planning():
    st.header("Team Capacity")
    db = Database()
    capacity = db.get_team_capacity()  # New method to implement
    st.bar_chart(capacity.set_index('member'))

def show_team_insights():
    """Display team insights section"""
    st.header("👥 Team Insights", divider="green")
    tab1, tab2 = st.tabs(["Availability", "Sentiment"])

    with tab1:
        st.subheader("Weekly Availability")
        try:
            availability_data = pd.DataFrame({
                'Member': ['Alice', 'Bob', 'Charlie'],
                'Mon': [8, 6, 0], 'Tue': [8, 8, 4],
                'Wed': [8, 7, 8], 'Thu': [8, 8, 8],
                'Fri': [6, 8, 4]
            }).melt(id_vars=['Member'], var_name='Day', value_name='Hours')
            
            fig = px.bar(availability_data, x='Day', y='Hours', color='Member',
                        barmode='group', height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Availability data error: {str(e)}")

    with tab2:
        st.subheader("Retrospective Analysis")
        try:
            analyzer = RetrospectiveAnalyzer()
            analysis = analyzer.analyze_sentiment()
            
            if 'error' in analysis:
                st.error(f"Analysis Error: {analysis['error']}")
                return

            total = analysis['positive'] + analysis['negative'] + analysis['neutral']
            smoothing = 1e-6
            positive_pct = (analysis['positive'] + smoothing) / (total + 3*smoothing) * 100
            negative_pct = (analysis['negative'] + smoothing) / (total + 3*smoothing) * 100
            neutral_pct = (analysis['neutral'] + smoothing) / (total + 3*smoothing) * 100

            col1, col2 = st.columns([2, 3])
            with col1:
                st.metric("Positive Sentiment", f"{positive_pct:.1f}%",
                         delta=f"{analysis['positive']} messages")
                st.metric("Critical Feedback", f"{negative_pct:.1f}%",
                         delta=f"{analysis['negative']} messages")
                st.caption(f"Analyzed {analysis['samples']} messages from last 7 days")

            with col2:
                fig = px.pie(
                    values=[analysis['positive'], analysis['negative'], analysis['neutral']],
                    names=['Positive', 'Critical', 'Neutral'],
                    hole=0.4,
                    color_discrete_sequence=['#4CAF50', '#F44336', '#FFC107']
                )
                fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)

            if negative_pct >= CRITICAL_THRESHOLD:
                st.warning(f"""
                ⚠️ {analysis['negative']} Critical Feedback Items Found:
                - Schedule retro meeting
                - Review technical blockers
                - Prioritize bug fixes
                """)
            elif positive_pct >= POSITIVE_THRESHOLD:
                st.success(f"""
                🎉 {analysis['positive']} Positive Highlights:
                - Share success in #general
                - Recognize contributors
                """)
            else:
                st.info("""
                💡 Balanced Sentiment:
                - Monitor trends
                - Encourage feedback
                """)
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")

def main():
    """Main dashboard application"""
    try:
        st.set_page_config(page_title="AI Scrum Master", layout="wide")
        #st.write("Dashboard initialized")  # Debug 1
        
        st.title("🤖 AI Scrum Master Dashboard")
        #st.write("Title set")  # Debug 2
        
        #display_connection_status()
        #st.write("Connection status displayed")  # Debug 3
        
        st_autorefresh(interval=5*60*1000, key="data_refresh")
        #st.write("Auto-refresh configured")  # Debug 4
        
        show_blockers_section()
        #st.write("Blockers section loaded")  # Debug 5
        
        show_analytics_section() 
        #st.write("Analytics section loaded")  # Debug 6
        
        show_team_insights()
        #st.write("Team insights loaded")  # Debug 7

        # Database sections
        db = Database()
        with st.container():
            st.header("📊 Data Insights", divider="rainbow")
            
            # Risk Predictions - Full width
            st.subheader("Risk Predictions")
            try:
                forecast = db.get_predictions()
                if not forecast.empty:
                    fig = px.line(forecast, x='ds', y='yhat_upper',
                                title="Task Completion Forecast",
                                height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No risk predictions available")
            except Exception as e:
                st.error(f"Failed to load predictions: {str(e)}")

            # Task Priorities - Below risk predictions
            st.subheader("Task Priorities")
            try:
                tasks = db.get_prioritized_tasks()
                if not tasks.empty:
                    # Improved table display
                    st.dataframe(
                        tasks,
                        column_config={
                            "title": "Task Name",
                            "due_date": st.column_config.DateColumn(
                                "Due Date",
                                format="YYYY-MM-DD"
                            ),
                            "priority": st.column_config.ProgressColumn(
                                "Priority Score",
                                help="Task priority (0-1 scale)",
                                format="%.2f",
                                min_value=0,
                                max_value=1,
                            )
                        },
                        hide_index=True,
                        height=400,
                        use_container_width=True
                    )
                else:
                    st.warning("No prioritized tasks available")
            except Exception as e:
                st.error(f"Failed to load tasks: {str(e)}")

        # Automation controls
        with st.expander("⚙️ Automation Settings"):
            cols = st.columns(3)
            with cols[0]:
                if st.button("🔄 Trigger Standups"):
                    with st.spinner("Initiating standups..."):
                        try:
                            from bots.slack_bot import trigger_daily_standup
                            if trigger_daily_standup():
                                st.success("Standups initiated successfully!")
                            else:
                                st.error("Failed to start standups")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            with cols[1]:
                if st.button("📊 Generate Report"):
                    with st.spinner("Compiling report..."):
                        try:
                            from report_generator import create_sprint_report
                            report = create_sprint_report()
                            st.download_button(
                                label="Download Report",
                                data=report,
                                file_name="sprint_report.md",
                                mime="text/markdown"
                            )
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            with cols[2]:
                if st.button("🧼 Cleanup Board"):
                    with st.spinner("Cleaning up..."):
                        try:
                            from bots.trello_integration import archive_old_cards
                            archived = archive_old_cards()
                            st.success(f"Archived {archived} old cards")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    
        st.markdown("""
        <style>
            .stDataFrame {
                max-height: 500px;
                overflow-y: auto;
            }
            .stPlotlyChart {
                margin-bottom: 2rem;
            }
            .stMetric {
                padding: 15px;
                background: #f8f9fa;
                border-radius: 10px;
            }
        </style>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Critical error: {str(e)}")
        logger.exception("Dashboard crash:")
        st.stop()

if __name__ == "__main__":
    main()