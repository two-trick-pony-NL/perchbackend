from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class Friendship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friends")
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friend_of")

    created_at = models.DateTimeField(auto_now_add=True)