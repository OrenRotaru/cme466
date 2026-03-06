from __future__ import annotations

from cv_pipeline_lab.core.serialization import pipeline_from_dict, pipeline_to_dict
from cv_pipeline_lab.core.types import CanvasState, EdgeModel, NodeModel, NoteModel, PipelineModel


def test_roundtrip_serialization() -> None:
    pipeline = PipelineModel(
        version="1.0",
        nodes=[
            NodeModel(id="n1", block_type="ImageInput", title="Input", x=10, y=20, params={"image_path": "img.jpg"}),
            NodeModel(id="n2", block_type="DenoiseBlur", title="Blur", x=30, y=40, params={"method": "gaussian"}),
        ],
        edges=[
            EdgeModel(id="e1", src_node="n1", src_port="image", dst_node="n2", dst_port="image"),
        ],
        canvas=CanvasState(zoom=1.5, pan_x=10, pan_y=12),
        notes=[NoteModel(id="t1", title="note", markdown="hello", x=1, y=2)],
        metadata={"app_version": "0.1.0"},
    )

    d = pipeline_to_dict(pipeline)
    back = pipeline_from_dict(d)

    assert back.version == "1.0"
    assert len(back.nodes) == 2
    assert len(back.edges) == 1
    assert len(back.notes) == 1
    assert back.canvas.zoom == 1.5
