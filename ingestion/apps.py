from django.apps import AppConfig


class IngestionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ingestion"

    def ready(self):
        import os
        if os.environ.get("RUN_MAIN") != "true":
            return

        from django_rq import get_scheduler
        from django.utils import timezone

        scheduler = get_scheduler("default")

        # prevent duplicate scheduling across processes
        existing_jobs = scheduler.get_jobs()

        already_scheduled = any(
            getattr(job, "func", None) == "ingestion.tasks.process_gps_stream"
            for job in existing_jobs
        )
        print("🤖Scheduling GPS Point Ingestion")

        if already_scheduled:
            print("❌ -- Process is already running")
            return

        scheduler.schedule(
            scheduled_time=timezone.now(),
            func="ingestion.tasks.process_gps_stream",
            interval=10,   # adjust as needed
            repeat=None,
        )
        print("✅  GPS Point Ingestion Scheduled")