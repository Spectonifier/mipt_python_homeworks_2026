import json
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


def _validate_positive_integer(number: int) -> bool:
    return isinstance(number, int) and number > 0


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    func_name: str
    block_time: datetime

    def __init__(self, message: str, function: CallableWithMeta[..., Any], blocked_since: datetime) -> None:
        super().__init__(message)
        self.func_name: str = f"{function.__module__}.{function.__name__}"
        self.block_time: datetime = blocked_since


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ) -> None:
        self._validate_input(critical_count, time_to_recover)

        self.critical_count: int = critical_count
        self.time_to_recover: int = time_to_recover
        self.triggers_on: type[Exception] = triggers_on
        self.failure_count: int = 0
        self.blocked_since: datetime | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> Callable[P, R_co]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            self._ensure_not_blocked(func)
            return self._call_with_breaker(func, *args, **kwargs)

        return wrapper

    def _validate_input(self, critical_count: int, time_to_recover: int) -> None:
        exceptions: list[ValueError] = []

        if not _validate_positive_integer(critical_count):
            exceptions.append(ValueError(INVALID_CRITICAL_COUNT))
        if not _validate_positive_integer(time_to_recover):
            exceptions.append(ValueError(INVALID_RECOVERY_TIME))

        if exceptions:
            raise ExceptionGroup(VALIDATIONS_FAILED, exceptions)

    def _ensure_not_blocked(self, func: CallableWithMeta[P, R_co]) -> None:
        if self.blocked_since is None:
            return
        if (datetime.now(UTC) - self.blocked_since).total_seconds() < self.time_to_recover:
            raise BreakerError(TOO_MUCH, func, self.blocked_since)
        self.blocked_since = None

    def _call_with_breaker(
        self,
        func: CallableWithMeta[P, R_co],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R_co:
        try:
            result = func(*args, **kwargs)
        except self.triggers_on as exception:
            self._register_failure(func, exception)
            raise
        else:
            self.failure_count = 0
            return result

    def _register_failure(
        self,
        func: CallableWithMeta[P, R_co],
        exception: Exception,
    ) -> None:
        self.failure_count += 1
        if self.failure_count < self.critical_count:
            return
        self.failure_count = 0
        self.blocked_since = datetime.now(UTC)
        raise BreakerError(TOO_MUCH, func, self.blocked_since) from exception


def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
