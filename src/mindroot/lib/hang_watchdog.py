"""Out-of-event-loop diagnostics for a stalled MindRoot asyncio loop.

A daemon thread observes a heartbeat updated by a tiny asyncio task.  If the
heartbeat stops, the thread writes process information and every Python thread's
stack to a bounded file.  It never restarts the process and is not used by any
audio hot path.
"""

from __future__ import annotations

import asyncio
import faulthandler
import signal
import os
import resource
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional


_TRUE = {"1", "true", "yes", "on"}


class HangWatchdog:
    def __init__(self) -> None:
        self.enabled = os.getenv("MR_HANG_WATCHDOG_ENABLED", "1").lower() in _TRUE
        self.log_path = os.getenv("MR_HANG_WATCHDOG_LOG", "/tmp/mindroot_hang_diagnostics.log")
        self.heartbeat_seconds = max(0.25, float(os.getenv("MR_HANG_WATCHDOG_HEARTBEAT_SECONDS", "1")))
        self.stall_seconds = max(self.heartbeat_seconds * 2, float(os.getenv("MR_HANG_WATCHDOG_STALL_SECONDS", "15")))
        self.repeat_seconds = max(5.0, float(os.getenv("MR_HANG_WATCHDOG_REPEAT_SECONDS", "60")))
        self.max_bytes = max(64 * 1024, int(os.getenv("MR_HANG_WATCHDOG_MAX_BYTES", "5242880")))
        self.backups = max(0, int(os.getenv("MR_HANG_WATCHDOG_BACKUPS", "3")))
        self._last_heartbeat = time.monotonic()
        self._last_dump = 0.0
        self._dump_count = 0
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._signal_file = None

    def _install_signal_dump(self) -> None:
        """Allow an external watchdog to request all-thread stacks via SIGUSR1."""
        if not hasattr(signal, "SIGUSR1"):
            return
        try:
            self._rotate()
            self._signal_file = open(self.log_path, "a", buffering=1)
            faulthandler.register(
                signal.SIGUSR1,
                file=self._signal_file,
                all_threads=True,
                chain=False,
            )
        except Exception:
            self._signal_file = None

    def _uninstall_signal_dump(self) -> None:
        if hasattr(signal, "SIGUSR1"):
            try:
                faulthandler.unregister(signal.SIGUSR1)
            except Exception:
                pass
        if self._signal_file is not None:
            try:
                self._signal_file.close()
            except Exception:
                pass
            self._signal_file = None

    async def start(self) -> None:
        if not self.enabled or self._thread is not None:
            return
        self._stop.clear()
        self._last_heartbeat = time.monotonic()
        self._install_signal_dump()
        self._thread = threading.Thread(
            target=self._watch_loop,
            name="mindroot-hang-watchdog",
            daemon=True,
        )
        self._thread.start()
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(), name="mindroot-hang-heartbeat"
        )
        self._write_event("WATCHDOG_STARTED", stall_seconds=self.stall_seconds)

    async def stop(self) -> None:
        self._stop.set()
        task = self._heartbeat_task
        self._heartbeat_task = None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        thread = self._thread
        self._thread = None
        if thread and thread is not threading.current_thread():
            await asyncio.to_thread(thread.join, 2.0)
        self._uninstall_signal_dump()
        self._write_event("WATCHDOG_STOPPED")

    async def _heartbeat_loop(self) -> None:
        while not self._stop.is_set():
            self._last_heartbeat = time.monotonic()
            await asyncio.sleep(self.heartbeat_seconds)

    def _watch_loop(self) -> None:
        check_seconds = min(1.0, max(0.25, self.heartbeat_seconds))
        while not self._stop.wait(check_seconds):
            now = time.monotonic()
            stale = now - self._last_heartbeat
            if stale < self.stall_seconds:
                continue
            if now - self._last_dump < self.repeat_seconds:
                continue
            self._last_dump = now
            self._dump_count += 1
            self._dump_all_threads(stale)

    def _rotate(self) -> None:
        try:
            path = Path(self.log_path)
            if not path.exists() or path.stat().st_size < self.max_bytes:
                return
            if self.backups <= 0:
                path.unlink(missing_ok=True)
                return
            oldest = Path(f"{self.log_path}.{self.backups}")
            oldest.unlink(missing_ok=True)
            for index in range(self.backups - 1, 0, -1):
                source = Path(f"{self.log_path}.{index}")
                if source.exists():
                    source.replace(f"{self.log_path}.{index + 1}")
            path.replace(f"{self.log_path}.1")
        except Exception:
            pass

    def _process_stats(self) -> dict:
        stats = {
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "threads": threading.active_count(),
        }
        try:
            stats["loadavg"] = os.getloadavg()
        except Exception:
            pass
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            stats.update(
                rss_max_kb=usage.ru_maxrss,
                user_cpu_seconds=round(usage.ru_utime, 3),
                system_cpu_seconds=round(usage.ru_stime, 3),
                voluntary_context_switches=usage.ru_nvcsw,
                involuntary_context_switches=usage.ru_nivcsw,
            )
        except Exception:
            pass
        try:
            stats["fd_count"] = len(os.listdir("/proc/self/fd"))
        except Exception:
            pass
        try:
            stats["current_rss_kb"] = int(Path("/proc/self/statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE") // 1024
        except Exception:
            pass
        try:
            stats["job_queue_diagnostics_mtime"] = os.path.getmtime(
                os.getenv("MR_JOB_QUEUE_DIAGNOSTICS_LOG", "/tmp/job_queue_diagnostics.log")
            )
        except Exception:
            pass
        return stats

    def _write_event(self, event: str, **fields) -> None:
        if not self.enabled:
            return
        try:
            self._rotate()
            timestamp = datetime.now().isoformat(timespec="milliseconds")
            details = " ".join(f"{key}={value!r}" for key, value in fields.items())
            with open(self.log_path, "a", buffering=1) as stream:
                stream.write(f"{timestamp} {event} pid={os.getpid()} {details}\n")
        except Exception:
            pass

    def _dump_all_threads(self, stale_seconds: float) -> None:
        try:
            self._rotate()
            timestamp = datetime.now().isoformat(timespec="milliseconds")
            stats = self._process_stats()
            with open(self.log_path, "a", buffering=1) as stream:
                stream.write("\n" + "=" * 88 + "\n")
                stream.write(
                    f"{timestamp} EVENT_LOOP_STALL dump={self._dump_count} "
                    f"heartbeat_stale_seconds={stale_seconds:.3f} stats={stats!r}\n"
                )
                stream.write("All Python thread stacks follow (most recent call first):\n")
                stream.flush()
                faulthandler.dump_traceback(file=stream, all_threads=True)
                stream.write("=" * 88 + "\n")
        except Exception:
            try:
                self._write_event("WATCHDOG_DUMP_FAILED", error=traceback.format_exc())
            except Exception:
                pass


hang_watchdog = HangWatchdog()
