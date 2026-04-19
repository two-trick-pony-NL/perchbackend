from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import LocationBatchSerializer
from .services.publisher import publish_gps_batch


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ingest_locations(request):
    serializer = LocationBatchSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    locations = serializer.validated_data.get("locations", [])

    if not locations:
        return Response(
            {
                "status": "error",
                "message": "No locations provided",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        publish_gps_batch(request.user.id, locations)
    except Exception as e:
        return Response(
            {
                "status": "error",
                "message": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {
            "status": "ok",
            "ingested": len(locations),
        },
        status=status.HTTP_200_OK,
    )