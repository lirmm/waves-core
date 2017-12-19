import functools


def log_exception(logger):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur

    @param logger: The logging object
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # log the log_exception
                err = "Exception [{}] in  {}".format(func.__name__, e.message)
                logger.exception(err)
                # re-raise the log_exception
                raise

        return wrapper

    return decorator