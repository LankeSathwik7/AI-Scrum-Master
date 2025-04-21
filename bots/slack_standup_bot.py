import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from core.config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN
from core.logger import configure_logger
from bots.trello_integration import create_trello_card

logger = configure_logger(__name__)

app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

def detect_blocker(text):
    blocker_phrases = ["blocked", "stuck", "waiting", "help", "issue"]
    return any(phrase in text.lower() for phrase in blocker_phrases)

@app.event("app_mention")
def handle_mentions(event, client):
    user_id = event["user"]
    client.chat_postMessage(
        channel=user_id,
        text="Hello! I'm your AI Scrum Master. Type `daily-standup` to start!"
    )

@app.message("daily-standup")
def trigger_daily_standup(message, say):
    try:
        # Send questions as a threaded response
        response = say(
            thread_ts=message['ts'],
            channel=message['channel'],
            text=(
                "🕗 *Daily Standup Reminder* 🕗\n"
                "1. What did you accomplish yesterday?\n"
                "2. What will you work on today?\n"
                "3. Any blockers or impediments?\n"
                "Please reply in thread!"
            )
        )
        
        # Also send a DM with the questions
        app.client.chat_postMessage(
            channel=message['user'],
            text=(
                "Here are your daily standup questions:\n"
                "1. What did you accomplish yesterday?\n"
                "2. What will you work on today?\n"
                "3. Any blockers or impediments?"
            )
        )
        
    except Exception as e:
        logger.error(f"Standup failed: {str(e)}")
        say(
            channel=message['channel'],
            text="Failed to start standup. Please try again."
        )

@app.event("message")
def handle_message(event, client):
    if event.get('subtype') == 'bot_message':
        return
    
    text = event.get('text', '')
    user_id = event.get('user')
    
    if detect_blocker(text):
        try:
            create_trello_card(text)
            client.chat_postMessage(
                channel=user_id,
                text="🚨 Blocker detected! Created Trello card."
            )
        except Exception as e:
            logger.error(f"Block handler failed: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting AI Scrum Master Bot")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()