import requests
import json
import os.path
import imaplib
import email
import feedparser # pyright: ignore[reportMissingImports]
from email.header import decode_header
from datetime import datetime
from langchain_core.tools import tool

# Google API Libraries
from google.auth.transport.requests import Request # pyright: ignore[reportMissingImports]
from google.oauth2.credentials import Credentials # pyright: ignore[reportMissingImports] 
from google_auth_oauthlib.flow import InstalledAppFlow # pyright: ignore[reportMissingImports]
from googleapiclient.discovery import build # pyright: ignore[reportMissingImports]

# Local hardware bridge import
# In production, 'bridge' replaces the French 'pont'

from .domotics import bridge # pyright: ignore[reportMissingImports]

# --- NEWS SERVICES CONFIGURATION ---
# Anonymized dictionary of RSS feeds
NEWS_FEEDS = {
    "MAIN_STREAM_1_POLITICS": "https://www.lemonde.fr/politique/rss_full.xml",
    "MAIN_STREAM_1_INTL": "https://www.lemonde.fr/en/france/rss_full.xml",
    "MAIN_STREAM_2_POLITICS": "https://www.lefigaro.fr/rss/figaro_politique.xml",
    "PUBLIC_SERVICE_POLITICS": "https://www.franceinfo.fr/politique.rss",
    "PUBLIC_SERVICE_INTL": "https://www.franceinfo.fr/monde.rss",
    "PUBLIC_SERVICE_ECO": "https://www.franceinfo.fr/economie.rss",
    "INSTITUTIONAL_SENATE": "https://www.senat.fr/rss/rapports.xml"
}

# --- GOOGLE AUTH CONFIGURATION ---
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly', 
    'https://www.googleapis.com/auth/gmail.readonly'
]

def get_google_service(service_name, version):
    """Anonymized helper to handle Google OAuth2 authentication."""
    creds = None
    # Token and credentials files should be in .gitignore
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build(service_name, version, credentials=creds)

# --- NEWS TOOLS ---

@tool
def compile_news_reports(sources: list = None):
    """
    Fetches and aggregates news headlines from multiple RSS feeds.
    If no sources are provided, defaults to a standard selection.
    """
    if not sources or not isinstance(sources, list) or len(sources) == 0:
        sources = ["PUBLIC_SERVICE_POLITICS", "MAIN_STREAM_1_POLITICS", "MAIN_STREAM_2_POLITICS"]
    
    compilation = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for key in sources:
        if not key or not isinstance(key, str): continue
        url = NEWS_FEEDS.get(key.upper())
        if not url: continue
        
        try:
            # agent=headers mimics a browser to bypass institutional bot filters
            feed = feedparser.parse(url, agent=headers["User-Agent"])
            
            if feed.entries:
                for entry in feed.entries[:3]: 
                    title = entry.title.replace('\n', ' ').strip()
                    compilation.append(f"[{key.upper()}] : {title}")
        except Exception as e:
            print(f"Error scanning {key}: {e}")
            
    if not compilation:
        return "ERROR: No news headlines could be retrieved from the selected feeds."
        
    return "\n".join(compilation)

# --- PERSONAL ASSISTANT TOOLS (GMAIL & CALENDAR) ---

@tool
def get_daily_calendar():
    """Retrieves today's calendar events from the primary Google Calendar."""
    try:
        service = get_google_service('calendar', 'v3')
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=10, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        
        if not events:
            return "No events found for today."
        
        summary = "Today's Schedule: "
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary += f"- {event['summary']} at {start} "
        return summary
    except Exception as e:
        return f"Calendar Error: {str(e)}"

@tool
def summarize_recent_emails():
    """Fetches and summarizes the last 5 emails from the Gmail inbox."""
    try:
        service = get_google_service('gmail', 'v1')
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=5).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return "No new emails found."
        
        summaries = "Recent Emails: "
        for msg in messages:
            m = service.users().messages().get(userId='me', id=msg['id']).execute()
            snippet = m['snippet']
            headers = m['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "No Subject")
            summaries += f" [Subject: {subject} | Snippet: {snippet}] "
        return summaries
    except Exception as e:
        return f"Gmail Error: {str(e)}"

# --- SMART HOME TOOLS ---

@tool
def control_lights(location: str, action: str):
    """Controls smart lights. Location: 'LIVING_ROOM' or 'BEDROOM'. Action: 'ON' or 'OFF'."""
    # Mapping anonymized locations to hardware IDs
    light_id = 'Hue color lamp 1' if location.upper() == "LIVING_ROOM" else 'Hue color lamp 2'
    bridge.set_light(light_id, 'on', (action.upper() == "ON"))
    return f"{location} light set to {action}."

# --- WEATHER TOOLS ---

@tool
def get_weather_forecast():
    """Fetches current weather and daily highs/lows for the configured coordinates."""
    # Coordinates should ideally be moved to an .env file
    lat = os.getenv("HOME_LAT", "45.1839")
    lon = os.getenv("HOME_LON", "5.7089")
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    
    try:
        response = requests.get(url)
        data = response.json()
        result = {
            "current": data['current_weather']['temperature'],
            "min": data['daily']['temperature_2m_min'][0],
            "max": data['daily']['temperature_2m_max'][0]
        }
        return json.dumps(result)
    except Exception as e:
        return f"Weather Service Error: {str(e)}"