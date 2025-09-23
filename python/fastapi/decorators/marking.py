from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


def marking(func: F) -> F:
    """Mark an endpoint as available for web runtime."""
    setattr(func, "marked", True)
    return func
