import os
from dotenv import load_dotenv

load_dotenv()

# Slack Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_TEAM_CHANNEL = os.getenv("SLACK_TEAM_CHANNEL", "general")
SLACK_RETRO_CHANNEL = os.getenv("SLACK_RETRO_CHANNEL", "retrospective")

# Trello Configuration
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")
TRELLO_LIST_ID = os.getenv("TRELLO_LIST_ID")
TRELLO_ARCHIVE_LIST = os.getenv("TRELLO_ARCHIVE_LIST", "")

# Application Settings
RISK_THRESHOLD = int(os.getenv("RISK_THRESHOLD", 10))
POSITIVE_THRESHOLD = float(os.getenv("POSITIVE_THRESHOLD", 0.25))
CRITICAL_THRESHOLD = float(os.getenv("CRITICAL_THRESHOLD", 0.15))