from django.urls import path

from .views import ingest_locations

urlpatterns = [
    path("ingest/", ingest_locations, name="ingest-locations"),
]