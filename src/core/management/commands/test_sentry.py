from django.core.management.base import BaseCommand, CommandParser

from core.services.event_service import EventService
from core.tasks import process_outbox_events


class Command(BaseCommand):
    help = 'Test Sentry integration by publishing and processing test events'

    def add_arguments(self, parser: CommandParser) -> None:
        pass

    def handle(self, *_args: str, **_options: str) -> None:
        try:
            # Publish test event
            self.stdout.write('Publishing test event...')
            EventService.publish_event(
                'test_event',
                {'test': 'data', 'source': 'manual_test'},
            )
            self.stdout.write(self.style.SUCCESS('Event published successfully'))

            # Process events
            self.stdout.write('Processing events...')
            process_outbox_events()
            self.stdout.write(
                self.style.SUCCESS('Events processed - check Sentry for traces'),
            )

            # Force an error for testing
            self.stdout.write('Testing error handling...')
            raise ValueError("Test error for Sentry")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error occurred (should be visible in Sentry): {e}'),
            )
