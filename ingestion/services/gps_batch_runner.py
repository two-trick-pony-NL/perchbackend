import threading
from ingestion.services.gps_batch_ingestion import run
import os

def start_gps_ingestion():
    if os.environ.get("RUN_MAIN") != "true":
        return

    print("🔥 Starting GPS batch ingestion")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()