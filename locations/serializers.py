from rest_framework import serializers
from .models import LocationEvent, TransitEvent


class StopEventSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = LocationEvent
        fields = "__all__"  # or explicit fields if you want control

    def get_type(self, obj):
        return "stop"

class TransitEventSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = TransitEvent
        fields = "__all__"

    def get_type(self, obj):
        return "transit"