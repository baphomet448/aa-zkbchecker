"""Cooperative cancellation of running checks, shared by the views
(which set the flags) and the Celery task (which reads them)."""

from django.core.cache import cache

# The browser polls every couple of seconds. Background tabs get their
# timers throttled to about once a minute, so the heartbeat must outlive that.
ALIVE_TTL = 120
STATE_TTL = 3600


def _alive_key(task_id: str) -> str:
    return f"zkbchecker:alive:{task_id}"


def _cancel_key(task_id: str) -> str:
    return f"zkbchecker:cancel:{task_id}"


def _active_key(user_id: int) -> str:
    return f"zkbchecker:active:{user_id}"


def touch(task_id: str) -> None:
    """Heartbeat: somebody is still watching this task."""
    cache.set(_alive_key(task_id), 1, ALIVE_TTL)


def cancel(task_id: str) -> None:
    cache.set(_cancel_key(task_id), 1, STATE_TTL)


def register(user_id: int, task_id: str) -> None:
    """Make task_id the user's active check; a previous one is cancelled."""
    previous = cache.get(_active_key(user_id))
    if previous and previous != task_id:
        cancel(previous)
    cache.set(_active_key(user_id), task_id, STATE_TTL)
    touch(task_id)


def cancel_active(user_id: int) -> None:
    """Cancel whatever check the user currently has running."""
    task_id = cache.get(_active_key(user_id))
    if task_id:
        cancel(task_id)


def should_stop(task_id: str) -> bool:
    return bool(cache.get(_cancel_key(task_id))) or not cache.get(_alive_key(task_id))


def release(user_id: int, task_id: str) -> None:
    """Clean up after a task ended, however it ended."""
    if cache.get(_active_key(user_id)) == task_id:
        cache.delete(_active_key(user_id))
    cache.delete_many([_alive_key(task_id), _cancel_key(task_id)])