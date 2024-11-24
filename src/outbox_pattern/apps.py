from django.apps import AppConfig


class OutboxPatternConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'outbox_pattern'
