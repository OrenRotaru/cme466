from __future__ import annotations

from cv_pipeline_lab.core.graph import topological_sort
from cv_pipeline_lab.core.registry import BlockRegistry
from cv_pipeline_lab.core.types import PipelineModel


def node_snippet(registry: BlockRegistry, block_type: str, params: dict) -> str:
    return registry.to_snippet(block_type, params)


def pipeline_snippet(pipeline: PipelineModel, registry: BlockRegistry) -> str:
    node_by_id = {n.id: n for n in pipeline.nodes}
    lines: list[str] = ["# Pipeline block snippets"]
    try:
        order = topological_sort(pipeline)
    except Exception:  # noqa: BLE001
        order = [n.id for n in pipeline.nodes]
    for nid in order:
        node = node_by_id[nid]
        lines.append("")
        lines.append(f"# Node {node.id}: {node.title} ({node.block_type})")
        lines.append(node_snippet(registry, node.block_type, node.params))
    return "\n".join(lines)
