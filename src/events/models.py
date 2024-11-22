from django.db import models

from core.models import TimeStampedModel


class EventOutbox(TimeStampedModel):
    event_type = models.CharField(max_length=255)
    environment = models.CharField(max_length=255)
    event_context = models.TextField()
    is_sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'event_outbox'
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self) -> str:
        return f'{self.event_type} in {self.environment}: {self.event_context}'
