from django.apps import AppConfig


class IngestionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ingestion"

    def ready(self):
        # prevent double-run with autoreloader
        import os
        if os.environ.get("RUN_MAIN") != "true":
            return

        from ingestion.services.gps_batch_runner import start_gps_ingestion
        start_gps_ingestion()