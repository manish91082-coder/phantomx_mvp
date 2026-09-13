from __future__ import annotations

from dataclasses import dataclass


class StaleDataError(RuntimeError):
    """Raised when market data is too old to be used for a decision."""


@dataclass(frozen=True)
class FreshnessPolicy:
    max_block_lag: int = 2

    def __post_init__(self) -> None:
        if self.max_block_lag < 0:
            raise ValueError("max_block_lag must be non-negative")


@dataclass(frozen=True)
class Observation:
    observed_block: int
    value: object


class FreshnessGuard:
    def __init__(self, policy: FreshnessPolicy) -> None:
        self._policy = policy

    def assert_fresh(self, observation: Observation, current_block: int) -> None:
        if current_block < observation.observed_block:
            raise StaleDataError("current block is behind observed block")
        if current_block - observation.observed_block > self._policy.max_block_lag:
            raise StaleDataError(
                f"observation is stale by {current_block - observation.observed_block} blocks"
            )
