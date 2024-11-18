from datetime import datetime

from django.db import models
from django.utils import timezone

from src.core.base_model import Model


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None,  # noqa
    ) -> None:
        # https://docs.djangoproject.com/en/5.1/ref/models/fields/#django.db.models.DateField.auto_now
        self.updated_at = timezone.now()

        if isinstance(update_fields, list):
            update_fields.append('updated_at')
        elif isinstance(update_fields, set):
            update_fields.add('updated_at')

        super().save(force_insert, force_update, using, update_fields)


class EventLogOutbox(models.Model):
    """
    Модель для хранения событий в таблице Outbox.

    Поля:
        - id: Уникальный идентификатор записи.
        - event_type: Тип события (например, 'user_created').
        - event_date_time: Дата и время события.
        - environment: Окружение приложения (например, 'production').
        - event_context: Контекст события в формате JSON.
        - metadata_version: Версия метаданных события.
        - processed: Указывает, было ли событие обработано и отправлено.
    """
    id = models.BigAutoField(primary_key=True)
    event_type = models.CharField(max_length=255)
    event_date_time = models.DateTimeField(default=timezone.now)
    environment = models.CharField(max_length=50)
    event_context = models.JSONField()
    metadata_version = models.PositiveIntegerField(default=1)
    processed = models.BooleanField(default=False)

    class Meta:
        db_table = 'event_log_outbox'


class EventLog(Model):
    """
    Модель для логов событий в ClickHouse.
    Используется для сериализации событий перед отправкой в ClickHouse.

    Поля:
       - event_type: Тип события (например, 'user_created')
       - event_date_time: Дата и время возникновения события
       - environment: Окружение приложения (например, 'production', 'staging')
       - event_context: Контекст события в формате словаря с дополнительными данными

    """

    class Config:
        arbitrary_types_allowed = True

    event_type: str
    event_date_time: datetime
    environment: str
    event_context: dict
    metadata_version: int = 1