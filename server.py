from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

def get_contact_id_by_email(email):
    url = f"https://api.hubapi.com/crm/v3/objects/contacts?hapikey={HUBSPOT_TOKEN}&properties=email"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url + f"&filters=email%3D{email}", headers=headers)
    results = response.json().get("results", [])
    return results[0]["id"] if results else None

@app.route('/api/instantly-webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    event_type = data.get("event_type")
    email = data.get("lead_email")
    subject = data.get("email_subject", "Instantly event")
    body = data.get("email_text", "")
    timestamp = data.get("timestamp", datetime.utcnow().isoformat())

    if not email:
        return jsonify({"error": "No email provided"}), 400

    # Найти ID контакта по email
    contact_id = get_contact_id_by_email(email)
    if not contact_id:
        return jsonify({"error": "Contact not found in HubSpot"}), 404

    # Создание Email Engagement
    engagement_data = {
        "properties": {
            "hs_timestamp": timestamp,
            "hs_email_subject": subject,
            "hs_email_text": body,
            "hs_email_direction": "SENT",
        },
        "associations": [
            {
                "to": {"id": contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}]
            }
        ]
    }

    url = "https://api.hubapi.com/crm/v3/objects/emails"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(url, json=engagement_data, headers=headers)
    return jsonify({"hubspot_response": r.json()}), r.status_code
