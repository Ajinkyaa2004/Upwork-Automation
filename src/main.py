import threading
from .poller import run_poller
from .telegram_bot import run_bot
from .upwork_client import upwork

def main():
    print("=== Upwork Agent Starting ===")
    try:
        token = upwork._get_access_token()
        print(f"Got access token (length {len(token)})")
        selector = upwork.get_company_selector()
        print("Company selector:", selector)
    except Exception as e:
        print(f"Initial Upwork auth test failed: {e}")

    poller_thread = threading.Thread(target=run_poller, daemon=True)
    poller_thread.start()

    # Telegram webhook runs on port 8000 and also serves as the health check
    run_bot()

if __name__ == "__main__":
    main()
