from django.db import models

from core.models import TimeStampedModel


class EventLogOutbox(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    event_type = models.CharField(max_length=255)
    payload = models.JSONField()
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["processed_at"]),
        ]
