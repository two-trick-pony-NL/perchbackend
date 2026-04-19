import time
from core.settings import redis_host as r
from ingestion.models import GPSBatch
from .services.stop_classifier import process_trajectory

def process_gps_batches():
    lock_key = None

    try:
        #First we have to find the user_id of the last GPS Batch we have
        user_id = (
            GPSBatch.objects
            .filter(status=GPSBatch.Status.PENDING)
            .order_by("created_at")
            .values_list("user_id", flat=True)
            .first()
        )

        if not user_id:
            #No user with pending batches
            return

        batches = list(
            GPSBatch.objects
            .filter(user_id=user_id, status=GPSBatch.Status.PENDING)
            .order_by("created_at")
        )

        # We grab the last batch already processed so we have context where the user left off.
        last_done = (
            GPSBatch.objects
            .filter(user_id=user_id, status=GPSBatch.Status.DONE)
            .order_by("-created_at")
            .first()
        )

        # If there was a last batch we add it to the batches list
        if last_done:
            batches = [last_done] + batches

        if not batches:
            #No batches to process
            return


        lock_key = f"gps:lock:{user_id}"

        if not r.set(lock_key, "1", nx=True, ex=120):
            time.sleep(0.2)

        try:
            # mark all as processing first
            GPSBatch.objects.filter(
                id__in=[b.id for b in batches]
            ).update(status=GPSBatch.Status.PROCESSING)

            # aggregate points
            all_points = []
            for batch in batches:
                all_points.extend(batch.points)

            # ensure correct ordering
            all_points.sort(key=lambda p: p["timestamp"])

            # process full trajectory
            process_trajectory(user_id, all_points)
            print("Stop Detector --- Processing User: ", user_id, str(len(all_points)), " Points")

            # mark done
            GPSBatch.objects.filter(
                id__in=[b.id for b in batches]
            ).update(status=GPSBatch.Status.DONE)

        except Exception as e:
            GPSBatch.objects.filter(
                id__in=[b.id for b in batches]
            ).update(
                status=GPSBatch.Status.FAILED,
                last_error=str(e),
            )
            raise

    finally:
        if lock_key:
            r.delete(lock_key)