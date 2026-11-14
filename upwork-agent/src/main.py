import threading
from .poller import run_poller
from .telegram_bot import run_bot
from .upwork_client import upwork

def main():
    print("=== Upwork Agent Starting ===")

    # Quick test of token + company selector
    try:
        token = upwork._get_access_token()
        print(f"Got access token (length {len(token)})")
        selector = upwork.get_company_selector()
        print("Company selector:", selector)
    except Exception as e:
        print(f"Initial Upwork auth test failed: {e}")
        print("Continuing anyway — check scopes and grant type.")

    # Start poller in background thread
    poller_thread = threading.Thread(target=run_poller, daemon=True)
    poller_thread.start()

    # Run Telegram bot in main thread (blocking)
    run_bot()

if __name__ == "__main__":
    main()
