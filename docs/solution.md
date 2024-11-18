Обзор проблемы:
Исходная проблема заключалась в том, что наше приложение отправляло логи событий напрямую в ClickHouse из веб-воркера. Это приводило к следующим проблемам:
- Потеря событий: при сбое веб-воркера между выполнением бизнес-логики и записью в ClickHouse события терялись.
- Плохой UX: ошибки при записи в ClickHouse приводили к задержкам и ошибкам на стороне пользователя.
- Низкая производительность ClickHouse: множество мелких вставок данных негативно сказывалось на производительности ClickHouse.



Для решения использован шаблон транзакционного Outbox (Transactional Outbox pattern).

Почему именно этот шаблон:
- Транзакционность: записи логов сохраняются в той же транзакции, что и основная бизнес-операция. Это гарантирует, что события не будут потеряны и сохранятся только при успешном выполнении операции.
- Асинхронность: отправка логов в ClickHouse происходит асинхронно, с помощью фоновых задач Celery. Это снижает нагрузку на веб-воркер и улучшает UX.
- Пакетная обработка: логи отправляются в ClickHouse пакетами, что повышает эффективность и производительность.

Этапы решения:
- Создана модель EventLogOutbox для хранения событий в локальной базе данных PostgreSQL.
- Вместо прямой записи в ClickHouse, логи сохраняются в таблицу EventLogOutbox. Запись происходит в рамках транзакции основной бизнес-логики, что обеспечивает целостность данных.
- Реализована задача send_event_logs, которая периодически отправляет непрочитанные логи в ClickHouse. После успешной отправки логи помечаются как обработанные.
- Логи отправляются в ClickHouse пакетами по 1000 записей, что уменьшает количество вставок и повышает эффективность работы ClickHouse.
- Основная логика отправки логов вынесена в сервис EventLogService. Задача Celery использует этот сервис, что повышает переиспользуемость кода.
- Во всех новых модулях используется structlog для единообразного и структурированного логирования.
- Все настройки берутся из переменных окружения, что соответствует принципам 12-factor app.


Диаграмма архитектуры:
+--------------------+
|   Django App       |
| (CreateUser UseCase)|
+---------+----------+
          |
          | Save event to EventLogOutbox (PostgreSQL)
          v
+--------------------+
|  PostgreSQL        |
| (EventLogOutbox)   |
+---------+----------+
          |
          | Celery task fetches unprocessed events
          v
+--------------------+
|   Celery Worker    |
| (send_event_logs)  |
+---------+----------+
          |
          | Send events in batches
          v
+--------------------+
|    ClickHouse      |
| (event_log table)  |
+--------------------+


Инструкция по запуску проекта находится в README.md



in English:
Problem Overview:
The original problem was that our application was sending event logs directly to ClickHouse from the webworker. This was causing the following problems:
- Loss of events: events were lost when the webworker crashed between executing business logic and writing to ClickHouse.
- Poor UX: errors when writing to ClickHouse resulted in delays and errors on the user side.
- Poor ClickHouse performance: many small data inserts were negatively impacting ClickHouse performance.



The Transactional Outbox pattern (Transactional Outbox pattern) was used for the solution.

Why this pattern:
- Transactional: log records are stored in the same transaction as the underlying business transaction. This ensures that events are not lost and are only saved when the transaction is successful.
- Asynchronous: sending logs to ClickHouse is done asynchronously by Celery background tasks. This reduces the load on the webworker and improves the UX.
- Batch processing: logs are sent to ClickHouse in batches, which improves efficiency and performance.

Solution Stages:
- Created an EventLogOutbox model to store events in a local PostgreSQL database.
- Instead of writing directly to ClickHouse, logs are saved to the EventLogOutbox table. The logging takes place within the core business logic transaction, which ensures data integrity.
- The send_event_logs task is implemented, which periodically sends unread logs to ClickHouse. After successful sending, the logs are marked as processed.
- Logs are sent to ClickHouse in batches of 1000 records, which reduces the number of inserts and increases the efficiency of ClickHouse.
- The main logic of sending logs is placed in the EventLogService. Celery task uses this service, which increases code reusability.
- All new modules use structlog for uniform and structured logging.
- All customizations are taken from environment variables, which is in line with 12-factor app principles.


Architecture diagram:
+--------------------+
| Django App |
| (CreateUser UseCase)|
+---------+----------+
          |
          | Save event to EventLogOutbox (PostgreSQL)
          v
+--------------------+
| PostgreSQL |
| (EventLogOutbox) |
+---------+----------+
          |
          | Celery task fetches unprocessed events
          v
+--------------------+
| Celery Worker |
| (send_event_logs) |
+---------+----------+
          |
          | Send events in batches
          v
+--------------------+
| ClickHouse |
| (event_log table) |
+--------------------+


Instructions on how to start the project can be found in README.md