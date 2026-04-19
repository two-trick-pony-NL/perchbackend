import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class IngestLocationsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        )
        self.url = "/api/v1/ingestion/ingest/"

        self.payload = {
            "locations": [
                {
                    "lat": 52.370216,
                    "lon": 4.895168,
                    "timestamp": "2026-04-13T10:00:00Z"
                },
                {
                    "lat": 52.371000,
                    "lon": 4.896000,
                    "timestamp": "2026-04-13T10:00:05Z"
                }
            ]
        }

    def authenticate(self):
        self.client.login(username="testuser", password="testpass")

    @patch("ingestion.views.publish_gps_batch")
    def test_ingest_locations_success(self, mock_publish):
        self.authenticate()

        response = self.client.post(
            self.url,
            data=self.payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["ingested"], 2)

        mock_publish.assert_called_once()

        args = mock_publish.call_args[0]
        self.assertEqual(args[0], self.user.id)
        self.assertEqual(len(args[1]), 2)

    def test_requires_authentication(self):
        response = self.client.post(
            self.url,
            data=self.payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    def test_invalid_payload_missing_locations(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            data={},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_location_data(self):
        self.authenticate()

        payload = {
            "locations": [
                {
                    "lat": "not-a-float",
                    "lon": 4.89,
                    "timestamp": "2026-04-13T10:00:00Z"
                }
            ]
        }

        response = self.client.post(
            self.url,
            data=payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)