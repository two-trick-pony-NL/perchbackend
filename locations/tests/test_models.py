import pytest
from django.contrib.auth import get_user_model

from locations.models import LocationPing

User = get_user_model()


@pytest.mark.django_db
def test_location_ping_creation():
    user = User.objects.create(username="testuser")

    ping = LocationPing.objects.create(
        user=user,
        lat=52.370216,
        lon=4.895168,
        h3_r15="8f2830828052bff",
        h3_r13="8d2830828052bfff",
        h3_r12="8c2830828052bfff",
        h3_r10="8a2830828052bfff",
        h3_r8="88283082805ffff",
        accuracy_m=5.0,
        speed_mps=0.0,
        timestamp="2026-04-13T12:00:00Z",
    )

    assert ping.id is not None
    assert ping.user.username == "testuser"
    assert ping.h3_r12.startswith("8c")