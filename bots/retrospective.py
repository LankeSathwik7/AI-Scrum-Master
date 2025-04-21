import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from transformers import pipeline
import torch
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from core.config import SLACK_BOT_TOKEN, SLACK_RETRO_CHANNEL
from core.logger import configure_logger

logger = configure_logger(__name__)

class RetrospectiveAnalyzer:
    def __init__(self):
        self.slack_client = WebClient(token=SLACK_BOT_TOKEN)
        self.sentiment_analyzer = self._init_sentiment_analyzer()
        logger.info(f"Device set to use {'cuda' if torch.cuda.is_available() else 'cpu'}")

    def _init_sentiment_analyzer(self):
        try:
            device = 0 if torch.cuda.is_available() else -1
            return pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=device,
                top_k=None,
                max_length=128,
                truncation=True,
                batch_size=8
            )
        except Exception as e:
            logger.error(f"Sentiment analyzer init failed: {str(e)}")
            return None

    def _get_or_create_retro_channel(self):
        try:
            response = self.slack_client.conversations_list(
                types="public_channel",
                exclude_archived=True
            )
            
            for channel in response.get('channels', []):
                if channel['name'].lower() == SLACK_RETRO_CHANNEL.lower():
                    return channel['id']

            logger.info(f"Creating new retrospective channel: {SLACK_RETRO_CHANNEL}")
            try:
                new_channel = self.slack_client.conversations_create(
                    name=SLACK_RETRO_CHANNEL,
                    is_private=False
                )
                return new_channel['channel']['id']
            except SlackApiError as e:
                if e.response['error'] == 'name_taken':
                    logger.warning(f"Channel {SLACK_RETRO_CHANNEL} exists but wasn't found initially")
                    return self._find_existing_channel()
                raise

        except SlackApiError as e:
            logger.error(f"Slack API Error: {e.response['error']}")
            if e.response['error'] == 'missing_scope':
                logger.critical("Missing required OAuth scope! Add 'channels:manage' scope in Slack app settings")
            return None

    def _find_existing_channel(self):
        try:
            response = self.slack_client.conversations_list(
                types="public_channel",
                exclude_archived=True,
                limit=1000
            )
            for channel in response.get('channels', []):
                if channel['name'].lower() == SLACK_RETRO_CHANNEL.lower():
                    return channel['id']
            return None
        except SlackApiError as e:
            logger.error(f"Channel search failed: {e.response['error']}")
            return None

    def analyze_sentiment(self):
        if not self.sentiment_analyzer:
            return {"error": "Sentiment analyzer not initialized"}
            
        try:
            channel_id = self._get_or_create_retro_channel()
            if not channel_id:
                return {"error": "Failed to access retrospective channel"}
            
            one_week_ago = datetime.now() - timedelta(days=7)
            messages = []
            cursor = None
            
            # Paginate through all messages
            for _ in range(10):  # Max 1000 messages
                response = self.slack_client.conversations_history(
                    channel=channel_id,
                    oldest=one_week_ago.timestamp(),
                    limit=200,
                    cursor=cursor
                )
                messages.extend(response.get('messages', []))
                cursor = response.get('response_metadata', {}).get('next_cursor')
                if not cursor:
                    break

            if not messages:
                return {"error": "No messages in retrospective channel"}
            
            valid_messages = [
                self._clean_message(msg.get('text', '')) 
                for msg in messages 
                if msg.get('text') and not msg.get('bot_id')
            ]

            logger.debug(f"Messages to analyze: {len(valid_messages)}")
            
            if not valid_messages:
                return {"error": "No analyzable text found"}

            # Batch processing with error handling
            batch_size = 8
            results = []
            for i in range(0, len(valid_messages), batch_size):
                try:
                    batch = valid_messages[i:i+batch_size]
                    results.extend(self.sentiment_analyzer(batch))
                except Exception as e:
                    logger.error(f"Batch {i//batch_size} failed: {str(e)}")
                    results.extend([[]] * len(batch))  # Add empty results for failed batch

            sentiment_counts = {
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }

            for i, message_results in enumerate(results):
                if not message_results:  # Skip failed analyses
                    continue
                    
                top_score = max(message_results, key=lambda x: x['score'])
                
                # DEBUG: Log raw classification
                logger.debug(f"Message: '{valid_messages[i]}'")
                logger.debug(f"Top classification: {top_score['label']} ({top_score['score']:.2f})")
                
                if top_score['score'] > 0.6:  # Adjusted confidence threshold
                    if top_score['label'] == 'positive':
                        sentiment_counts["positive"] += 1
                    elif top_score['label'] == 'negative':
                        sentiment_counts["negative"] += 1
                    else:
                        sentiment_counts["neutral"] += 1
                else:
                    sentiment_counts["neutral"] += 1

            return {
                **sentiment_counts,
                "samples": len(valid_messages)
            }
            
        except SlackApiError as e:
            logger.error(f"Slack API Error: {e.response['error']}")
            return {"error": "Slack API connection failed"}
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {"error": "Technical failure in analysis"}

    def _clean_message(self, text):
        """Remove timestamps, metadata, and formatting from messages"""
        # Remove Slack mentions and formatting
        text = re.sub(r'<[^>]+>', '', text)  # Remove all Slack markup
        # Remove any timestamps like "11:35 PM"
        text = re.sub(r'\b\d{1,2}:\d{2}\s?(?:AM|PM)?\b', '', text)
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove special characters except basic punctuation
        return re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text).strip()
    
if __name__ == "__main__":
    analyzer = RetrospectiveAnalyzer()
    print(analyzer.analyze_sentiment())