# Flask IM Mockup — Messaging API Mock Server

A lightweight Flask server that mocks Telegram Bot API, Slack Web API, WhatsApp Cloud API, and Viber REST API for local development and testing. Zero configuration required — just spin it up with Docker or Python and start testing your messaging integrations.

## Features

- **Multi-platform mocking**: Telegram, Slack, WhatsApp, Viber
- **Real API request/response formats** — matches official API specs
- **Color-coded dashboard** — real-time message statistics with auto-refresh
- **Per-platform logging** — separate log files + combined view
- **Development-friendly** — accepts any credentials, logs everything, validates loosely
- **Standalone ready** — use standalone or integrate into larger projects
- **Zero dependencies** — Flask only

## Quick Start

### With Docker (Recommended)

```yaml
# docker-compose.yml
services:
  im-mockup:
    build: .
    restart: unless-stopped
    ports:
      - "8502:5000"
    volumes:
      - ./app:/app
```

Then:

```bash
docker compose up
# Browse: http://localhost:8502
```

### Standalone Python

```bash
pip install flask==3.0.2
python app/app.py
# Browse: http://localhost:5000
```

## Dashboard

Open `http://localhost:8502` to see:
- Real-time message counts per platform (color-coded)
- Links to individual platform logs
- Combined log view
- Auto-refreshing every 5 seconds

## Endpoints

### Telegram Bot API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/bot<token>/sendMessage` | Send a text message |
| POST | `/bot<token>/getMe` | Get bot info |
| POST | `/bot<token>/setWebhook` | Configure webhook |
| POST/GET | `/bot<token>/getUpdates` | Fetch updates |

**Request example:**
```bash
curl -X POST http://localhost:8502/botTEST_TOKEN/sendMessage \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 12345, "text": "Hello!"}'
```

### Slack Web API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat.postMessage` | Send a message to a channel |
| GET/POST | `/api/auth.test` | Test authentication |

**Request example:**
```bash
curl -X POST http://localhost:8502/api/chat.postMessage \
  -H "Authorization: Bearer xoxb-test" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "channel=C123&text=Hello"
```

### WhatsApp Cloud API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v19.0/<phone_id>/messages` | Send a message |
| GET | `/v19.0/<phone_id>/messages` | Webhook verification challenge |

**Request example:**
```bash
curl -X POST http://localhost:8502/v19.0/123456/messages \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "+1234567890",
    "type": "text",
    "text": {"body": "Hello!"}
  }'
```

### Viber REST API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/pa/send_message` | Send a message |
| POST | `/pa/set_webhook` | Configure webhook |

**Request example:**
```bash
curl -X POST http://localhost:8502/pa/send_message \
  -H "X-Viber-Auth-Token: test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": "user123",
    "type": "text",
    "text": "Hello!"
  }'
```

## Integration with Your App

Configure your app to use the mock server's base URL in development:

```python
# Example: Python SDK using configurable base URL
import os

MESSAGING_TELEGRAM_API_URL = os.getenv(
    'MESSAGING_TELEGRAM_API_URL',
    'http://localhost:8502'  # Local mock (dev)
)
MESSAGING_SLACK_API_URL = os.getenv(
    'MESSAGING_SLACK_API_URL',
    'http://localhost:8502'  # Local mock (dev)
)

# Production uses real APIs:
# MESSAGING_TELEGRAM_API_URL = 'https://api.telegram.org'
# MESSAGING_SLACK_API_URL = 'https://slack.com'
```

Then make requests to:
```
http://localhost:8502/bot{TOKEN}/sendMessage
http://localhost:8502/api/chat.postMessage
# etc.
```

## Logging

All requests are logged in JSON format with ISO timestamps.

**Log locations:**
- `/logs/telegram.log` — Telegram requests
- `/logs/slack.log` — Slack requests
- `/logs/whatsapp.log` — WhatsApp requests
- `/logs/viber.log` — Viber requests
- `/logs/all.log` — Combined log of all requests

**Log format:**
```
[2026-04-06T00:49:14.899927]
{
  "platform": "telegram",
  "method": "sendMessage",
  "token": "test_token",
  "request": {
    "chat_id": 12345,
    "text": "Hello",
    ...
  }
}
```

View logs via the dashboard at `/logs` or `/logs/<filename>`.

## Features

### Token Handling
- Accepts **any token** — no validation performed
- Tokens are partially masked in logs (`token[:20] + "..."`)
- Useful for testing without real credentials

### Response Format
- Responses match official API specs exactly
- Messages auto-increment with unique IDs
- Timestamps generated from system time

### Error Handling
- Missing authorization headers → returns proper error codes
- Slack: `{"ok": false, "error": "not_authed"}`
- Viber: `{"status": 1, "status_message": "Invalid auth token"}`

### Warnings
- WhatsApp free-form text (non-template) → logs warning about 24h window requirement

## Development

### Run tests locally
```bash
python -m pytest tests/
```

### Rebuild Docker image
```bash
docker compose build flask-im-mockup
```

### Clean logs
```bash
rm -rf app/logs/
```

## Use Cases

- **Local development** — test messaging integrations without calling real APIs
- **CI/CD testing** — mock external services in automated tests
- **Integration testing** — verify your app's request/response handling
- **API contract verification** — ensure your code matches expected formats
- **Dashboard verification** — test logging and monitoring

## Built For

Created as a companion debug tool for OpenEMIS POCOR-9623 (Instant Messaging feature).  
Useful for anyone building messaging integrations with multiple platforms.

Learn more: https://www.openemis.org

## License

MIT — See LICENSE file

## Contributing

Issues and pull requests welcome on [GitHub](https://github.com/tixuz/flask-im-mockup).
