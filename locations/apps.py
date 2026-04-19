from django.apps import AppConfig

class LocationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "locations"

    def ready(self):
        import os
        if os.environ.get("RUN_MAIN") != "true":
            return

        from django_rq import get_scheduler
        from django.utils import timezone

        scheduler = get_scheduler("default")

        # prevent duplicate schedules
        existing_jobs = scheduler.get_jobs()

        already_scheduled = any(
            getattr(job, "func", None) == "locations.tasks.process_gps_batches"
            for job in existing_jobs
        )

        if already_scheduled:
            return

        scheduler.schedule(
            scheduled_time=timezone.now(),
            func="locations.tasks.process_gps_batches",
            interval=10,   # every N seconds
            repeat=None,
        )