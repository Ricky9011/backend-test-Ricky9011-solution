from django.contrib.auth.models import AbstractBaseUser
from django.db import models, transaction

from core.models import TimeStampedModel


class User(TimeStampedModel, AbstractBaseUser):
    email = models.EmailField(unique=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    class Meta(AbstractBaseUser.Meta):
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None, # noqa
    ) -> None:
        with transaction.atomic():
            super().save(force_insert, force_update, using, update_fields)

            # import here to avoid circular import
            from outbox.models import OutboxUser
            OutboxUser.objects.create(user=self)

    def __str__(self) -> str:
        if all([self.first_name, self.last_name]):
            return f'{self.first_name} {self.last_name}'

        return self.email
