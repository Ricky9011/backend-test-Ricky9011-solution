from django.db import models


class Outbox(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_type = models.CharField(max_length=255)
    event_date_time = models.DateTimeField(auto_now_add=True)
    environment = models.CharField(max_length=20)
    event_context = models.JSONField()
    processed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

