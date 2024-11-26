# Sentry Integration Documentation

## Overview

This document describes how Sentry is integrated into our event logging system for monitoring, error tracking, and performance analysis.

## Purpose

Sentry integration serves several key purposes in our project:
1. Transaction monitoring for event processing
2. Error tracking and debugging
3. Performance monitoring for batch operations
4. Real-time alerts for critical issues

## Implementation

### Core Components

1. **Event Processing Monitoring**
```python
# core/tasks.py

@shared_task
def process_outbox_events():
    """Monitored by Sentry transaction"""
    with start_transaction(op="process_events", name="process_outbox_events") as transaction:
        try:
            # Process events...
            transaction.set_status("ok")
        except Exception as e:
            transaction.set_status("internal_error")
            transaction.set_data("error", str(e))
            raise
```

2. **Transaction Data Points**
- Batch size
- Processing status
- Error information
- Processing duration

### Key Metrics Tracked

1. **Success Metrics**
- Number of events processed
- Batch processing time
- Queue size

2. **Error Metrics**
- Failed events count
- Error types
- Retry attempts

## Testing

### Unit Tests Location
Tests are located in `core/tests/test_outbox_processing_tests.py` (note the '_tests.py' suffix as per pytest configuration)

### Key Test Scenarios
```python
def test_process_outbox_events_sentry_integration():
    """Tests successful event processing with Sentry monitoring"""
    # Test implementation...

def test_process_outbox_events_sentry_error_handling():
    """Tests error handling and Sentry error reporting"""
    # Test implementation...
```

### Running Tests
```bash
# Run all tests
docker-compose exec app pytest
```

## Configuration

### Environment Variables
```env
SENTRY_CONFIG_DSN="your-sentry-dsn"
SENTRY_CONFIG_ENVIRONMENT="dev"
```

### Sentry Setup in Django
```python
# core/settings.py

SENTRY_SETTINGS = {
    "dsn": env("SENTRY_CONFIG_DSN"),
    "environment": env("SENTRY_CONFIG_ENVIRONMENT"),
}

if SENTRY_SETTINGS.get("dsn") and not DEBUG:
    sentry_sdk.init(
        dsn=SENTRY_SETTINGS["dsn"],
        environment=SENTRY_SETTINGS["environment"],
        integrations=[
            sentry_sdk.DjangoIntegration(),
            sentry_sdk.CeleryIntegration(),
        ],
        default_integrations=False,
    )
```

## Monitoring in Sentry UI

### Key Areas to Monitor

1. **Performance**
- Transaction duration
- Batch processing time
- Queue processing metrics

2. **Issues**
- Failed event processing
- Database connection issues
- ClickHouse insertion errors

3. **Alerts**
- High error rates
- Processing delays
- Queue buildup

### Custom Queries

Monitor failed events:
```sql
type:transaction op:process_events status:internal_error
```

## Best Practices

1. **Transaction Naming**
- Use consistent operation names
- Include meaningful context
- Follow `operation_action` format

2. **Error Handling**
- Always set transaction status
- Include relevant error context
- Use proper error grouping

3. **Performance Monitoring**
- Monitor batch sizes
- Track processing duration
- Set appropriate alert thresholds

## Troubleshooting

Common issues and solutions:
1. Missing transactions
   - Check Sentry DSN configuration
   - Verify environment settings

2. Incomplete error data
   - Ensure proper exception handling
   - Check context data inclusion

3. Performance issues
   - Monitor batch sizes
   - Check database connection pools
   - Verify ClickHouse performance

