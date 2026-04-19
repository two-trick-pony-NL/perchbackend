from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class FeedEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    type = models.CharField(max_length=50)  # stop, copresence, memory
    data = models.JSONField()

    timestamp = models.DateTimeField()