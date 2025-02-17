### Реализация решения

1. Была создана таблица `EventOutbox` в PostgreSQL, которая сохраняет логи событий.
При логировании события записываются сначала в нее. Для этого был реализован EventOutboxLogger в [event_outbox_logger.py](..%2Fsrc%2Fcore%2Fevent_outbox_logger.py).
2. Добавлена периодическая задача Celery в [tasks.py](..%2Fsrc%2Fusers%2Ftasks.py),
которая батчами размером по 1000 записей (`settings.CLICKHOUSE_BATCH_SIZE`) перезаписывает события
из таблицы `EventOutbox` в Clickhouse с интервалом в 10 минут (`settings.CLICKHOUSE_UPDATE_INTERVAL`).\
Для этого были добавлены сервисы в compose файл: `celery_worker` и `celery_beat`, конфиг для celery [celery.py](..%2Fsrc%2Fcore%2Fcelery.py).

#### Таким образом, в текущей реализации:
1. Запсись в Clickhouse асинхронная
2. Использовал transaction при перезаписи записей, разрешил `EventLogClient` выбрасывать ошибки, сохранив логирование.
В самой задаче перезаписи дополнительного логирования нет (просто except: pass), поскольку достаточно логирования в `EventLogClient`.
3. Решили проблему с тем что запись в Clickhouse производилась по 1 записи и работала неоптимально.
4. Тесты, честно, не трогал

#### In addition:
  - Заменил кастомно-реализованный метод для каста к camel case на `underscore` из библиотеки `inflection`.
  - В conftest исправил захардкоженный host на `settings.CLICKHOUSE_HOST`
  - Заменил в [.env.ci](..%2Fsrc%2Fcore%2F.env.ci) `CELERY_BROKER` на `redis://redis:6379/0`