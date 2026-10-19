from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from api.core.config import get_settings
from api.core.security import utc_now_iso


@dataclass
class Packet:
    seq: int
    envelope: dict[str, Any]


class ChatPacketQueue:
    """Per-chat outbound packet buffer. WS flushers consume; runs only enqueue."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self._lock = threading.RLock()
        self._packets: deque[Packet] = deque()
        self._next_seq = 1
        self._ack_seq = 0
        self._epoch = 0
        self._cond = threading.Condition(self._lock)
        self._last_activity = time.monotonic()

    @property
    def epoch(self) -> int:
        with self._lock:
            return self._epoch

    def fence(self) -> int:
        """Clear queue and bump epoch (e.g. after rollback)."""
        with self._lock:
            self._packets.clear()
            self._epoch += 1
            self._next_seq = 1
            self._ack_seq = 0
            self._cond.notify_all()
            return self._epoch

    def enqueue(self, type_: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        settings = get_settings()
        with self._lock:
            seq = self._next_seq
            self._next_seq += 1
            envelope = {
                "v": 1,
                "type": type_,
                "id": str(uuid.uuid4()),
                "agent_id": self.agent_id,
                "seq": seq,
                "ts": utc_now_iso(),
                "payload": payload or {},
                "epoch": self._epoch,
            }
            self._packets.append(Packet(seq=seq, envelope=envelope))
            self._last_activity = time.monotonic()
            # Bound memory: drop oldest undelivered when over cap
            max_n = settings.packet_queue_max_packets
            while len(self._packets) > max_n:
                self._packets.popleft()
            self._cond.notify_all()
            return envelope

    def ack(self, seq: int) -> None:
        with self._lock:
            if seq > self._ack_seq:
                self._ack_seq = seq
            while self._packets and self._packets[0].seq <= self._ack_seq:
                self._packets.popleft()
            self._last_activity = time.monotonic()

    def snapshot_undelivered(self, after_seq: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            floor = max(after_seq, self._ack_seq)
            return [p.envelope for p in self._packets if p.seq > floor]

    def wait_new(self, after_seq: int, timeout: float = 1.0) -> list[dict[str, Any]]:
        with self._cond:
            self._cond.wait(timeout=timeout)
            floor = max(after_seq, self._ack_seq)
            return [p.envelope for p in self._packets if p.seq > floor]

    def stats(self) -> dict[str, Any]:
        with self._lock:
            last_seq = self._next_seq - 1
            return {
                "last_seq": last_seq,
                "ack_seq": self._ack_seq,
                "backlog_count": len(self._packets),
                "epoch": self._epoch,
            }

    def trim_if_idle(self, ttl_seconds: int) -> bool:
        with self._lock:
            if time.monotonic() - self._last_activity > ttl_seconds and not self._packets:
                return True
            return False
