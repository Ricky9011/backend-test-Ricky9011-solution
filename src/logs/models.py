from django.db import models

# Create your models here.
import uuid
from django.db import models





class EventLogOutbox(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=255)
    event_date_time = models.DateTimeField()
    environment = models.CharField(max_length=50)
    event_context = models.JSONField()
    metadata_version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['processed', 'created_at']),
        ]
        db_table = 'event_log_outbox'
