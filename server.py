from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)  # обязательно именно 'app', иначе gunicorn не найдёт

HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

@app.route('/api/instantly-webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    #email = data.get("email")
    print("Incoming Webhook:", data)

    if not email:
        return jsonify({"error": "No email provided"}), 400

    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "properties": {
            "email": email
        }
    }

    r = requests.post("https://api.hubapi.com/crm/v3/objects/contacts", headers=headers, json=payload)
    return jsonify({"hubspot_response": r.json()}), r.status_code
