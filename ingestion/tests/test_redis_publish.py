from unittest.mock import MagicMock, patch
from ingestion.services import publisher


def test_publish_gps_batch_mock_redis():
    mock_redis = MagicMock()
    mock_pipe = MagicMock()

    mock_redis.pipeline.return_value = mock_pipe

    with patch("ingestion.services.publisher.redis_host", mock_redis):
        publisher.publish_gps_batch(
            user_id=1,
            locations=[
                {
                    "lat": 1,
                    "lon": 2,
                    "timestamp": __import__("datetime").datetime(2026, 1, 1)
                }
            ]
        )

    mock_redis.pipeline.assert_called_once()
    mock_pipe.xadd.assert_called_once()
    mock_pipe.execute.assert_called_once()