CREATE TABLE IF NOT EXISTS event_log
(
    `event_type` String,
    `event_date_time` DateTime64(6),
    `environment` String,
    `event_context` String,
    `metadata_version` Int32 DEFAULT 1,
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date_time)
ORDER BY (event_date_time, event_type)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS buffer_event_log
(
    `event_type` String,
    `event_date_time` DateTime64(6),
    `environment` String,
    `event_context` String,
    `metadata_version` Int32 DEFAULT 1,
)
ENGINE = Buffer(default, event_log, 16, 10, 60, 100, 10000, 1000000, 10000000, 100000000);
