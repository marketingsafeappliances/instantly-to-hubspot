from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

import os
HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

@app.route('/api/instantly-webhook', methods=['POST'])
def instantly_webhook():
    data = request.get_json()
    email = data.get('email') or data.get('contact', {}).get('email')

    if not email:
        return jsonify({"error": "No email found"}), 400

    # Отправка в HubSpot
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "properties": {
            "email": email,
            "lead_source": "Instantly Webhook"
        }
    }
    r = requests.post("https://api.hubapi.com/crm/v3/objects/contacts", headers=headers, json=payload)
    return jsonify({"hubspot_response": r.json()}), r.status_code