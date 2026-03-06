from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cv_pipeline_lab.core.types import CanvasState, EdgeModel, NodeModel, NoteModel, PipelineModel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def pipeline_to_dict(pipeline: PipelineModel) -> dict[str, Any]:
    nodes = [asdict(n) for n in sorted(pipeline.nodes, key=lambda n: n.id)]
    edges = [asdict(e) for e in sorted(pipeline.edges, key=lambda e: e.id)]
    notes = [asdict(n) for n in sorted(pipeline.notes, key=lambda n: n.id)]

    metadata = dict(pipeline.metadata)
    metadata.setdefault("created_at", _now_iso())

    return {
        "version": pipeline.version,
        "nodes": nodes,
        "edges": edges,
        "canvas": asdict(pipeline.canvas),
        "notes": notes,
        "metadata": metadata,
    }


def pipeline_from_dict(data: dict[str, Any]) -> PipelineModel:
    nodes = [NodeModel(**n) for n in data.get("nodes", [])]
    edges = [EdgeModel(**e) for e in data.get("edges", [])]
    notes = [NoteModel(**n) for n in data.get("notes", [])]

    canvas_data = data.get("canvas", {})
    canvas = CanvasState(
        zoom=float(canvas_data.get("zoom", 1.0)),
        pan_x=float(canvas_data.get("pan_x", 0.0)),
        pan_y=float(canvas_data.get("pan_y", 0.0)),
    )

    metadata = dict(data.get("metadata", {}))
    metadata.setdefault("created_at", _now_iso())

    return PipelineModel(
        version=str(data.get("version", "1.0")),
        nodes=nodes,
        edges=edges,
        canvas=canvas,
        notes=notes,
        metadata=metadata,
    )


def save_pipeline(pipeline: PipelineModel, path: str | Path) -> None:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    d = pipeline_to_dict(pipeline)
    p.write_text(json.dumps(d, indent=2, sort_keys=True))


def load_pipeline(path: str | Path) -> PipelineModel:
    p = Path(path).expanduser()
    data = json.loads(p.read_text())
    return pipeline_from_dict(data)
