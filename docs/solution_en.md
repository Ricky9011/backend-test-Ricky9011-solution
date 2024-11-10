# Backend test task

## # The Problem

Our application sends event logs that are later used for business analysis, incident investigations and security audits.

To store these logs we use a column-based database Clickhouse and the so-called One Big Table (further referred to as OBT) - a wide table that
contains the following columns (the columns may be extended in the future):

```
event_type: String
event_date_time: DateTime
environment: String
event_context: String // JSON field with unstructured payload
metadata_version: UInt64 // for versioning purposes
```

The application pushes logs synchronously directly to CH, see an example in the `CreateUser` use case.

This approach has caused several problems, such as:

- due to the lack of transactionality logs are missed in case of a web-worker failure before the business-logic step is executed
- Clickhouse network write errors cause poor UX
- Clickhouse struggles with large numbers of small inserts (see https://clickhouse.com/blog/common-getting-started-issues-with-clickhouse#many-small-inserts)

We need to implement a new write mechanism that will eliminate those problems and provide a convenient interface for publishing logs

**Restrictions and requirements:**

- for the sake of simplicity we don't want to use Kafka for event streaming.
- we don't want to use Clickhouse-specific features such as RabbitMQ/Kafka engine for publishing logs since there is a chance that Clickhouse will be replaced with another database down the line
- we don't want to use external file storage, like AWS S3
- the `event_context` field contains unstructured JSON payload up to N MBytes so it may not be a good idea to push it directly to a queue
- `Transactional outbox pattern` might be useful for this problem
- we would like to see a simple and efficient solution that uses a well-known tech stack for ease of maintenance, monitoring and debugging

## # The Solution

To solve the problem we decided to use the `Transactional outbox pattern`. This approach involves creating an additional table, which serves as the central source of events to be processed by other services. Using database transactions ensures that only data that has been truly committed to the database is processed by other services, thereby avoiding duplication.

The table `OutboxUser` is created for this purpose, this makes it very efficient for storage and querying as the table needs only to store its own ID and the ID of the user that will get written in logs as a foreign key. This design reduces the amount of data read and written to the database, ensuring efficiency, especially if message queues are implemented in the future. In this solution, multiple outbox tables will be created for different event types, making it easier for specific workers to process each type of event and facilitating data parsing and processing.

Message queues are not used in this solution in order to keep it simple, but can be used when there is a need for multiple consumers to process the data.

`Celery beat` is chosen as the scheduler for this task, it is chosen instead of crontabs due to its simplicity to set up and its easy integration with Django.

The scheduler checks for any new data in the outbox tables at specific intervals (currently every 10 seconds, should be adjusted according to business needs). If there is any data in the table, then the data is processed in batches for efficiency (currently in batches of size 100, although the minimum recommended by Clickhouse is 1000; the current value can be adjusted according to business needs). Once the data is processed, it is deleted to prevent duplication.
