from rest_framework import serializers


class LocationPingSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    timestamp = serializers.DateTimeField()

    # NEW SIGNALS (all optional for backward compatibility)
    accuracy = serializers.FloatField(required=False, allow_null=True)
    speed = serializers.FloatField(required=False, allow_null=True)
    heading = serializers.FloatField(required=False, allow_null=True)

    altitude = serializers.FloatField(required=False, allow_null=True)
    altitude_accuracy = serializers.FloatField(required=False, allow_null=True)


class LocationBatchSerializer(serializers.Serializer):
    locations = LocationPingSerializer(many=True)