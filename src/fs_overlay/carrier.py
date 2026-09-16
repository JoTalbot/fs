"""Explicit carrier boundary for filesystem/storage placements."""
from __future__ import annotations

import os
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Protocol


class CarrierAdapter(Protocol):
    """A carrier owns approved storage locations; it never expands their scope."""
    name: str
    root: Path

    def put(self, relative_name: str, data: bytes) -> str: ...
    def get(self, relative_name: str) -> bytes: ...
    def delete(self, relative_name: str) -> None: ...
    def contains(self, relative_name: str) -> bool: ...


class LocalDirectoryCarrier:
    """POSIX carrier using stable directory descriptors and no-follow traversal.

    Windows is intentionally unsupported until a native reparse-point-safe
    multi-component implementation exists; silently falling back to pathname
    operations would recreate the isolation race this adapter is meant to close.
    """
    name = "local-directory"

    def __init__(self, root: str | Path):
        if os.name == "nt":
            raise NotImplementedError("race-resistant LocalDirectoryCarrier is not implemented on Windows")
        if os.open not in os.supports_dir_fd or not hasattr(os, "O_NOFOLLOW"):
            raise NotImplementedError("carrier requires POSIX dirfd and O_NOFOLLOW support")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW
        self._root_fd = os.open(self.root, flags)
        if not stat.S_ISDIR(os.fstat(self._root_fd).st_mode):
            os.close(self._root_fd)
            self._root_fd = None
            raise NotADirectoryError(str(self.root))

    def __del__(self) -> None:
        fd = getattr(self, "_root_fd", None)
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
            self._root_fd = None

    @staticmethod
    def _parts(relative_name: str) -> tuple[str, ...]:
        if not isinstance(relative_name, str) or not relative_name or relative_name.startswith("/"):
            raise ValueError("carrier name must be a non-empty relative path")
        parts = tuple(relative_name.split("/"))
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError("carrier name must not contain empty, '.' or '..' components")
        return parts

    def _open_directory(self, name: str, parent_fd: int) -> int:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW
        fd = os.open(name, flags, dir_fd=parent_fd)
        try:
            if not stat.S_ISDIR(os.fstat(fd).st_mode):
                raise NotADirectoryError(name)
            return fd
        except Exception:
            os.close(fd)
            raise

    @contextmanager
    def _parent_fd(self, relative_name: str) -> Iterator[tuple[int, str]]:
        parts = self._parts(relative_name)
        fd = os.dup(self._root_fd)
        try:
            for part in parts[:-1]:
                try:
                    next_fd = self._open_directory(part, fd)
                except FileNotFoundError:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                    next_fd = self._open_directory(part, fd)
                os.close(fd)
                fd = next_fd
            yield fd, parts[-1]
        finally:
            os.close(fd)

    @staticmethod
    def _fsync_directory_fd(fd: int) -> None:
        os.fsync(fd)

    @staticmethod
    def _new_temp_name() -> str:
        return f".carrier-tmp-{os.urandom(16).hex()}"

    def put(self, relative_name: str, data: bytes) -> str:
        with self._parent_fd(relative_name) as (parent_fd, leaf):
            temporary = self._new_temp_name()
            temp_fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent_fd)
            try:
                with os.fdopen(temp_fd, "wb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, leaf, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                self._fsync_directory_fd(parent_fd)
            finally:
                try:
                    os.unlink(temporary, dir_fd=parent_fd)
                except FileNotFoundError:
                    pass
        return relative_name

    def get(self, relative_name: str) -> bytes:
        with self._parent_fd(relative_name) as (parent_fd, leaf):
            fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
            with os.fdopen(fd, "rb") as handle:
                return handle.read()

    def delete(self, relative_name: str) -> None:
        try:
            with self._parent_fd(relative_name) as (parent_fd, leaf):
                try:
                    os.unlink(leaf, dir_fd=parent_fd)
                except FileNotFoundError:
                    return
                self._fsync_directory_fd(parent_fd)
        except FileNotFoundError:
            return

    def contains(self, relative_name: str) -> bool:
        try:
            with self._parent_fd(relative_name) as (parent_fd, leaf):
                try:
                    stat_result = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
                except FileNotFoundError:
                    return False
                return stat.S_ISREG(stat_result.st_mode)
        except FileNotFoundError:
            return False
