import datetime as dt
from collections.abc import Iterable
from functools import cached_property

from django.db import models
from django.utils import timezone
from pydantic import BaseModel

from src.common.utils import generate_ulid


class PydanticModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            dt.date: lambda v: v.isoformat(),
            dt.datetime: lambda v: v.isoformat(),
            Exception: lambda e: str(e),
        }
        ignored_types = (cached_property,)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True

    def save(
        self,
        force_insert: int = False,
        force_update: int = False,
        using: str | None = None,
        update_fields: Iterable | None = None,
    ) -> None:
        # https://docs.djangoproject.com/en/5.1/ref/models/fields/#django.db.models.DateField.auto_now
        self.updated_at = timezone.now()

        if isinstance(update_fields, list):
            update_fields.append("updated_at")
        elif isinstance(update_fields, set):
            update_fields.add("updated_at")

        super().save(force_insert, force_update, using, update_fields)


class UUIDModel(models.Model):
    class Meta:
        abstract = True

    id = models.UUIDField(
        primary_key=True,
        default=generate_ulid,
        editable=False,
        verbose_name="ID",
    )
