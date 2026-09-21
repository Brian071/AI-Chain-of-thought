import sys
import os
import time
import webbrowser
import uvicorn

# Ensure project root in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    print("==================================================")
    print("  QwQ-32B CoT Offline AI Suite - Windows Launcher ")
    print("==================================================")
    print(f"Membuka browser lokal di {url}...")

    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    from app.main import app
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
