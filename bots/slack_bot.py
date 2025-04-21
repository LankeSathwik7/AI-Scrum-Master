import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_bolt import App
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.socket_mode import SocketModeHandler
from core.config import (
    SLACK_BOT_TOKEN,
    SLACK_SIGNING_SECRET,
    SLACK_APP_TOKEN,
    SLACK_TEAM_CHANNEL
)
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

def handle_standup_reminder(channel):
    questions = (
        "🕗 *Daily Standup Reminder* 🕗\n"
        "1. What did you accomplish yesterday?\n"
        "2. What will you work on today?\n"
        "3. Any blockers or impediments?\n"
        "Please reply in thread!"
    )
    return app.client.chat_postMessage(
        channel=channel,
        text=questions
    )

@app.event("app_mention")
def handle_mentions(event, say):
    user_id = event["user"]
    say(
        channel=user_id,
        text="Hello! I'm your AI Scrum Master. Type `daily-standup` to start!"
    )

@app.message("daily-standup")
def trigger_daily_standup():
    from slack_sdk import WebClient
    from core.config import SLACK_BOT_TOKEN, SLACK_TEAM_CHANNEL
    
    client = WebClient(token=SLACK_BOT_TOKEN)
    
    try:
        # 1. Join channel first
        join_response = client.conversations_join(channel=SLACK_TEAM_CHANNEL)
        if not join_response["ok"]:
            raise Exception("Failed to join channel")
            
        # 2. Post message
        post = client.chat_postMessage(
            channel=SLACK_TEAM_CHANNEL,
            text="🕗 Daily Standup Reminder 🕗"
        )
        
        return True
    except Exception as e:
        logger.error(f"Standup failed: {str(e)}")
        return False

def join_channel(channel_id):
    try:
        response = app.client.conversations_join(channel=channel_id)
        if not response["ok"]:
            logger.warning(f"Already in channel {channel_id}")
    except SlackApiError as e:
        if e.response['error'] == 'already_in_channel':
            return
        raise

@app.event("message")
def handle_message(event, say):
    if event.get('subtype') == 'bot_message':
        return
    
    text = event.get('text', '').lower()
    channel = event.get('channel')
    user_id = event.get('user')
    
    # Join channel if not already member
    join_channel(channel)
    
    if 'daily-standup' in text:
        trigger_daily_standup(event, say)
    
    if detect_blocker(text):
        try:
            create_trello_card(text)
            say(
                thread_ts=event['ts'],
                channel=channel,
                text="🚨 Blocker detected! Created Trello card."
            )
        except Exception as e:
            logger.error(f"Block handler failed: {str(e)}")
            say(
                channel=channel,
                text="Failed to create Trello card. Please notify admin."
            )
    
if __name__ == "__main__":
    logger.info("Starting AI Scrum Master Bot")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()