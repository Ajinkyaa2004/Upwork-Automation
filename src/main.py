import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from .poller import run_poller
from .telegram_bot import run_bot
from .upwork_client import upwork

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8000), HealthHandler)
    server.serve_forever()

def main():
    print("=== Upwork Agent Starting ===")
    try:
        token = upwork._get_access_token()
        print(f"Got access token (length {len(token)})")
        selector = upwork.get_company_selector()
        print("Company selector:", selector)
    except Exception as e:
        print(f"Initial Upwork auth test failed: {e}")

    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    poller_thread = threading.Thread(target=run_poller, daemon=True)
    poller_thread.start()

    run_bot()

if __name__ == "__main__":
    main()
