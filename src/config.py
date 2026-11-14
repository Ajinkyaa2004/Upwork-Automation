import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    UPWORK_CLIENT_ID = os.getenv("UPWORK_CLIENT_ID")
    UPWORK_CLIENT_SECRET = os.getenv("UPWORK_CLIENT_SECRET")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # changed to a widely available model
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

config = Config()
