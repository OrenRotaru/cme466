from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from cv_pipeline_lab.core.executor import PipelineExecutor
from cv_pipeline_lab.core.registry import create_default_registry
from cv_pipeline_lab.core.types import EdgeModel, NodeModel, PipelineModel


def _sample_path(tmp_path: Path) -> Path:
    img = np.zeros((120, 180, 3), dtype=np.uint8)
    cv2.rectangle(img, (30, 20), (150, 100), (220, 220, 220), -1)
    path = tmp_path / "sample.jpg"
    ok = cv2.imwrite(str(path), img)
    assert ok
    return path


def test_incremental_run_recomputes_changed_and_downstream_only(tmp_path: Path) -> None:
    image_path = _sample_path(tmp_path)
    registry = create_default_registry()
    executor = PipelineExecutor(registry)

    pipeline = PipelineModel(
        nodes=[
            NodeModel(id="in", block_type="ImageInput", title="Input", x=0, y=0, params={"image_path": str(image_path)}),
            NodeModel(id="g", block_type="GrayConvert", title="Gray", x=100, y=0, params={}),
            NodeModel(
                id="t",
                block_type="SimpleThreshold",
                title="Threshold",
                x=200,
                y=0,
                params={"thresh": 120, "max_value": 255, "type": "binary", "pre_blur": 1, "otsu": False},
            ),
            NodeModel(id="out", block_type="ImageOutputPreview", title="Out", x=300, y=0, params={}),
        ],
        edges=[
            EdgeModel(id="e1", src_node="in", src_port="image", dst_node="g", dst_port="image"),
            EdgeModel(id="e2", src_node="g", src_port="image", dst_node="t", dst_port="image"),
            EdgeModel(id="e3", src_node="t", src_port="image", dst_node="out", dst_port="image"),
        ],
    )

    first = executor.run(pipeline)
    assert not first.validation_errors
    assert first.node_results["out"].error is None

    pipeline.nodes[2].params["thresh"] = 80
    second = executor.run_incremental(pipeline, changed_nodes={"t"}, previous_result=first)
    assert not second.validation_errors
    assert second.node_results["t"].error is None
    assert second.node_results["out"].error is None
    assert any(log.startswith("[cache] Input (in)") for log in second.logs)
    assert any(log.startswith("[cache] Gray (g)") for log in second.logs)
    assert any(log.startswith("[ok] Threshold (t)") for log in second.logs)
