import os
import requests
import json
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

def send_teams_message(message: str, title: str = "Automated AI Workspace Update"):
    """
    Sends a message to a Microsoft Teams channel via a configured Incoming Webhook.
    """
    if not TEAMS_WEBHOOK_URL or TEAMS_WEBHOOK_URL == "YOUR_TEAMS_WEBHOOK_URL":
        print(f"WARNING: TEAMS_WEBHOOK_URL not configured in .env. Cannot send message to Teams. Message: {message}")
        return

    headers = {"Content-Type": "application/json"}
    
    # Using an Adaptive Card for richer messages
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": title,
                            "wrap": True,
                            "size": "Medium",
                            "weight": "Bolder"
                        },
                        {
                            "type": "TextBlock",
                            "text": message,
                            "wrap": True
                        }
                    ]
                }
            }
        ]
    }

    try:
        response = requests.post(TEAMS_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        print(f"Successfully sent message to Teams. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to send message to Teams. Reason: {e}")
        if e.response is not None:
            print(f"Teams API Response: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred while sending message to Teams: {e}")
