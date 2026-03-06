from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from cv_pipeline_lab.core.registry import create_default_registry
from cv_pipeline_lab.core.types import Detection, RunContext


def _sample_image() -> np.ndarray:
    img = np.zeros((240, 320, 3), dtype=np.uint8)
    img[:] = (30, 30, 30)
    # Add simple shapes and contrast for detectors.
    img[40:200, 60:260] = (200, 200, 200)
    return img


def _contours_image() -> np.ndarray:
    img = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.rectangle(img, (20, 40), (80, 180), (255, 255, 255), -1)   # area ~8400, aspect ~0.43
    cv2.rectangle(img, (140, 90), (290, 140), (255, 255, 255), -1)  # area ~7500, aspect ~3.0
    return img


def test_compute_blocks_default_run() -> None:
    registry = create_default_registry()
    ctx = RunContext(pipeline_dir=Path.cwd())
    image = _sample_image()

    compute_blocks = [
        "PreprocessPipeline",
        "ResizeImage",
        "ImageCrop",
        "ContrastAdjustment",
        "LogTransform",
        "GammaTransform",
        "InRangeMask",
        "DenoiseBlur",
        "Filter2D",
        "Sharpen",
        "CannyEdge",
        "SimpleThreshold",
        "AdaptiveThreshold",
        "BinaryMorphology",
        "ContoursAnalysis",
        "HoughCircles",
        "HaarMultiDetect",
        "CascadeDetectCustom",
        "HOGDescriptor64x128",
        "HOGDescriptorConfigurable",
        "HOGSVMDetectPeople",
        "HOGDetectMultiScaleAdvanced",
        "DlibHOGFaceDetect",
    ]

    for block_type in compute_blocks:
        block = registry.get(block_type)
        params = registry.default_params(block_type)
        spec = registry.get_spec(block_type)
        if spec.input_ports and spec.input_ports[0].type == "mask":
            inputs = {"mask": cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)}
        else:
            inputs = {"image": image.copy()}
        try:
            outputs = block.run(inputs, params, ctx)
        except RuntimeError as exc:
            # If OpenCV build lacks cascade files, skip that one case.
            if block_type == "HaarMultiDetect" and "cascades" in str(exc).lower():
                continue
            if block_type == "DlibHOGFaceDetect" and "dlib is not installed" in str(exc).lower():
                continue
            raise

        assert isinstance(outputs, dict)
        spec = registry.get_spec(block_type)
        for port in spec.output_ports:
            assert port.name in outputs

        if "image" in outputs:
            assert isinstance(outputs["image"], np.ndarray)
        if "mask" in outputs:
            assert outputs["mask"].ndim == 2
        if "feature_vector" in outputs:
            assert len(outputs["feature_vector"]) > 0
        if "detections" in outputs:
            assert isinstance(outputs["detections"], list)


def test_simple_adjustment_blocks_custom_params() -> None:
    registry = create_default_registry()
    ctx = RunContext(pipeline_dir=Path.cwd())
    image = _sample_image()

    cases = [
        ("ContrastAdjustment", {"alpha": 1.8, "beta": 20}),
        ("LogTransform", {"gain": 1.3, "normalize": True}),
        ("GammaTransform", {"gamma": 0.7, "gain": 1.0}),
    ]

    for block_type, params in cases:
        block = registry.get(block_type)
        defaults = registry.default_params(block_type)
        merged = dict(defaults)
        merged.update(params)
        outputs = block.run({"image": image.copy()}, merged, ctx)
        assert "image" in outputs
        assert outputs["image"].shape == image.shape
        assert outputs["image"].dtype == np.uint8


def test_image_crop_block_custom_box() -> None:
    registry = create_default_registry()
    ctx = RunContext(pipeline_dir=Path.cwd())
    image = _sample_image()
    block = registry.get("ImageCrop")

    params = registry.default_params("ImageCrop")
    params.update({"x": 30, "y": 40, "width": 120, "height": 80})
    outputs = block.run({"image": image.copy()}, params, ctx)

    assert "image" in outputs
    assert outputs["image"].shape[:2] == (80, 120)
    assert outputs["meta"]["crop_box"] == {"x": 30, "y": 40, "width": 120, "height": 80}


def test_denoise_blur_methods_run_with_method_specific_params() -> None:
    registry = create_default_registry()
    ctx = RunContext(pipeline_dir=Path.cwd())
    image = _sample_image()
    block = registry.get("DenoiseBlur")

    params_by_method = [
        {
            "method": "box",
            "box_ksize_x": 7,
            "box_ksize_y": 3,
            "box_normalize": True,
            "box_border": "reflect",
        },
        {
            "method": "gaussian",
            "gauss_ksize_x": 9,
            "gauss_ksize_y": 5,
            "gauss_sigma_x": 1.4,
            "gauss_sigma_y": 0.8,
            "gauss_border": "replicate",
        },
        {
            "method": "median",
            "median_ksize": 7,
        },
        {
            "method": "bilateral",
            "bilateral_d": 11,
            "bilateral_sigma_color": 95.0,
            "bilateral_sigma_space": 70.0,
            "bilateral_border": "default",
        },
    ]

    defaults = registry.default_params("DenoiseBlur")
    for method_params in params_by_method:
        params = dict(defaults)
        params.update(method_params)
        outputs = block.run({"image": image.copy()}, params, ctx)
        assert "image" in outputs
        assert outputs["image"].shape == image.shape


def test_contours_analysis_filters_area_and_aspect_ratio() -> None:
    registry = create_default_registry()
    ctx = RunContext(pipeline_dir=Path.cwd())
    block = registry.get("ContoursAnalysis")
    image = _contours_image()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    params = registry.default_params("ContoursAnalysis")
    params.update(
        {
            "ensure_binary": True,
            "binary_thresh": 127,
            "invert": False,
            "retrieval": "external",
            "approx_mode": "simple",
            "filter_by_area": True,
            "area_min": 5000,
            "area_max": 10000,
            "filter_by_aspect_ratio": True,
            "aspect_ratio_min": 2.0,
            "aspect_ratio_max": 4.0,
        }
    )
    outputs = block.run({"mask": mask.copy()}, params, ctx)

    assert "detections" in outputs
    assert len(outputs["detections"]) == 1
    det = outputs["detections"][0]
    assert det.extra["area"] >= 5000
    assert 2.0 <= det.extra["aspect_ratio"] <= 4.0
    assert outputs["meta"]["kept_contours"] == 1


def test_contours_analysis_supports_all_find_contours_modes() -> None:
    registry = create_default_registry()
    ctx = RunContext(pipeline_dir=Path.cwd())
    block = registry.get("ContoursAnalysis")
    image = _contours_image()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    defaults = registry.default_params("ContoursAnalysis")
    defaults.update(
        {
            "ensure_binary": True,
            "binary_thresh": 127,
            "invert": False,
            "filter_by_area": False,
            "filter_by_aspect_ratio": False,
        }
    )

    retrieval_modes = ["external", "list", "ccomp", "tree", "floodfill"]
    approx_modes = ["none", "simple", "tc89_l1", "tc89_kcos"]
    for retrieval in retrieval_modes:
        for approx in approx_modes:
            params = dict(defaults)
            params["retrieval"] = retrieval
            params["approx_mode"] = approx
            outputs = block.run({"mask": mask.copy()}, params, ctx)
            assert isinstance(outputs["mask"], np.ndarray)
            assert outputs["mask"].dtype == np.uint8
            assert "meta" in outputs
            assert outputs["meta"]["retrieval"] == retrieval
            assert outputs["meta"]["approx_mode"] == approx


def test_binary_morphology_operations_and_kernel_shapes() -> None:
    registry = create_default_registry()
    ctx = RunContext(pipeline_dir=Path.cwd())
    block = registry.get("BinaryMorphology")
    image = _contours_image()
    mask = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    defaults = registry.default_params("BinaryMorphology")
    operations = ["dilate", "erode", "open", "close", "gradient", "tophat", "blackhat"]
    shapes = ["rect", "ellipse", "cross"]

    for operation in operations:
        for shape in shapes:
            params = dict(defaults)
            params.update(
                {
                    "operation": operation,
                    "kernel_shape": shape,
                    "kernel_w": 5,
                    "kernel_h": 5,
                    "iterations": 1,
                    "ensure_binary": True,
                    "binary_thresh": 127,
                }
            )
            outputs = block.run({"mask": mask.copy()}, params, ctx)
            assert "mask" in outputs
            assert outputs["mask"].shape == mask.shape
            assert outputs["mask"].dtype == np.uint8
            assert outputs["meta"]["operation"] == operation


def test_contour_count_block_counts_and_prints(capsys) -> None:
    registry = create_default_registry()
    ctx = RunContext(pipeline_dir=Path.cwd())
    block = registry.get("ContourCount")
    image = _sample_image()

    detections = [
        Detection((10, 10, 20, 20), "contour", 1.0),
        {"bbox": (40, 30, 20, 10), "label": "contour", "score": 1.0},
        {"bbox": (80, 80, 15, 15), "label": "circle", "score": 1.0},
    ]

    params = registry.default_params("ContourCount")
    outputs = block.run({"image": image.copy(), "detections": detections}, params, ctx)

    captured = capsys.readouterr()
    assert "Contour count: 2" in captured.out
    assert outputs["meta"]["contour_count"] == 2
    assert outputs["meta"]["total_detections"] == 3
    assert outputs["image"].shape == image.shape
    assert isinstance(outputs["detections"], list)


def test_apply_mask_channel_split_merge_and_psnr_blocks(capsys) -> None:
    registry = create_default_registry()
    ctx = RunContext(pipeline_dir=Path.cwd())
    image = _sample_image()

    split = registry.get("ChannelSplit")
    split_out = split.run({"image": image.copy()}, registry.default_params("ChannelSplit"), ctx)
    assert {"image_b", "image_g", "image_r"} <= set(split_out.keys())

    merge = registry.get("ChannelMerge")
    merge_out = merge.run(
        {"image_b": split_out["image_b"], "image_g": split_out["image_g"], "image_r": split_out["image_r"]},
        registry.default_params("ChannelMerge"),
        ctx,
    )
    assert "image" in merge_out
    assert merge_out["image"].shape == image.shape

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    apply_mask = registry.get("ApplyMask")
    mask_out = apply_mask.run({"image": image.copy(), "mask": mask}, registry.default_params("ApplyMask"), ctx)
    assert "image" in mask_out
    assert mask_out["image"].shape == image.shape

    psnr_block = registry.get("PSNRCompare")
    psnr_params = registry.default_params("PSNRCompare")
    psnr_out = psnr_block.run({"image_a": image.copy(), "image_b": merge_out["image"]}, psnr_params, ctx)
    captured = capsys.readouterr()
    assert "PSNR:" in captured.out
    assert "meta" in psnr_out
    assert "psnr" in psnr_out["meta"]


def test_detection_style_draw_and_custom_cascade_block() -> None:
    registry = create_default_registry()
    ctx = RunContext(pipeline_dir=Path.cwd())
    image = _sample_image()

    draw_block = registry.get("DetectionStyleDraw")
    draw_params = registry.default_params("DetectionStyleDraw")
    detections = [
        Detection((20, 20, 40, 40), "person", 0.2),
        Detection((100, 40, 30, 50), "person", 0.8),
    ]
    draw_params.update({"filter_by_score": True, "min_score": 0.5, "max_score": 1.0})
    draw_out = draw_block.run({"image": image.copy(), "detections": detections}, draw_params, ctx)
    assert "image" in draw_out
    assert "meta" in draw_out
    assert draw_out["meta"]["drawn_count"] == 1
    assert len(draw_out["detections"]) == 1
    assert draw_out["detections"][0].score >= 0.5

    cascade_block = registry.get("CascadeDetectCustom")
    cascade_params = registry.default_params("CascadeDetectCustom")
    cascade_params["cascade_path"] = cv2.data.haarcascades + "haarcascade_frontalface_alt.xml"
    cascade_out = cascade_block.run({"image": image.copy()}, cascade_params, ctx)
    assert "image" in cascade_out
    assert "detections" in cascade_out
    assert "meta" in cascade_out
