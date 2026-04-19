from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


# locations/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class LocationEvent(models.Model):
    class Type(models.TextChoices):
        STOP = "stop", "Stop"
        ZONE = "zone", "Zone"

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)

    # ----------------------------
    # TIME
    # ----------------------------
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    duration_seconds = models.IntegerField()

    # ----------------------------
    # SPACE
    # ----------------------------
    h3 = models.CharField(max_length=20, db_index=True)
    center_lat = models.FloatField()
    center_lon = models.FloatField()

    # ----------------------------
    # UNCERTAINTY MODEL
    # ----------------------------
    confidence = models.FloatField()
    avg_accuracy_m = models.FloatField()
    radius_m = models.FloatField()

    # ----------------------------
    # CLASSIFICATION
    # ----------------------------
    event_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        db_index=True,
    )

    # ----------------------------
    # FEATURES (future ML / debugging)
    # ----------------------------
    features = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "start_time"]),
            models.Index(fields=["user", "event_type"]),
            models.Index(fields=["h3"]),
        ]

class TransitEvent(models.Model):
    """
    Derived movement edge between two LocationEvents.

    This is NOT a behavioral state.
    It is a relationship: how the user moved between places.
    """

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    start_event = models.ForeignKey(
        LocationEvent,
        on_delete=models.CASCADE,
        related_name="transits_out",
    )

    end_event = models.ForeignKey(
        LocationEvent,
        on_delete=models.CASCADE,
        related_name="transits_in",
    )

    # ------------------------------------------------------------
    # SPATIAL EDGE
    # ------------------------------------------------------------
    start_h3 = models.CharField(max_length=20, db_index=True)
    end_h3 = models.CharField(max_length=20, db_index=True)

    # ------------------------------------------------------------
    # TEMPORAL EDGE
    # ------------------------------------------------------------
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)

    duration_seconds = models.IntegerField()

    # ------------------------------------------------------------
    # MOVEMENT FEATURES
    # ------------------------------------------------------------
    distance_meters = models.FloatField()
    speed_mps = models.FloatField()

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "start_time"]),
            models.Index(fields=["user", "end_time"]),
        ]

    def __str__(self):
        return f"{self.user_id} transit {self.start_h3} → {self.end_h3}"