from django.db import models

from core.models import TimeStampedModel


# stores event logs according to the outbox pattern for further insert in ch
class OutboxEvent(TimeStampedModel, models.Model):
    EVENT_TYPES = [
        ("user_created", "User Created"),
    ]

    class ProcessedStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSED = "PROCESSED", "Processed"

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    environment = models.CharField(max_length=50)
    event_context = models.JSONField()
    metadata_version = models.BigIntegerField(default=1)
    status = models.CharField(
        max_length=10,
        choices=ProcessedStatus.choices,
        default=ProcessedStatus.PENDING,
    )

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} at {self.created_at}"
