import functools
from collections.abc import Callable, Mapping, Sequence
from typing import Any, ParamSpec, TypeVar

import sentry_sdk
import structlog
from sentry_sdk.tracing import Transaction

logger = structlog.get_logger(__name__)

R = TypeVar('R')
P = ParamSpec('P')

def _handle_transaction(
    transaction: Transaction,
    operation_name: str,
    trace_data: dict[str, str],
    func: Callable[P, R],
    args: Sequence[Any],
    kwargs: Mapping[str, Any],
) -> R:
    """Handle the main transaction logic"""
    # Add metadata to transaction
    for key, value in trace_data.items():
        transaction.set_data(key, value)

    # Execute function with structured logging
    with structlog.contextvars.bound_contextvars(**trace_data):
        logger.info(f"starting_{operation_name}")
        result = func(*args, **kwargs)
        logger.info(f"completed_{operation_name}")

    transaction.set_status("ok")
    return result

def trace_event(
    operation_name: str,
    metadata: dict[str, str] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that creates a Sentry transaction and adds structured logging.

    Args:
        operation_name: Name of the operation for tracing
        metadata: Additional metadata to be included in logs and traces

    Example:
        @trace_event("process_user", {"user_type": "admin"})
        def process_user(user_id: int):
            ...
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Prepare metadata for logging and tracing
            trace_data = {
                "operation": operation_name,
                **(metadata or {}),
                "function": func.__name__,
            }

            # Start Sentry transaction
            with sentry_sdk.start_transaction(
                op=operation_name,
                name=f"{func.__name__}.{operation_name}",
            ) as transaction:
                try:
                    return _handle_transaction(
                        transaction,
                        operation_name,
                        trace_data,
                        func,
                        args,
                        kwargs,
                    )
                except Exception as e:
                    # Log error with full context
                    logger.error(
                        f"failed_{operation_name}",
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True,
                    )
                    transaction.set_status("internal_error")
                    raise

        return wrapper
    return decorator
