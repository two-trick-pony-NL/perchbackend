from django.apps import AppConfig


class LocationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "locations"

    def ready(self):
        # prevent double-run with autoreloader
        import os
        if os.environ.get("RUN_MAIN") != "true":
            return

        from locations.services.stop_runner import start_stop_worker
        start_stop_worker()