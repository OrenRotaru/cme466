from __future__ import annotations

import ast

from cv_pipeline_lab.core.export_notebook import export_notebook
from cv_pipeline_lab.core.export_python import export_python_script
from cv_pipeline_lab.core.registry import create_default_registry
from cv_pipeline_lab.core.types import EdgeModel, NodeModel, PipelineModel


def _pipeline() -> PipelineModel:
    return PipelineModel(
        nodes=[
            NodeModel(id="n1", block_type="ImageInput", title="Input", x=0, y=0, params={"image_path": "sample.jpg"}),
            NodeModel(
                id="n2",
                block_type="DenoiseBlur",
                title="Blur",
                x=20,
                y=20,
                params={"method": "gaussian", "gauss_ksize_x": 5, "gauss_ksize_y": 5, "gauss_sigma_x": 1.2},
            ),
            NodeModel(id="n3", block_type="ImageOutputPreview", title="Output", x=40, y=40, params={}),
            NodeModel(id="n4", block_type="ConceptHOGCellsBlocks3780", title="Concept", x=20, y=120, params={"markdown": "HOG concept"}),
            NodeModel(id="n5", block_type="SimpleThreshold", title="Orphan Threshold", x=200, y=200, params={"thresh": 120}),
        ],
        edges=[
            EdgeModel(id="e1", src_node="n1", src_port="image", dst_node="n2", dst_port="image"),
            EdgeModel(id="e2", src_node="n2", src_port="image", dst_node="n3", dst_port="image"),
        ],
    )


def _contour_count_pipeline() -> PipelineModel:
    return PipelineModel(
        nodes=[
            NodeModel(id="n1", block_type="ImageInput", title="Input", x=0, y=0, params={"image_path": "sample.jpg"}),
            NodeModel(id="n2", block_type="SimpleThreshold", title="Threshold", x=20, y=20, params={"thresh": 110}),
            NodeModel(id="n3", block_type="ContoursAnalysis", title="Contours", x=40, y=40, params={"retrieval": "external"}),
            NodeModel(id="n4", block_type="ContourCount", title="Count", x=60, y=60, params={"label_filter": "contour"}),
        ],
        edges=[
            EdgeModel(id="e1", src_node="n1", src_port="image", dst_node="n2", dst_port="image"),
            EdgeModel(id="e2", src_node="n2", src_port="mask", dst_node="n3", dst_port="mask"),
            EdgeModel(id="e3", src_node="n3", src_port="image", dst_node="n4", dst_port="image"),
            EdgeModel(id="e4", src_node="n3", src_port="detections", dst_node="n4", dst_port="detections"),
        ],
    )


def _new_blocks_pipeline() -> PipelineModel:
    return PipelineModel(
        nodes=[
            NodeModel(id="n1", block_type="ImageInput", title="Input", x=0, y=0, params={"image_path": "sample.jpg"}),
            NodeModel(id="n2", block_type="ResizeImage", title="Resize", x=20, y=20, params={"mode": "dsize", "width": 320, "height": 240}),
            NodeModel(id="n3", block_type="InRangeMask", title="Range", x=40, y=40, params={"color_space": "hsv"}),
            NodeModel(id="n4", block_type="ApplyMask", title="Apply", x=60, y=60, params={}),
            NodeModel(id="n5", block_type="SplitImage", title="Split", x=80, y=80, params={}),
            NodeModel(id="n6", block_type="Filter2D", title="Filter", x=100, y=100, params={"kernel_json": "[[0,-1,0],[-1,5,-1],[0,-1,0]]"}),
            NodeModel(id="n7", block_type="PSNRCompare", title="PSNR", x=120, y=120, params={}),
            NodeModel(id="n8", block_type="ChannelSplit", title="ChSplit", x=140, y=140, params={}),
            NodeModel(id="n9", block_type="ChannelMerge", title="ChMerge", x=160, y=160, params={}),
        ],
        edges=[
            EdgeModel(id="e1", src_node="n1", src_port="image", dst_node="n2", dst_port="image"),
            EdgeModel(id="e2", src_node="n2", src_port="image", dst_node="n3", dst_port="image"),
            EdgeModel(id="e3", src_node="n2", src_port="image", dst_node="n4", dst_port="image"),
            EdgeModel(id="e4", src_node="n3", src_port="mask", dst_node="n4", dst_port="mask"),
            EdgeModel(id="e5", src_node="n4", src_port="image", dst_node="n5", dst_port="image"),
            EdgeModel(id="e6", src_node="n5", src_port="image_a", dst_node="n6", dst_port="image"),
            EdgeModel(id="e7", src_node="n5", src_port="image_a", dst_node="n7", dst_port="image_a"),
            EdgeModel(id="e8", src_node="n6", src_port="image", dst_node="n7", dst_port="image_b"),
            EdgeModel(id="e9", src_node="n7", src_port="image", dst_node="n8", dst_port="image"),
            EdgeModel(id="e10", src_node="n8", src_port="image_b", dst_node="n9", dst_port="image_b"),
            EdgeModel(id="e11", src_node="n8", src_port="image_g", dst_node="n9", dst_port="image_g"),
            EdgeModel(id="e12", src_node="n8", src_port="image_r", dst_node="n9", dst_port="image_r"),
        ],
    )


def _face_blocks_pipeline() -> PipelineModel:
    return PipelineModel(
        nodes=[
            NodeModel(id="n1", block_type="ImageInput", title="Input", x=0, y=0, params={"image_path": "sample.jpg"}),
            NodeModel(id="n2", block_type="HOGDetectMultiScaleAdvanced", title="HOG Adv", x=20, y=20, params={}),
            NodeModel(id="n3", block_type="DetectionStyleDraw", title="Style", x=40, y=40, params={"shape": "ellipse"}),
            NodeModel(id="n4", block_type="CascadeDetectCustom", title="Cascade", x=60, y=60, params={}),
            NodeModel(id="n5", block_type="HOGDescriptorConfigurable", title="HOG Config", x=80, y=80, params={}),
            NodeModel(id="n6", block_type="DlibHOGFaceDetect", title="Dlib", x=100, y=100, params={}),
        ],
        edges=[
            EdgeModel(id="e1", src_node="n1", src_port="image", dst_node="n2", dst_port="image"),
            EdgeModel(id="e2", src_node="n2", src_port="image", dst_node="n3", dst_port="image"),
            EdgeModel(id="e3", src_node="n2", src_port="detections", dst_node="n3", dst_port="detections"),
            EdgeModel(id="e4", src_node="n1", src_port="image", dst_node="n4", dst_port="image"),
            EdgeModel(id="e5", src_node="n1", src_port="image", dst_node="n5", dst_port="image"),
            EdgeModel(id="e6", src_node="n1", src_port="image", dst_node="n6", dst_port="image"),
        ],
    )


def test_python_export_syntax() -> None:
    registry = create_default_registry()
    script = export_python_script(_pipeline(), registry)
    ast.parse(script)
    assert "PIPELINE_DICT" in script
    assert "main()" in script


def test_notebook_export_shape() -> None:
    registry = create_default_registry()
    nb = export_notebook(_pipeline(), registry)
    assert len(nb.cells) >= 5
    assert nb.cells[0].cell_type == "markdown"
    code_sources = "\n\n".join(cell.source for cell in nb.cells if cell.cell_type == "code")
    for cell in nb.cells:
        if cell.cell_type == "code":
            ast.parse(cell.source)
    assert "cv_pipeline_lab" not in code_sources
    assert "node_id =" not in code_sources
    assert "cv2.imread" in code_sources
    assert "show(" in code_sources
    assert "Orphan Threshold" not in code_sources


def test_notebook_export_contour_count_block_snippet() -> None:
    registry = create_default_registry()
    nb = export_notebook(_contour_count_pipeline(), registry)
    code_sources = "\n\n".join(cell.source for cell in nb.cells if cell.cell_type == "code")
    assert "Contour count:" in code_sources
    assert "contour_count" in code_sources
    assert "(count={" in code_sources


def test_notebook_export_new_blocks_templates_parse() -> None:
    registry = create_default_registry()
    nb = export_notebook(_new_blocks_pipeline(), registry)
    for cell in nb.cells:
        if cell.cell_type == "code":
            ast.parse(cell.source)
    code_sources = "\n\n".join(cell.source for cell in nb.cells if cell.cell_type == "code")
    assert "cv2.inRange" in code_sources
    assert "cv2.filter2D" in code_sources
    assert "cv2.PSNR" in code_sources


def test_notebook_export_face_blocks_templates_parse() -> None:
    registry = create_default_registry()
    nb = export_notebook(_face_blocks_pipeline(), registry)
    for cell in nb.cells:
        if cell.cell_type == "code":
            ast.parse(cell.source)
    code_sources = "\n\n".join(cell.source for cell in nb.cells if cell.cell_type == "code")
    assert "cv2.CascadeClassifier" in code_sources
    assert "detectMultiScale" in code_sources
    assert "cv2.HOGDescriptor" in code_sources
    assert "import dlib" in code_sources
