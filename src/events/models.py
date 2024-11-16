from django.db import models

from core.models import TimeStampedModel


class EventLog(TimeStampedModel):
    event_type = models.CharField(max_length=256)
    event_date_time = models.DateTimeField()
    environment = models.CharField(max_length=128)
    event_context = models.TextField()
    metadata_version = models.IntegerField(default=1)
    is_pushed_to_clickhouse = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'EventLog'
        verbose_name_plural = 'EventLogs'
        
        indexes = [
            models.Index(fields=('is_pushed_to_clickhouse', 'id')),
        ]
