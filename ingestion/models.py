from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class GPSBatch(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)

    points = models.JSONField()
    point_count = models.IntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )

    attempts = models.IntegerField(default=0)

    last_error = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)