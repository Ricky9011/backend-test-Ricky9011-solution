## Testing Strategy

Our testing approach focuses on ensuring the reliability of the event logging system. Here's what we test and why:

### Event Publishing Tests (`test_event_service.py`)

1. **Successful Event Publishing**
```python
def test_publish_event_success():
    """Test successful event publishing"""
    EventService.publish_event('test_event', {'test': 'data'})
    
    event = OutboxEvent.objects.first()
    assert event.event_type == 'test_event'
    assert event.event_data == {'test': 'data'}
    assert event.status == OutboxEvent.STATUS_PENDING
```
This test ensures that:
- Events are correctly saved to the outbox table
- All event fields are properly stored
- Initial event status is set to 'pending'

2. **Error Handling**
```python
def test_publish_event_database_error(mocker):
    """Test handling of database errors during event publishing"""
    mocker.patch('core.models.OutboxEvent.objects.create',
                 side_effect=DatabaseError("Test DB Error"))
    
    with pytest.raises(EventPublishError) as exc_info:
        EventService.publish_event('test_event', {'test': 'data'})
    
    assert "Failed to publish event" in str(exc_info.value)
```
This test verifies that:
- Database errors are properly caught and wrapped
- Custom EventPublishError is raised with meaningful message
- System fails gracefully when database operations fail

### Integration Tests

Our tests use real PostgreSQL and ClickHouse instances (via Docker) instead of mocks where possible. This ensures:
- Real database interactions are tested
- Transaction handling works as expected
- Integration between services functions correctly

### Running Tests

1. Run all tests:
```bash
docker-compose exec app pytest
```

### Test Dependencies
- `pytest-django`: For Django test utilities and fixtures
- `pytest-mock`: For mocking in Python tests

### What We Test

1. **Event Publishing**
   - Successful event creation
   - Error handling
   - Transaction integrity

2. **Event Processing**
   - Batch processing
   - Error handling during processing
   - Retry mechanism

3. **Integration Points**
   - PostgreSQL interactions
   - ClickHouse interactions
   - Celery task execution

4. **Edge Cases**
   - Database errors
   - Network failures
   - Invalid event data

### What We Don't Mock
We prefer using real instances over mocks for:
- Database connections
- ClickHouse operations
- Basic Django ORM operations

This ensures our tests catch real-world issues that might be missed with mocks.

### Future Test Improvements
- Add performance tests for batch processing
- Add stress tests for high event volumes
- Add monitoring tests for queue metrics
- Add end-to-end tests for complete event flow

