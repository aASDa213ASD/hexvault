from __future__ import annotations

import threading
import time

from src.lcu.client import accept_ready_check, get_matchmaking_search_state


class AutoAcceptService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._running = False
        self._last_state: str | None = None
        self._last_error: str | None = None
        self._accepted_count = 0
        self._last_accept_at: float | None = None

    def start(self) -> bool:
        with self._lock:
            if self._running: return False

            self._stop_event = threading.Event()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._running = True
            self._last_error = None
            self._thread.start()
            
            return True

    def stop(self) -> bool:
        thread_to_join: threading.Thread | None = None
        with self._lock:
            if not self._running: return False
            self._stop_event.set()
            thread_to_join = self._thread

        if thread_to_join and thread_to_join.is_alive():
            thread_to_join.join(timeout=3.0)

        with self._lock:
            self._running = False
            self._thread = None
        
        return True

    def status(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "last_state": self._last_state,
                "last_error": self._last_error,
                "accepted_count": self._accepted_count,
                "last_accept_at": self._last_accept_at,
            }

    def _set_state(self, **values: object) -> None:
        with self._lock:
            for key, value in values.items():
                setattr(self, f"_{key}", value)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                state = get_matchmaking_search_state()
                self._set_state(last_state=state)

                if state == "Found":
                    result = accept_ready_check()
                    if not result:
                        self._set_state(last_error="LCU unavailable")
                    elif result.get("ok"):
                        with self._lock:
                            next_count = self._accepted_count + 1
                        self._set_state(
                            accepted_count=next_count,
                            last_accept_at=time.time(),
                            last_error=None,
                        )
                    else:
                        self._set_state(
                            last_error=f"Accept failed (status {result.get('status')})"
                        )
                    time.sleep(1.0)
                    continue

                self._set_state(last_error=None)
                time.sleep(1.0)
            except Exception as exc:  # noqa: BLE001
                self._set_state(last_error=str(exc))
                time.sleep(1.0)

        with self._lock:
            self._running = False
            self._thread = None


auto_accept_service = AutoAcceptService()
