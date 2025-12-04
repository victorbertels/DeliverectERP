import time
from datetime import datetime, timedelta

# Token cache
_token_cache = {
    'token': None,
    'expires_at': None
}

def getToken():
    import requests
    import json
    import os
    
    # Check if we have a valid cached token
    if _token_cache['token'] and _token_cache['expires_at']:
        if datetime.now() < _token_cache['expires_at']:
            return _token_cache['token']
    
    # Try to get credentials from Streamlit secrets first (for Streamlit Cloud)
    try:
        import streamlit as st
        client_id = st.secrets.get("CLIENT_ID")
        client_secret = st.secrets.get("CLIENT_SECRET")
    except:
        # Fall back to .env file for local development
        from dotenv import load_dotenv
        load_dotenv()
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in Streamlit secrets or .env file")

    url = "https://api.deliverect.io/oauth/token"

    payload = json.dumps({
    "client_id": client_id,
    "client_secret": client_secret,
    "audience": "https://api.deliverect.com",
    "grant_type": "token"
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload).json()
    token = response["access_token"]
    
    # Cache the token (OAuth tokens typically expire in 1 hour, we'll refresh 5 minutes early)
    expires_in = response.get("expires_in", 3600)  # Default to 1 hour if not provided
    _token_cache['token'] = token
    _token_cache['expires_at'] = datetime.now() + timedelta(seconds=expires_in - 300)
    
    return token


def getHeaders():
    """Get headers with a fresh token"""
    return {
        'Authorization': f'Bearer {getToken()}'
    }