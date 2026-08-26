"""
Local Launcher for Portfolio Stock Briefing
Starts a local lightweight HTTP server and opens the briefing dashboard in the default browser.
"""

import os
import sys
import webbrowser
import http.server
import socketserver
import threading
import time

PORT = 8089

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Disable caching for instant updates
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def start_server():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # Find open port
    port = PORT
    for p in range(PORT, PORT + 20):
        try:
            server = socketserver.TCPServer(("", p), CustomHandler)
            port = p
            break
        except OSError:
            continue

    url = f"http://localhost:{port}/index.html"
    print("=" * 60)
    print(f"  [Portfolio Stock Briefing] Local Server Started!")
    print(f"  URL: {url}")
    print("=" * 60)

    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()

if __name__ == "__main__":
    start_server()
