from datetime import timedelta

from clickhouse_connect.driver import Client
from django.test import override_settings
from freezegun import freeze_time

from src.logs.models import OutboxLog
from src.logs.tasks import cleanup_outbox


class TestCleanupOutbox:
    def test_no_logs(self, ch_client: Client) -> None:
        assert OutboxLog.objects.count() == 0

        cleanup_outbox()

        assert OutboxLog.objects.count() == 0

    @override_settings(CLICKHOUSE_CLEANUP_INTERVAL=0)
    def test_success(
        self,
        ch_client: Client,
        daily_outbox_logs: list[OutboxLog],
    ) -> None:
        assert OutboxLog.objects.filter(exported_at__isnull=False).count() == 6
        assert OutboxLog.objects.filter(exported_at__isnull=True).count() == 4

        with freeze_time(daily_outbox_logs[3].exported_at + timedelta(seconds=1)):
            cleanup_outbox()

        assert OutboxLog.objects.filter(exported_at__isnull=False).count() == 2
        assert OutboxLog.objects.filter(exported_at__isnull=True).count() == 4

        for log in daily_outbox_logs[:4]:
            assert not OutboxLog.objects.filter(id=log.id).exists()
