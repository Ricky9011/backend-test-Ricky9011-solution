from django.db import models


# Create your models here.
class EventOutbox(models.Model):
    event_type = models.CharField(max_length=255)
    event_date_time = models.DateTimeField(auto_now_add=True)
    environment = models.CharField(max_length=100)
    event_context = models.JSONField()
    metadata_version = models.PositiveIntegerField(default=1)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
