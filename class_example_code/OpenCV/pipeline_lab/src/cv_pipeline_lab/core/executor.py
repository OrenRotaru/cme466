from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from cv_pipeline_lab.core.graph import inbound_edges_by_node, outbound_edges_by_node, topological_sort, validate_pipeline
from cv_pipeline_lab.core.registry import BlockRegistry
from cv_pipeline_lab.core.types import (
    ExecutionResult,
    NodeRunResult,
    PipelineModel,
    RunContext,
)


@dataclass(slots=True)
class PipelineExecutor:
    registry: BlockRegistry

    def run(
        self,
        pipeline: PipelineModel,
        image_override: str | None = None,
        pipeline_path: str | None = None,
    ) -> ExecutionResult:
        result = ExecutionResult()
        result.validation_errors = validate_pipeline(pipeline, self.registry)
        if result.validation_errors:
            return result

        node_by_id = {n.id: n for n in pipeline.nodes}
        inbound = inbound_edges_by_node(pipeline.edges)

        try:
            order = topological_sort(pipeline)
        except ValueError as exc:
            result.validation_errors = [str(exc)]
            return result

        result.order = order

        pipeline_dir = Path(pipeline_path).expanduser().resolve().parent if pipeline_path else Path.cwd()
        ctx = RunContext(pipeline_dir=pipeline_dir, image_override=image_override)

        for node_id in order:
            node = node_by_id[node_id]
            block = self.registry.get(node.block_type)
            spec = block.spec()

            if not node.enabled:
                result.node_results[node_id] = NodeRunResult(outputs={}, skipped=True)
                result.logs.append(f"[skip] {node.title} ({node.id}) disabled")
                continue

            inputs: dict[str, Any] = {}
            for edge in inbound.get(node_id, []):
                src_res = result.node_results.get(edge.src_node)
                if src_res is None or src_res.error is not None:
                    continue
                if edge.src_port not in src_res.outputs:
                    continue
                val = src_res.outputs[edge.src_port]
                if isinstance(val, np.ndarray):
                    val = val.copy()
                inputs[edge.dst_port] = val

            missing = [p.name for p in spec.input_ports if p.name not in inputs]
            if missing and not spec.is_concept:
                err = f"Missing inputs for {node.title} ({node.id}): {', '.join(missing)}"
                result.node_results[node_id] = NodeRunResult(error=err)
                result.logs.append(f"[error] {err}")
                continue

            try:
                outputs = block.run(inputs, node.params, ctx)
                outputs = outputs or {}
                result.node_results[node_id] = NodeRunResult(outputs=outputs)
                result.logs.append(f"[ok] {node.title} ({node.id})")
            except Exception as exc:  # noqa: BLE001
                err = f"{type(exc).__name__}: {exc}"
                result.node_results[node_id] = NodeRunResult(error=err)
                result.logs.append(f"[error] {node.title} ({node.id}): {err}")

        return result

    def run_incremental(
        self,
        pipeline: PipelineModel,
        changed_nodes: set[str],
        previous_result: ExecutionResult | None,
        image_override: str | None = None,
        pipeline_path: str | None = None,
    ) -> ExecutionResult:
        # If we do not have a valid baseline, fall back to full run.
        if previous_result is None or not changed_nodes:
            return self.run(pipeline, image_override=image_override, pipeline_path=pipeline_path)

        result = ExecutionResult()
        result.validation_errors = validate_pipeline(pipeline, self.registry)
        if result.validation_errors:
            return result

        node_by_id = {n.id: n for n in pipeline.nodes}
        inbound = inbound_edges_by_node(pipeline.edges)
        outbound = outbound_edges_by_node(pipeline.edges)

        try:
            order = topological_sort(pipeline)
        except ValueError as exc:
            result.validation_errors = [str(exc)]
            return result
        result.order = order

        # Run changed nodes and all downstream descendants.
        affected: set[str] = set()
        stack = [nid for nid in changed_nodes if nid in node_by_id]
        while stack:
            nid = stack.pop()
            if nid in affected:
                continue
            affected.add(nid)
            for edge in outbound.get(nid, []):
                stack.append(edge.dst_node)

        # No valid changed IDs -> reuse full previous result if possible.
        if not affected:
            return self.run(pipeline, image_override=image_override, pipeline_path=pipeline_path)

        # Reuse unaffected upstream results from cache when valid; otherwise fallback.
        for nid in order:
            if nid in affected:
                continue
            prev = previous_result.node_results.get(nid)
            if prev is None or prev.error is not None:
                return self.run(pipeline, image_override=image_override, pipeline_path=pipeline_path)
            result.node_results[nid] = NodeRunResult(outputs=dict(prev.outputs), error=None, skipped=prev.skipped)
            result.logs.append(f"[cache] {node_by_id[nid].title} ({nid})")

        pipeline_dir = Path(pipeline_path).expanduser().resolve().parent if pipeline_path else Path.cwd()
        ctx = RunContext(pipeline_dir=pipeline_dir, image_override=image_override)

        for node_id in order:
            if node_id not in affected:
                continue

            node = node_by_id[node_id]
            block = self.registry.get(node.block_type)
            spec = block.spec()

            if not node.enabled:
                result.node_results[node_id] = NodeRunResult(outputs={}, skipped=True)
                result.logs.append(f"[skip] {node.title} ({node.id}) disabled")
                continue

            inputs: dict[str, Any] = {}
            for edge in inbound.get(node_id, []):
                src_res = result.node_results.get(edge.src_node)
                if src_res is None or src_res.error is not None:
                    continue
                if edge.src_port not in src_res.outputs:
                    continue
                val = src_res.outputs[edge.src_port]
                if isinstance(val, np.ndarray):
                    val = val.copy()
                inputs[edge.dst_port] = val

            missing = [p.name for p in spec.input_ports if p.name not in inputs]
            if missing and not spec.is_concept:
                err = f"Missing inputs for {node.title} ({node.id}): {', '.join(missing)}"
                result.node_results[node_id] = NodeRunResult(error=err)
                result.logs.append(f"[error] {err}")
                continue

            try:
                outputs = block.run(inputs, node.params, ctx)
                outputs = outputs or {}
                result.node_results[node_id] = NodeRunResult(outputs=outputs)
                result.logs.append(f"[ok] {node.title} ({node.id})")
            except Exception as exc:  # noqa: BLE001
                err = f"{type(exc).__name__}: {exc}"
                result.node_results[node_id] = NodeRunResult(error=err)
                result.logs.append(f"[error] {node.title} ({node.id}): {err}")

        return result
