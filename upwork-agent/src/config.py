import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    UPWORK_CLIENT_ID = os.getenv("UPWORK_CLIENT_ID")
    UPWORK_CLIENT_SECRET = os.getenv("UPWORK_CLIENT_SECRET")
    UPWORK_TENANT_ID = os.getenv("UPWORK_TENANT_ID") or None

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "120"))
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/agent.db")

config = Config()
