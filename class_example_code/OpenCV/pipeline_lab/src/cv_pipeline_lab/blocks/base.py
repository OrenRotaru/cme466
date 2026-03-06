from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from cv_pipeline_lab.core.types import BlockSpec, RunContext


class BlockBase(ABC):
    @classmethod
    @abstractmethod
    def spec(cls) -> BlockSpec:
        raise NotImplementedError

    @abstractmethod
    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        return f"# {cls.spec().title}\n# params: {params}"
