"""Environment-owned scheduling and settlement; values must be JSON serializable.

create(config) opens one session. observe() is read-only. submit() binds an
idempotency key and expected revision; acceptance is distinct from settlement.
poll(after) returns settled outcomes, including delayed async outcomes. A
terminal status requires no more agent actions. close() is idempotent and must
confirm cleanup or raise. No optional capability is implied by this protocol.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass(frozen=True)
class Capabilities:
    synchronous: bool = True
    asynchronous: bool = False
    multi_agent: bool = True
    simultaneous_actions: bool = False
    snapshot: bool = False
    clock: str = 'turn'


@dataclass(frozen=True)
class Decision:
    agent: str
    observation: Any
    legal_actions: tuple[Any, ...]
    constraints: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Frame:
    revision: int
    decisions: tuple[Decision, ...]


@dataclass(frozen=True)
class Status:
    terminated: bool = False
    truncated: bool = False
    reason: str | None = None
    results: dict = field(default_factory=dict)

    @property
    def done(self):
        return self.terminated or self.truncated


@dataclass(frozen=True)
class Resolution:
    cursor: int
    revision: int
    operation: str
    effects: dict


@dataclass(frozen=True)
class Submission:
    operation: str
    status: str  # accepted | rejected | pending; never synonymous with resolved
    revision: int
    reason: str | None = None
    outcomes: tuple[Resolution, ...] = ()


class EnvironmentSession(Protocol):
    capabilities: Capabilities
    def observe(self) -> Frame: ...
    def submit(self, actions: dict[str, Any], *, operation: str, expected_revision: int) -> Submission: ...
    def poll(self, after: int = 0) -> tuple[Resolution, ...]: ...
    def status(self) -> Status: ...
    def close(self) -> None: ...


EnvironmentFactory = Callable[[dict], EnvironmentSession]
