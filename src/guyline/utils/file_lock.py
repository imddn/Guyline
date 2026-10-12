"""Cross-platform exclusive file-lock helpers.

Used to serialise read-modify-write sequences on shared JSON registries
(credentials, settings, cron, memory index, swarm mailbox). Pair with
:func:`guyline.utils.fs.atomic_write_text` to make each critical section
both race-free and crash-safe.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from guyline.platforms import PlatformName, get_platform


class SwarmLockError(RuntimeError):
    """Base error for file-lock failures."""


class SwarmLockUnavailableError(SwarmLockError):
    """Raised when file locking is unavailable on the current platform."""


@contextmanager
def exclusive_file_lock(
    lock_path: Path,
    *,
    platform_name: PlatformName | None = None,
) -> Iterator[None]:
    """Acquire an exclusive file lock for the duration of the context."""
    resolved_platform = platform_name or get_platform()
    if resolved_platform == "windows":
        with _exclusive_windows_lock(lock_path):
            yield
        return
    if resolved_platform in {"macos", "linux", "wsl"}:
        with _exclusive_posix_lock(lock_path):
            yield
        return
    raise SwarmLockUnavailableError(
        f"file locking is not supported on platform {resolved_platform!r}"
    )


@contextmanager
def exclusive_file_lock_fd(
    lock_fd: int,
    *,
    platform_name: PlatformName | None = None,
) -> Iterator[None]:
    """Lock an already-open descriptor without reopening its path."""

    resolved_platform = platform_name or get_platform()
    if resolved_platform == "windows":
        with _lock_windows_fd(lock_fd):
            yield
        return
    if resolved_platform in {"macos", "linux", "wsl"}:
        with _lock_posix_fd(lock_fd):
            yield
        return
    raise SwarmLockUnavailableError(
        f"file locking is not supported on platform {resolved_platform!r}"
    )


@contextmanager
def _lock_posix_fd(lock_fd: int) -> Iterator[None]:
    try:
        import fcntl
    except ImportError as exc:
        raise SwarmLockUnavailableError(f"fcntl not available: {exc}") from exc

    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    try:
        yield
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)


@contextmanager
def _lock_windows_fd(lock_fd: int) -> Iterator[None]:
    try:
        import msvcrt
    except ImportError as exc:
        raise SwarmLockUnavailableError(f"msvcrt not available: {exc}") from exc

    os.lseek(lock_fd, 0, os.SEEK_SET)
    if os.fstat(lock_fd).st_size == 0:
        os.write(lock_fd, b"\0")
        os.fsync(lock_fd)
    os.lseek(lock_fd, 0, os.SEEK_SET)
    msvcrt.locking(lock_fd, msvcrt.LK_LOCK, 1)
    try:
        yield
    finally:
        os.lseek(lock_fd, 0, os.SEEK_SET)
        msvcrt.locking(lock_fd, msvcrt.LK_UNLCK, 1)


@contextmanager
def _exclusive_posix_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.touch(exist_ok=True)
    with lock_path.open("a+b") as lock_file, _lock_posix_fd(lock_file.fileno()):
        yield


@contextmanager
def _exclusive_windows_lock(lock_path: Path) -> Iterator[None]:
    try:
        import msvcrt
    except ImportError as exc:
        raise SwarmLockUnavailableError(f"msvcrt not available: {exc}") from exc

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        # msvcrt.locking requires a byte range to exist and the file be open
        # in binary mode. Lock the first byte for the lifetime of the
        # critical section.
        lock_file.seek(0)
        if lock_path.stat().st_size == 0:
            lock_file.write(b"\0")
            lock_file.flush()
        lock_file.seek(0)
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
