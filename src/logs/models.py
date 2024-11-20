from django.db import models


class OutboxLog(models.Model):
    class Meta:
        verbose_name = "Outbox Log"
        verbose_name_plural = "Outbox Logs"

    event_type = models.CharField(max_length=255, verbose_name="Event Type")
    event_date_time = models.DateTimeField(verbose_name="Event Date Time")
    environment = models.CharField(max_length=7, verbose_name="Environment")
    event_context = models.TextField(verbose_name="Event Context")
    metadata_version = models.BigIntegerField(verbose_name="Metadata Version")
    exported_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Exported At",
    )

    def __str__(self) -> str:
        return f"{self.event_type} - {self.event_date_time}"
