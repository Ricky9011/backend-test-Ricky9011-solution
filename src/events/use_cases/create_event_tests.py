import pytest

from events.use_cases.create_event import CreateEvent, CreateEventRequest
from users.use_cases import UserCreated
from events.models import EventOutbox

pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def f_use_case() -> CreateEvent:
    return CreateEvent()


def test_event_created(f_use_case: CreateEvent) -> None:
    created_user = UserCreated(
        email='test@test.org',
        first_name='Test',
        last_name='Testovich',
    )
    events_count_before = EventOutbox.objects.count()
    f_use_case.execute(CreateEventRequest(raw_data=[created_user]))
    events_count_after = EventOutbox.objects.count()
    event = EventOutbox.objects.first()

    assert events_count_before < events_count_after
    assert event.event_type == 'user_created'
    assert event.event_context == created_user.model_dump_json()
    assert event.environment == 'Local'
