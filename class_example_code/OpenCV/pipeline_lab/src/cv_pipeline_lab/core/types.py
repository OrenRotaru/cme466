from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np

PortType = Literal["image", "mask", "detections", "feature_vector", "meta"]
ParamType = Literal["int", "float", "bool", "enum", "str"]


@dataclass(slots=True)
class Detection:
    bbox: tuple[int, int, int, int]
    label: str
    score: float = 1.0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PortSpec:
    name: str
    type: PortType
    description: str = ""


@dataclass(slots=True)
class ParamSpec:
    name: str
    type: ParamType
    default: Any
    label: str | None = None
    min_value: float | int | None = None
    max_value: float | int | None = None
    step: float | int | None = None
    options: list[str] = field(default_factory=list)
    help_text: str = ""
    visible_if: dict[str, list[Any]] = field(default_factory=dict)


@dataclass(slots=True)
class BlockSpec:
    type_name: str
    title: str
    category: str
    input_ports: list[PortSpec] = field(default_factory=list)
    output_ports: list[PortSpec] = field(default_factory=list)
    params: list[ParamSpec] = field(default_factory=list)
    description: str = ""
    is_concept: bool = False


@dataclass(slots=True)
class NodeModel:
    id: str
    block_type: str
    title: str
    x: float
    y: float
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass(slots=True)
class EdgeModel:
    id: str
    src_node: str
    src_port: str
    dst_node: str
    dst_port: str


@dataclass(slots=True)
class NoteModel:
    id: str
    title: str
    markdown: str
    x: float = 0.0
    y: float = 0.0


@dataclass(slots=True)
class CanvasState:
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0


@dataclass(slots=True)
class PipelineModel:
    version: str = "1.0"
    nodes: list[NodeModel] = field(default_factory=list)
    edges: list[EdgeModel] = field(default_factory=list)
    canvas: CanvasState = field(default_factory=CanvasState)
    notes: list[NoteModel] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RunContext:
    pipeline_dir: Path
    image_override: str | None = None
    artifacts_dir: Path | None = None


DataValue = np.ndarray | list[Detection] | np.ndarray | dict[str, Any] | Any


@dataclass(slots=True)
class NodeRunResult:
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    skipped: bool = False


@dataclass(slots=True)
class ExecutionResult:
    order: list[str] = field(default_factory=list)
    node_results: dict[str, NodeRunResult] = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        if self.validation_errors:
            return False
        return all(r.error is None for r in self.node_results.values())
