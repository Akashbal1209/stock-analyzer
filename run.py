"""
Run this file to start the Stock Analyzer Pro web app.
Usage: python run.py
Then open: http://127.0.0.1:8080
"""
from app import app, SERVER_HOST, SERVER_PORT
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)
    webbrowser.open(f'http://127.0.0.1:{SERVER_PORT}')

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("   STOCK ANALYZER PRO - Starting...")
    print(f"   URL: http://127.0.0.1:{SERVER_PORT}")
    print("   Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False, threaded=True)
