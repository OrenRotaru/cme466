from __future__ import annotations

from cv_pipeline_lab.core.graph import topological_sort, validate_pipeline
from cv_pipeline_lab.core.registry import create_default_registry
from cv_pipeline_lab.core.types import EdgeModel, NodeModel, PipelineModel


def test_validate_requires_single_input() -> None:
    registry = create_default_registry()
    pipeline = PipelineModel(
        nodes=[
            NodeModel(id="n1", block_type="ImageInput", title="in1", x=0, y=0, params={"image_path": "a.jpg"}),
            NodeModel(id="n2", block_type="ImageInput", title="in2", x=0, y=0, params={"image_path": "b.jpg"}),
        ],
        edges=[],
    )
    errors = validate_pipeline(pipeline, registry)
    assert any("Exactly one enabled source node" in e for e in errors)


def test_cycle_detection() -> None:
    pipeline = PipelineModel(
        nodes=[
            NodeModel(id="a", block_type="ImageInput", title="a", x=0, y=0, params={"image_path": "x.jpg"}),
            NodeModel(id="b", block_type="GrayConvert", title="b", x=0, y=0, params={}),
            NodeModel(id="c", block_type="ColorConvert", title="c", x=0, y=0, params={}),
        ],
        edges=[
            EdgeModel(id="e1", src_node="a", src_port="image", dst_node="b", dst_port="image"),
            EdgeModel(id="e2", src_node="b", src_port="image", dst_node="c", dst_port="image"),
            EdgeModel(id="e3", src_node="c", src_port="image", dst_node="b", dst_port="image"),
        ],
    )
    try:
        topological_sort(pipeline)
        assert False, "expected cycle error"
    except ValueError as exc:
        assert "cycle" in str(exc).lower()


def test_validate_rejects_image_to_mask_connection() -> None:
    registry = create_default_registry()
    pipeline = PipelineModel(
        nodes=[
            NodeModel(id="in", block_type="ImageInput", title="Input", x=0, y=0, params={"image_path": "x.jpg"}),
            NodeModel(id="m", block_type="BinaryMorphology", title="Morph", x=10, y=10, params={}),
        ],
        edges=[
            EdgeModel(id="e1", src_node="in", src_port="image", dst_node="m", dst_port="mask"),
        ],
    )
    errors = validate_pipeline(pipeline, registry)
    assert any("type mismatch" in e.lower() and "image -> mask" in e.lower() for e in errors)


def test_validate_accepts_single_video_frame_input_source() -> None:
    registry = create_default_registry()
    pipeline = PipelineModel(
        nodes=[
            NodeModel(id="in", block_type="VideoFrameInput", title="Video", x=0, y=0, params={"source": "0"}),
            NodeModel(id="g", block_type="GrayConvert", title="Gray", x=10, y=10, params={}),
        ],
        edges=[EdgeModel(id="e1", src_node="in", src_port="image", dst_node="g", dst_port="image")],
    )
    errors = validate_pipeline(pipeline, registry)
    assert errors == []
