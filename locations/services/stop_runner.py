import threading
from locations.services.stop_detector import run
import os

def start_stop_worker():
    if os.environ.get("RUN_MAIN") != "true":
        return

    thread = threading.Thread(target=run, daemon=True)
    thread.start()