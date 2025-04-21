import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
from datetime import datetime, timedelta
from core.config import *
from core.logger import configure_logger

logger = configure_logger(__name__)

def validate_trello_response(response):
    if response.status_code != 200:
        raise TrelloAPIError(f"API Error {response.status_code}: {response.text}")
    return response.json()

class TrelloAPIError(Exception):
    pass

def fetch_trello_data():
    try:
        url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/cards"
        params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN,
            "checklists": "all",
            "fields": "name,desc,dateLastActivity,checklists,closed,labels,idList"
        }
        return validate_trello_response(requests.get(url, params=params))
    except Exception as e:
        logger.error(f"Trello fetch failed: {str(e)}")
        return []

def create_trello_card(blocker_text):
    try:
        url = "https://api.trello.com/1/cards"
        query = {
            'key': TRELLO_API_KEY,
            'token': TRELLO_TOKEN,
            'idList': TRELLO_LIST_ID,
            'name': f"Blocker: {blocker_text[:50]}",
            'desc': f"{blocker_text}\n\nBoard ID: {TRELLO_BOARD_ID}", 
            'pos': 'top'
        }
        return validate_trello_response(requests.post(url, params=query))
    except TrelloAPIError as e:
        logger.error(f"Trello API Error: {str(e)}")
        raise

def archive_old_cards(days=14):
    try:
        archive_list_id = TRELLO_ARCHIVE_LIST or get_archive_list()
        
        archived = 0
        cutoff = datetime.now().replace(tzinfo=None) - timedelta(days=days)
        for card in fetch_trello_data():
            last_active = pd.to_datetime(card['dateLastActivity']).tz_localize(None)
            if last_active < cutoff:
                url = f"https://api.trello.com/1/cards/{card['id']}"
                params = {
                    'key': TRELLO_API_KEY,
                    'token': TRELLO_TOKEN,
                    'closed': 'true',
                    'idList': archive_list_id
                }
                requests.put(url, params=params)
                archived += 1
        return archived
    except Exception as e:
        logger.error(f"Archive failed: {str(e)}")
        return 0

def get_archive_list():
    try:
        url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists"
        params = {'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN}
        lists = validate_trello_response(requests.get(url, params=params))
        
        for lst in lists:
            if 'archive' in lst['name'].lower():
                return lst['id']
            
        # Create new archive list
        new_list = validate_trello_response(requests.post(
            "https://api.trello.com/1/lists",
            params={
                'key': TRELLO_API_KEY,
                'token': TRELLO_TOKEN,
                'name': 'Archive',
                'idBoard': TRELLO_BOARD_ID,
                'pos': 'bottom'
            }
        ))
        return new_list['id']
    except Exception as e:
        logger.error(f"Archive list creation failed: {str(e)}")
        raise