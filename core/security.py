from functools import wraps
import os
import time
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Rate limiting (reqs/min)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

def encrypt_env():
    """Use python-dotenv-vault for production"""
    from dotenv_vault import load_dotenv
    load_dotenv()

def trello_oauth():
    """OAuth2 flow example"""
    from trello import TrelloClient
    client = TrelloClient(
        api_key=os.getenv('TRELLO_KEY'),
        api_secret=os.getenv('TRELLO_SECRET'),
        token=os.getenv('OAUTH_TOKEN'),
        token_secret=os.getenv('OAUTH_SECRET')
    )
    return client