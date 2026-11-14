# Upwork Agent – Render Deployment

## Quick Deploy on Render

1. Push this folder to a GitHub repo (or use Render’s “Deploy from public Git” / manual upload).
2. Go to [render.com](https://render.com) → New → Background Worker.
3. Connect the repo.
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m src.main`
   - **Environment**: Python 3.11
5. Add Environment Variables:
   - `UPWORK_CLIENT_ID`
   - `UPWORK_CLIENT_SECRET`
   - `GROQ_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
6. Deploy.

The agent will start polling Upwork and send draft notifications to Telegram.
