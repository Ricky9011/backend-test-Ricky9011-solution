# src/core/services/monitoring.py

from django.db.models import Count

from core.models import OutboxEvent


def get_queue_metrics() -> dict:
    """
    Returns metrics about the current state of the event queue
    """
    return OutboxEvent.objects.values('status').annotate(
        count=Count('id'),
    ).order_by('status')
