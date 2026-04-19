import os
import django
import redis
import rq
from dotenv import load_dotenv

# load .env file
load_dotenv("core/.env")

# macOS fork safety fix
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

REDIS_URL = (
    f"redis://{os.getenv('REDIS_USER')}:"
    f"{os.getenv('REDIS_PASSWORD')}@"
    f"{os.getenv('REDIS_HOST')}:14988"
)

redis_conn = redis.from_url(REDIS_URL)

worker = rq.Worker(['default', 'GPS_POINT_INGESTION', 'STOP_DETECTION'], connection=redis_conn)
worker.work()