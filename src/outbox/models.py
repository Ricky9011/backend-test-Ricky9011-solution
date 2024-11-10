from django.db import models

from core.models import TimeStampedModel
from users.models import User


class OutboxUser(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
