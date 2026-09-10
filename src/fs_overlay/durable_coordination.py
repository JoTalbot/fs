"""Cross-platform durable admission coordination adapters.

This module provides a small process-scoped file-lock implementation for the
``DurableAdmissionCoordinator`` production boundary. It coordinates writers
but does not make the journal write transactional with unrelated storage, and
it does not recover or steal a lock after a crashed process. Deployments that
need transactional durability should provide a database or equivalent
transaction coordinator instead.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
import errno
import hashlib
import os
from pathlib import Path
import time
from typing import IO, Callable

from .production_adapters import DurableAdmissionCoordinator


class CoordinationTimeout(TimeoutError):
    """Raised when a coordination lock cannot be acquired before its deadline."""


@dataclass(frozen=True)
class _HeldLock(AbstractContextManager[None]):
    handle: IO[bytes]
    unlock: Callable[[], None]

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            self.unlock()
        finally:
            self.handle.close()


class FileAdmissionCoordinator(DurableAdmissionCoordinator):
    """Coordinate admissions between processes using a local lock file.

    The implementation uses ``fcntl.flock`` on POSIX and ``msvcrt.locking`` on
    Windows. Lock files are deliberately retained, because removing a lock
    path while another process may still hold an OS lock creates a race.

    A crashed process releases the OS-level lock automatically. There is no
    stale-lock deletion or lock stealing. ``timeout`` therefore means only
    "wait this long for the OS lock", never "assume the owner is dead".
    """

    def __init__(self, directory: str | Path, *, timeout: float = 5.0, poll_interval: float = 0.01):
        if timeout < 0:
            raise ValueError("timeout must be non-negative")
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        self.directory = Path(directory)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, resource_id: str) -> Path:
        if not resource_id:
            raise ValueError("resource_id must not be empty")
        digest = hashlib.sha256(resource_id.encode("utf-8")).hexdigest()
        return self.directory / f"{digest}.lock"

    def acquire(self, resource_id: str) -> AbstractContextManager[None]:
        path = self._path(resource_id)
        handle = open(path, "a+b")
        if os.name == "nt" and handle.seek(0, 2) == 0:
            handle.write(b"\0")
            handle.flush()
        deadline = time.monotonic() + self.timeout
        try:
            while True:
                try:
                    unlock = self._try_lock(handle)
                    return _HeldLock(handle, unlock)
                except (BlockingIOError, OSError) as exc:
                    if not self._is_would_block(exc):
                        raise
                    if time.monotonic() >= deadline:
                        raise CoordinationTimeout(
                            f"timed out acquiring coordination lock for {resource_id!r}"
                        ) from None
                    time.sleep(self.poll_interval)
        except Exception:
            handle.close()
            raise

    @staticmethod
    def _is_would_block(exc: OSError) -> bool:
        return isinstance(exc, BlockingIOError) or getattr(exc, "errno", None) in {
            errno.EACCES,
            errno.EAGAIN,
        }

    @staticmethod
    def _try_lock(handle: IO[bytes]) -> Callable[[], None]:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                if getattr(exc, "errno", None) not in {errno.EACCES, errno.EAGAIN}:
                    raise
                raise BlockingIOError from None

            def unlock() -> None:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

            return unlock

        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        def unlock() -> None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

        return unlock
