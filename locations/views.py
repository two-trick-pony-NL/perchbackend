from itertools import chain
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

from locations.models import LocationEvent, TransitEvent
from .serializers import StopEventSerializer, TransitEventSerializer


class EventFeedViewSet(ViewSet):
    PAGE_SIZE = 50

    def list(self, request):
        user_id = request.user.id
        cursor = request.GET.get("cursor")

        stops = LocationEvent.objects.filter(user_id=user_id)
        transits = TransitEvent.objects.filter(user_id=user_id)

        stop_data = StopEventSerializer(stops, many=True).data
        transit_data = TransitEventSerializer(transits, many=True).data

        events = list(chain(stop_data, transit_data))

        events.sort(key=lambda x: x["start_time"], reverse=True)

        if cursor:
            events = [
                e for e in events
                if str(e["start_time"]) < cursor
            ]

        page = events[:self.PAGE_SIZE]

        next_cursor = page[-1]["start_time"] if page else None

        return Response({
            "results": page,
            "next_cursor": next_cursor,
        })