# Upwork Agent - Automated Message Drafting with Approval

A system that:
1. Polls Upwork for new messages
2. Fetches conversation context
3. Generates a draft reply with Groq LLM
4. Sends you a Telegram notification with Approve / Reject buttons
5. On Approve, sends the message via Upwork GraphQL API

## Setup

1. Copy `.env.example` to `.env` and fill in values
2. `pip install -r requirements.txt`
3. Run `python -m src.main`

## Required Environment Variables

See `.env.example`

## Current Limitations

- Uses Client Credentials grant (as configured on your key). Full messaging access may require Authorization Code flow + Messaging scopes.
- Telegram bot needs to be created and token + chat ID provided.
- Polling interval is configurable (default 2 minutes).
