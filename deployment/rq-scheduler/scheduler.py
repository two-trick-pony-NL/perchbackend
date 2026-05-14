# scheduler.py
import subprocess
import time

while True:
    print("Starting RQ scheduler...")

    process = subprocess.run([
        "python",
        "manage.py",
        "rqscheduler",
        "--interval",
        "30"
    ])

    print(f"Scheduler exited with code {process.returncode}")
    time.sleep(5)