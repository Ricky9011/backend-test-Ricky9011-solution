from core.base_model import Model
from core.celery import app
from core.event_log_client import EventLogClient
from outbox.models import OutboxUser

BATCH_SIZE = 100


class UserCreated(Model):
    email: str
    first_name: str
    last_name: str


# outbox is defined as a list in order to get passed by reference
def write_to_log(outbox: list[OutboxUser]) -> None:
    users = []
    outbox_ids = []
    for box in outbox:
        users.append(UserCreated(email=box.user.email,
                                 first_name=box.user.first_name,
                                 last_name=box.user.last_name),
                     )
        outbox_ids.append(box.id)
    with EventLogClient.init() as client:
        inserted = client.insert(data=users)
        if inserted:
            OutboxUser.objects.filter(id__in=outbox_ids).delete()


@app.task
def add_db() -> None:
    while True:
        outbox = OutboxUser.objects.select_related('user').all().order_by('id')[:BATCH_SIZE]
        if not outbox:
            break
        write_to_log(list(outbox))
