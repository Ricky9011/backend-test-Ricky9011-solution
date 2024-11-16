import structlog

from core.event_log_client import EventLogClient, EVENT_LOG_COLUMNS
from core.use_case import UseCase, UseCaseRequest, UseCaseResponse
from events.models import EventLog
from users.models import User

logger = structlog.get_logger(__name__)


class PushEventsLogRequest(UseCaseRequest):
    batch: int = 1000


class PushEventsLogResponse(UseCaseResponse):
    result: User | None = None
    error: str = ''


class PushEventsLogToClickhouse(UseCase):
    
    def _execute(self, request: PushEventsLogRequest) -> PushEventsLogResponse:
        
        with EventLogClient.init() as client:
            while True:
                event_logs_data = list(
                    EventLog.objects
                    .select_for_update()
                    .filter(is_pushed_to_clickhouse=False)
                    #  In Postgres, the true comes first, in SQLite, false comes first
                    .order_by('-is_pushed_to_clickhouse', '-id')
                    .values_list(*EVENT_LOG_COLUMNS, 'id')
                    [:request.batch]
                )
                if not len(event_logs_data):
                    break
                
                event_logs_ids = []
                event_logs_to_push = []
                for items in event_logs_data:
                    event_logs_ids.append(items[-1])
                    event_logs_to_push.append(items[:-1])
                    client.insert(data=event_logs_to_push)
                
                EventLog.objects.filter(id__in=event_logs_ids).update(is_pushed_to_clickhouse=True)
                logger.info('pushed {} log events into clickhouse'.format(len(event_logs_to_push)))
        
        return PushEventsLogResponse()
