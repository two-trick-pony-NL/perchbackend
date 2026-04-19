from django.urls import path
from .views import EventFeedViewSet

event_feed = EventFeedViewSet.as_view({"get": "list"})

urlpatterns = [
    path("events/", event_feed),
]