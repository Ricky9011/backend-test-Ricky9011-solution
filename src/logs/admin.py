from django.contrib import admin

from src.logs.models import OutboxLog


@admin.register(OutboxLog)
class OutboxLogAdmin(admin.ModelAdmin):
    pass
