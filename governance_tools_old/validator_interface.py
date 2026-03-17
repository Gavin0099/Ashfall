#!/usr/bin/env python3
"""
Shared validator interface for external domain validators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field


@dataclass
class ValidatorResult:
    ok: bool
    rule_ids: list[str]
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence_summary: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class DomainValidator(ABC):
    @property
    @abstractmethod
    def rule_ids(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def validate(self, payload: dict) -> ValidatorResult:
        raise NotImplementedError
