from functools import wraps

import sentry_sdk


def sentry_tracing(transaction_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(op="task", name=transaction_name) as transaction:
                try:
                    result = func(*args, **kwargs)
                    transaction.set_status("ok")
                    return result
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    transaction.set_status("internal_error")
                    raise

        return wrapper

    return decorator
