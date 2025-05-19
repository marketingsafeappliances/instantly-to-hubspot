from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)
HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

def log_note_to_hubspot(email, note_body, timestamp):
    # Поиск контакта
    search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    search_payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }],
        "properties": ["email"],
        "limit": 1
    }

    r = requests.post(search_url, headers=headers, json=search_payload)
    result = r.json()

    if not result.get("results"):
        return {"error": f"Contact with email {email} not found"}, 404

    contact_id = result["results"][0]["id"]

    # Создание Note
    engagement_url = "https://api.hubapi.com/engagements/v1/engagements"
    note_payload = {
        "engagement": {
            "active": True,
            "type": "NOTE",
            "timestamp": timestamp
        },
        "associations": {
            "contactIds": [contact_id]
        },
        "metadata": {
            "body": note_body
        }
    }

    response = requests.post(engagement_url, headers=headers, json=note_payload)
    return response.json(), response.status_code

@app.route('/api/instantly-webhook', methods=['POST'])
def instantly_webhook():
    data = request.get_json()

    # Основные поля
    email = data.get("lead_email")
    event = data.get("event_type")
    campaign = data.get("campaign_name")
    timestamp = data.get("timestamp")

    # Без email — ничего не делаем
    if not email:
        return jsonify({"error": "lead_email is required"}), 400

    # Собираем тело заметки
    note_lines = [
        f"📌 Event: `{event}`",
        f"📢 Campaign: {campaign}",
        f"🕒 Time: {timestamp}"
    ]

    # Добавляем step/variant, если есть
    if data.get("step"): note_lines.append(f"➡️ Step: {data.get('step')}")
    if data.get("variant"): note_lines.append(f"🧪 Variant: {data.get('variant')}")
    if data.get("is_first") is not None: note_lines.append(f"🆕 First occurrence: {data.get('is_first')}")

    # Email content
    if data.get("email_subject"): note_lines.append(f"✉️ Subject: {data.get('email_subject')}")
    if data.get("email_text"): note_lines.append(f"📝 Text: {data.get('email_text')[:200]}...")

    # Reply content
    if data.get("reply_subject"): note_lines.append(f"↩️ Reply subject: {data.get('reply_subject')}")
    if data.get("reply_text_snippet"): note_lines.append(f"📎 Snippet: {data.get('reply_text_snippet')}")
    if data.get("reply_text"): note_lines.append(f"📨 Reply: {data.get('reply_text')[:500]}...")
    if data.get("unibox_url"): note_lines.append(f"🔗 View in Unibox: {data.get('unibox_url')}")

    note_body = "\n".join(note_lines)

    # Записываем в HubSpot
    result, status = log_note_to_hubspot(email, note_body, timestamp)
    return jsonify({"hubspot_response": result}), status
