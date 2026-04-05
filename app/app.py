import json
import os
import re
import time
import random
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
app.url_map.strict_slashes = False
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Message counters for mock responses
message_counters = {
    "telegram": 1000,
    "slack": 1000,
    "whatsapp": 1000,
    "viber": 1000
}

# --- Utility: Sanitize values for safe logging ---
def sanitize_value(value):
    if isinstance(value, str):
        value = re.sub(r'[\x00-\x1f\x7f]', '', value)
        return value.replace('\r', '\\r').replace('\n', '\\n')
    return value

def sanitize_dict(data):
    if isinstance(data, dict):
        return {k: sanitize_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_dict(item) for item in data]
    else:
        return sanitize_value(data)

# --- File logger (matches flask-webhooks pattern) ---
def log_to_file(filename, data):
    full_path = os.path.join(LOG_DIR, filename)
    with open(full_path, "a") as f:
        f.write(f"[{datetime.now().isoformat()}]\n")
        f.write(json.dumps(sanitize_dict(data), indent=2, ensure_ascii=False))
        f.write("\n\n")

def log_all_platforms(data):
    """Log to all.log"""
    log_to_file("all.log", data)

# --- Dashboard HTML ---
@app.route('/')
def index():
    logs = {}
    for platform in ["telegram", "slack", "whatsapp", "viber"]:
        log_file = os.path.join(LOG_DIR, f"{platform}.log")
        if os.path.isfile(log_file):
            with open(log_file, 'r') as f:
                content = f.read()
            logs[platform] = content

    # Count entries and get last 30
    entries = []
    for platform in ["telegram", "slack", "whatsapp", "viber"]:
        log_file = os.path.join(LOG_DIR, f"{platform}.log")
        if os.path.isfile(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
            # Parse ISO timestamps and count
            timestamps = [line.strip() for line in lines if line.startswith('[')]
            color = {"telegram": "blue", "slack": "orange", "whatsapp": "green", "viber": "purple"}[platform]
            entries.append({
                "platform": platform,
                "count": len(timestamps),
                "color": color
            })

    # Build HTML
    stats_html = ""
    for entry in entries:
        stats_html += f'<p style="color: {entry["color"]}"><strong>{entry["platform"].capitalize()}</strong>: {entry["count"]} messages</p>'

    logs_html = ""
    for platform in ["telegram", "slack", "whatsapp", "viber"]:
        logs_html += f'<li><a href="/logs/{platform}.log" target="_blank">{platform.capitalize()} Log</a></li>'
    logs_html += '<li><a href="/logs/all.log" target="_blank">Combined Log</a></li>'

    return f'''
    <html>
    <head>
        <title>IM Mockup Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 2em; background: #f5f5f5; }}
            h1 {{ color: #333; }}
            .stats {{ background: white; padding: 1em; border-radius: 5px; margin: 1em 0; }}
            .stats p {{ margin: 0.5em 0; }}
            .links {{ background: white; padding: 1em; border-radius: 5px; }}
            .links ul {{ list-style: none; padding: 0; }}
            .links li {{ margin: 0.5em 0; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>📱 Instant Messaging Mock Server</h1>
        <p>Real-time dashboard for Telegram, Slack, WhatsApp, and Viber API mockups.</p>
        <div class="stats">
            <h2>Message Statistics</h2>
            {stats_html}
            <p style="font-size: 0.9em; color: #666;">Auto-refreshing every 5 seconds</p>
        </div>
        <div class="links">
            <h2>Log Files</h2>
            <ul>
                {logs_html}
            </ul>
        </div>
    </body>
    </html>
    '''

@app.route('/logs')
def list_logs():
    files = [f for f in os.listdir(LOG_DIR) if os.path.isfile(os.path.join(LOG_DIR, f))]
    links = '\n'.join([f'<li><a href="/logs/{f}" target="_blank">{f}</a></li>' for f in sorted(files)])
    return f'''
    <html>
    <head><title>IM Mockup Logs</title></head>
    <body>
        <h1>📁 Logs</h1>
        <p>Click on a log file to view its contents:</p>
        <ul>{links}</ul>
        <p><a href="/">← Back to Dashboard</a></p>
    </body>
    </html>
    '''

@app.route('/logs/<path:filename>')
def view_log_file(filename):
    full_path = os.path.join(LOG_DIR, filename)
    if not os.path.isfile(full_path):
        return "Log file not found", 404

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    escaped = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    return f'''
    <html>
    <head>
        <title>{filename} - Log Viewer</title>
        <style>
            body {{ font-family: monospace; white-space: pre-wrap; background: #f9f9f9; padding: 1em; }}
            a {{ display: block; margin-bottom: 1em; }}
        </style>
    </head>
    <body>
        <a href="/logs">← Back to Logs List</a>
        <h2>{filename}</h2>
        <pre>{escaped}</pre>
    </body>
    </html>
    '''

# ============================================================================
# TELEGRAM BOT API MOCKS
# ============================================================================

@app.route('/bot<token>/sendMessage', methods=['POST'])
def telegram_send_message(token):
    data = request.get_json(silent=True) or {}

    chat_id = data.get('chat_id')
    text = data.get('text')
    parse_mode = data.get('parse_mode')

    log_entry = {
        "platform": "telegram",
        "method": "sendMessage",
        "token": token,
        "request": {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
    }

    log_to_file("telegram.log", log_entry)
    log_all_platforms(log_entry)

    message_counters["telegram"] += 1
    response = {
        "ok": True,
        "result": {
            "message_id": message_counters["telegram"],
            "chat": {
                "id": chat_id,
                "type": "private"
            },
            "text": text,
            "date": int(time.time())
        }
    }
    return jsonify(response), 200

@app.route('/bot<token>/getMe', methods=['POST'])
def telegram_get_me(token):
    log_entry = {
        "platform": "telegram",
        "method": "getMe",
        "token": token
    }

    log_to_file("telegram.log", log_entry)
    log_all_platforms(log_entry)

    response = {
        "ok": True,
        "result": {
            "id": 123456789,
            "is_bot": True,
            "first_name": "OpenEMIS Test Bot",
            "username": "openemis_test_bot"
        }
    }
    return jsonify(response), 200

@app.route('/bot<token>/setWebhook', methods=['POST'])
def telegram_set_webhook(token):
    data = request.get_json(silent=True) or {}

    url = data.get('url')
    secret_token = data.get('secret_token')

    log_entry = {
        "platform": "telegram",
        "method": "setWebhook",
        "token": token,
        "request": {
            "url": url,
            "secret_token": secret_token
        }
    }

    log_to_file("telegram.log", log_entry)
    log_all_platforms(log_entry)

    response = {
        "ok": True,
        "result": True,
        "description": "Webhook was set"
    }
    return jsonify(response), 200

@app.route('/bot<token>/getUpdates', methods=['POST', 'GET'])
def telegram_get_updates(token):
    log_entry = {
        "platform": "telegram",
        "method": "getUpdates",
        "token": token
    }

    log_to_file("telegram.log", log_entry)
    log_all_platforms(log_entry)

    response = {
        "ok": True,
        "result": []
    }
    return jsonify(response), 200

# ============================================================================
# SLACK WEB API MOCKS
# ============================================================================

@app.route('/api/chat.postMessage', methods=['POST'])
def slack_post_message():
    auth_header = request.headers.get('Authorization', '')

    if not auth_header or not auth_header.startswith('Bearer '):
        log_entry = {
            "platform": "slack",
            "method": "chat.postMessage",
            "status": "error",
            "error": "not_authed",
            "message": "Missing Authorization header"
        }
        log_to_file("slack.log", log_entry)
        log_all_platforms(log_entry)
        return jsonify({"ok": False, "error": "not_authed"}), 401

    token = auth_header.split(' ')[1]

    # Get channel and text from form data or JSON
    channel = request.form.get('channel') or (request.get_json(silent=True) or {}).get('channel')
    text = request.form.get('text') or (request.get_json(silent=True) or {}).get('text')
    blocks = request.form.get('blocks') or (request.get_json(silent=True) or {}).get('blocks')

    log_entry = {
        "platform": "slack",
        "method": "chat.postMessage",
        "token": token[:20] + "...",  # Sanitize token in log
        "request": {
            "channel": channel,
            "text": text,
            "blocks": blocks
        }
    }

    log_to_file("slack.log", log_entry)
    log_all_platforms(log_entry)

    message_counters["slack"] += 1
    ts = f"{int(time.time())}.{message_counters['slack']:06d}"

    response = {
        "ok": True,
        "channel": channel,
        "ts": ts,
        "message": {
            "text": text,
            "type": "message",
            "user": "U123456",
            "ts": ts
        }
    }
    return jsonify(response), 200

@app.route('/api/auth.test', methods=['GET', 'POST'])
def slack_auth_test():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    log_entry = {
        "platform": "slack",
        "method": "auth.test",
        "token": token[:20] + "..." if token else None
    }

    log_to_file("slack.log", log_entry)
    log_all_platforms(log_entry)

    response = {
        "ok": True,
        "url": "https://openemis.slack.com/",
        "team": "OpenEMIS",
        "user": "bot",
        "team_id": "T0001",
        "user_id": "U0001"
    }
    return jsonify(response), 200

# ============================================================================
# WHATSAPP CLOUD API MOCKS
# ============================================================================

@app.route('/v19.0/<phone_id>/messages', methods=['POST', 'GET'])
def whatsapp_messages(phone_id):
    # Webhook verification challenge (GET request)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        log_entry = {
            "platform": "whatsapp",
            "method": "messages (webhook verification)",
            "phone_id": phone_id,
            "mode": mode,
            "verify_token": verify_token
        }

        log_to_file("whatsapp.log", log_entry)
        log_all_platforms(log_entry)

        return challenge if challenge else "Challenge failed", 200

    # POST: Send message
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

    data = request.get_json(silent=True) or {}

    msg_type = data.get('type')
    to = data.get('to')

    log_entry = {
        "platform": "whatsapp",
        "method": "messages",
        "phone_id": phone_id,
        "token": token[:20] + "..." if token else None,
        "request": {
            "type": msg_type,
            "to": to,
            "messaging_product": data.get('messaging_product')
        }
    }

    # Warn if using free-form text (not template)
    if msg_type == 'text':
        log_entry["warning"] = "FREE_FORM text message — will fail in production without 24h window"

    log_to_file("whatsapp.log", log_entry)
    log_all_platforms(log_entry)

    message_counters["whatsapp"] += 1
    response = {
        "messaging_product": "whatsapp",
        "contacts": [
            {"input": to, "wa_id": to}
        ],
        "messages": [
            {"id": f"wamid.mock_{message_counters['whatsapp']}"}
        ]
    }
    return jsonify(response), 200

# ============================================================================
# VIBER REST API MOCKS
# ============================================================================

@app.route('/pa/send_message', methods=['POST'])
def viber_send_message():
    auth_token = request.headers.get('X-Viber-Auth-Token')

    if not auth_token:
        log_entry = {
            "platform": "viber",
            "method": "send_message",
            "status": "error",
            "error": "Invalid auth token"
        }
        log_to_file("viber.log", log_entry)
        log_all_platforms(log_entry)
        return jsonify({"status": 1, "status_message": "Invalid auth token"}), 401

    data = request.get_json(silent=True) or {}

    receiver = data.get('receiver')
    msg_type = data.get('type')
    text = data.get('text')
    sender = data.get('sender', {})

    log_entry = {
        "platform": "viber",
        "method": "send_message",
        "token": auth_token[:20] + "...",
        "request": {
            "receiver": receiver,
            "type": msg_type,
            "text": text,
            "sender": sender
        }
    }

    log_to_file("viber.log", log_entry)
    log_all_platforms(log_entry)

    message_counters["viber"] += 1
    response = {
        "status": 0,
        "status_message": "ok",
        "message_token": random.randint(1000000, 9999999)
    }
    return jsonify(response), 200

@app.route('/pa/set_webhook', methods=['POST'])
def viber_set_webhook():
    auth_token = request.headers.get('X-Viber-Auth-Token')
    data = request.get_json(silent=True) or {}

    url = data.get('url')
    event_types = data.get('event_types', [])

    log_entry = {
        "platform": "viber",
        "method": "set_webhook",
        "token": auth_token[:20] + "..." if auth_token else None,
        "request": {
            "url": url,
            "event_types": event_types
        }
    }

    log_to_file("viber.log", log_entry)
    log_all_platforms(log_entry)

    response = {
        "status": 0,
        "status_message": "ok",
        "event_types": ["delivered", "seen"]
    }
    return jsonify(response), 200

# --- Start server ---
if __name__ == '__main__':
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
    app.run(host='0.0.0.0', port=5000)
