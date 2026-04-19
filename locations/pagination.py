from rest_framework.pagination import CursorPagination


class EventCursorPagination(CursorPagination):
    page_size = 50
    ordering = "-start_time"