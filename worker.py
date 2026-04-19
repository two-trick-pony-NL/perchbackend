# worker.py
import os
import django
import redis
import rq

os.getenv()

# Fix fork crash on macOS with Pillow, Requests, PyArrow, etc.
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

REDIS_URL = (
    f"redis://{os.getenv('REDIS_USER')}:"
    f"{os.getenv('REDIS_PASSWORD')}@"
    f"{os.getenv('REDIS_HOST')}:14988"
)
redis_conn = redis.from_url(REDIS_URL)




# Start the worker
worker = rq.Worker(['default'], connection=redis_conn)
worker.work()