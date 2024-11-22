from datetime import datetime

from clickhouse_connect.driver import Client
from django.test import override_settings

from src.logs.models import OutboxLog
from src.logs.tasks import export_outbox_logs


class TestExportOutboxLogsTask:
    def get_ch_event_logs(
        self,
        ch_client: Client,
    ) -> list[tuple[str, datetime, str, str, int]]:
        return ch_client.query(
            "SELECT * FROM default.event_log ORDER BY event_date_time",
        ).result_rows

    def test_no_logs(self, ch_client: Client) -> None:
        assert OutboxLog.objects.count() == 0
        assert self.get_ch_event_logs(ch_client) == []

        export_outbox_logs()

        assert OutboxLog.objects.count() == 0
        assert self.get_ch_event_logs(ch_client) == []

    @override_settings(CLICKHOUSE_BATCH_SIZE=3)
    def test_success(
        self,
        ch_client: Client,
        daily_outbox_logs: list[OutboxLog],
    ) -> None:
        assert OutboxLog.objects.filter(exported_at__isnull=False).count() == 6
        assert OutboxLog.objects.filter(exported_at__isnull=True).count() == 4
        assert self.get_ch_event_logs(ch_client) == []

        export_outbox_logs()

        assert OutboxLog.objects.filter(exported_at__isnull=False).count() == 10
        assert OutboxLog.objects.filter(exported_at__isnull=True).count() == 0

        rows = self.get_ch_event_logs(ch_client)
        assert len(rows) == 4
        assert rows == [
            ("test", datetime(2022, 1, day), "dev", "{}", 1)  # noqa: DTZ001
            for day in range(7, 11)
        ]
