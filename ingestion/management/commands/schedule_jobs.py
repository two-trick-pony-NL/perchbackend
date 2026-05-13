from django.core.management.base import BaseCommand
from django.utils import timezone
from django_rq import get_scheduler


JOBS = [
    {
        "queue": "default",
        "func": "ingestion.tasks.process_gps_stream",
        "interval": 10,
    },
    {
        "queue": "GPS_POINT_INGESTION",
        "func": "locations.tasks.process_gps_batches",
        "interval": 10,
    },
]


class Command(BaseCommand):
    help = "Register recurring RQ scheduler jobs (idempotent)"

    def handle(self, *args, **options):
        for job in JOBS:
            scheduler = get_scheduler(job["queue"])
            already_scheduled = any(
                getattr(j, "func", None) == job["func"]
                for j in scheduler.get_jobs()
            )
            if already_scheduled:
                self.stdout.write(f"  already scheduled: {job['func']}")
                continue
            scheduler.schedule(
                scheduled_time=timezone.now(),
                func=job["func"],
                interval=job["interval"],
                repeat=None,
            )
            self.stdout.write(self.style.SUCCESS(f"  scheduled: {job['func']}"))