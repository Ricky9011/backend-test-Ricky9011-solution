from django.core.management.base import BaseCommand
from logs.services import process_logs

class Command(BaseCommand):
    help = "Process logs in the outbox and send them to ClickHouse."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=100, help="Number of logs to process in a single batch")

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        processed_count = process_logs(batch_size=batch_size)
        self.stdout.write(f"Successfully processed {processed_count} logs.")
