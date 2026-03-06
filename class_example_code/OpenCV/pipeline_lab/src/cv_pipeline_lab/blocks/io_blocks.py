from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from cv_pipeline_lab.blocks.base import BlockBase
from cv_pipeline_lab.blocks.utils import ensure_bgr, ensure_gray
from cv_pipeline_lab.core.types import BlockSpec, Detection, ParamSpec, PortSpec, RunContext


class ImageInputBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ImageInput",
            title="Image Input",
            category="I/O",
            output_ports=[PortSpec("image", "image")],
            params=[ParamSpec("image_path", "str", "", label="Image Path")],
            description="Load image from file path",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        path = ctx.image_override or str(params.get("image_path", "")).strip()
        if not path:
            raise ValueError("ImageInput requires image_path or --image override")
        img = cv2.imread(str(Path(path).expanduser()))
        if img is None:
            raise ValueError(f"Unable to load image: {path}")
        return {"image": img}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        return (
            "# Image Input\n"
            f"image = cv2.imread(r\"{params.get('image_path', '')}\")\n"
            "if image is None:\n"
            "    raise ValueError('Could not load image')"
        )


class VideoFrameInputBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="VideoFrameInput",
            title="Video Frame Input",
            category="I/O",
            output_ports=[PortSpec("image", "image"), PortSpec("meta", "meta")],
            params=[
                ParamSpec("source", "str", "0", label="Source (index or path)"),
                ParamSpec("api_preference", "int", 0, min_value=0, max_value=10000, step=1, label="API Preference"),
                ParamSpec("frame_index", "int", 0, min_value=0, max_value=100000, step=1),
                ParamSpec("set_width", "int", 0, min_value=0, max_value=8192, step=1),
                ParamSpec("set_height", "int", 0, min_value=0, max_value=8192, step=1),
                ParamSpec("set_fps", "float", 0.0, min_value=0.0, max_value=240.0, step=0.5),
            ],
            description="Capture one frame from webcam/video file via cv2.VideoCapture.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        source_raw = str(params.get("source", "0")).strip()
        if source_raw.isdigit():
            source: int | str = int(source_raw)
        else:
            source = str(Path(source_raw).expanduser())

        api = int(params.get("api_preference", 0))
        cap = cv2.VideoCapture(source, api) if api > 0 else cv2.VideoCapture(source)
        if not cap.isOpened():
            raise ValueError(f"Unable to open video source: {source_raw}")

        set_w = int(params.get("set_width", 0))
        set_h = int(params.get("set_height", 0))
        set_fps = float(params.get("set_fps", 0.0))
        if set_w > 0:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(set_w))
        if set_h > 0:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(set_h))
        if set_fps > 0.0:
            cap.set(cv2.CAP_PROP_FPS, set_fps)

        frame_index = int(params.get("frame_index", 0))
        if frame_index > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, float(frame_index))

        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            raise RuntimeError("VideoCapture read failed")

        meta = {
            "source": source_raw,
            "frame_index": frame_index,
            "width": int(frame.shape[1]),
            "height": int(frame.shape[0]),
        }
        return {"image": frame, "meta": meta}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        source = str(params.get("source", "0")).strip()
        api = int(params.get("api_preference", 0))
        frame_index = int(params.get("frame_index", 0))
        set_w = int(params.get("set_width", 0))
        set_h = int(params.get("set_height", 0))
        set_fps = float(params.get("set_fps", 0.0))
        return (
            "# Video Frame Input\n"
            f"source = {source!r}\n"
            "source_obj = int(source) if str(source).isdigit() else source\n"
            f"cap = cv2.VideoCapture(source_obj{', ' + str(api) if api > 0 else ''})\n"
            "if not cap.isOpened():\n"
            "    raise ValueError(f'Unable to open source: {source}')\n"
            f"if {set_w} > 0:\n"
            f"    cap.set(cv2.CAP_PROP_FRAME_WIDTH, {set_w})\n"
            f"if {set_h} > 0:\n"
            f"    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, {set_h})\n"
            f"if {set_fps} > 0:\n"
            f"    cap.set(cv2.CAP_PROP_FPS, {set_fps})\n"
            f"if {frame_index} > 0:\n"
            f"    cap.set(cv2.CAP_PROP_POS_FRAMES, {frame_index})\n"
            "ok, image = cap.read()\n"
            "cap.release()\n"
            "if not ok or image is None:\n"
            "    raise RuntimeError('VideoCapture read failed')"
        )


class ImageOutputPreviewBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ImageOutputPreview",
            title="Image Output Preview",
            category="I/O",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image")],
            description="Terminal output node for previews",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = inputs.get("image")
        if image is None:
            raise ValueError("ImageOutputPreview expects input image")
        return {"image": ensure_bgr(image)}


class SaveImageBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="SaveImage",
            title="Save Image",
            category="I/O",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image"), PortSpec("meta", "meta")],
            params=[ParamSpec("output_path", "str", "", label="Output Path")],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = inputs.get("image")
        if image is None:
            raise ValueError("SaveImage expects input image")
        image = ensure_bgr(image)
        out_path = str(params.get("output_path", "")).strip()
        if not out_path:
            base = ctx.artifacts_dir or (ctx.pipeline_dir / "tmp" / "pipeline_outputs")
            base.mkdir(parents=True, exist_ok=True)
            out_path = str(base / "saved_image.png")
        p = Path(out_path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        ok = cv2.imwrite(str(p), image)
        if not ok:
            raise RuntimeError(f"Failed to save image to {p}")
        return {"image": image, "meta": {"saved_path": str(p)}}


class SplitImageBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="SplitImage",
            title="Split Image",
            category="Utility",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image_a", "image"), PortSpec("image_b", "image")],
            description="Fan-out branch utility",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = inputs.get("image")
        if image is None:
            raise ValueError("SplitImage expects input image")
        image = ensure_bgr(image)
        return {"image_a": image.copy(), "image_b": image.copy()}


class MergeImageBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="MergeImage",
            title="Merge Image",
            category="Utility",
            input_ports=[PortSpec("image_a", "image"), PortSpec("image_b", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[
                ParamSpec("mode", "enum", "hconcat", options=["hconcat", "vconcat", "alpha", "choose_a", "choose_b"]),
                ParamSpec("alpha", "float", 0.5, min_value=0.0, max_value=1.0, step=0.05),
            ],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        a = inputs.get("image_a")
        b = inputs.get("image_b")
        if a is None or b is None:
            raise ValueError("MergeImage expects image_a and image_b")
        a = ensure_bgr(a)
        b = ensure_bgr(b)
        mode = str(params.get("mode", "hconcat"))
        alpha = float(params.get("alpha", 0.5))

        if mode == "choose_a":
            merged = a
        elif mode == "choose_b":
            merged = b
        elif mode == "alpha":
            if a.shape != b.shape:
                b = cv2.resize(b, (a.shape[1], a.shape[0]))
            merged = cv2.addWeighted(a, 1.0 - alpha, b, alpha, 0)
        elif mode == "vconcat":
            w = min(a.shape[1], b.shape[1])
            a2 = cv2.resize(a, (w, int(a.shape[0] * w / a.shape[1])))
            b2 = cv2.resize(b, (w, int(b.shape[0] * w / b.shape[1])))
            merged = cv2.vconcat([a2, b2])
        else:
            h = min(a.shape[0], b.shape[0])
            a2 = cv2.resize(a, (int(a.shape[1] * h / a.shape[0]), h))
            b2 = cv2.resize(b, (int(b.shape[1] * h / b.shape[0]), h))
            merged = cv2.hconcat([a2, b2])
        return {"image": merged}


class DrawDetectionsBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="DrawDetections",
            title="Draw Detections",
            category="Utility",
            input_ports=[PortSpec("image", "image"), PortSpec("detections", "detections")],
            output_ports=[PortSpec("image", "image")],
            params=[
                ParamSpec("show_label", "bool", True),
                ParamSpec("show_score", "bool", True),
            ],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = inputs.get("image")
        detections = inputs.get("detections") or []
        if image is None:
            raise ValueError("DrawDetections expects image")
        out = ensure_bgr(image).copy()
        show_label = bool(params.get("show_label", True))
        show_score = bool(params.get("show_score", True))
        for det in detections:
            if isinstance(det, Detection):
                x, y, w, h = det.bbox
                label = det.label
                score = det.score
            else:
                x, y, w, h = tuple(det.get("bbox", (0, 0, 0, 0)))
                label = str(det.get("label", "obj"))
                score = float(det.get("score", 1.0))
            cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = ""
            if show_label:
                text += label
            if show_score:
                text += (" " if text else "") + f"{score:.2f}"
            if text:
                cv2.putText(out, text, (x, max(10, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        return {"image": out}


class ApplyMaskBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ApplyMask",
            title="Apply Mask (Bitwise AND)",
            category="Utility",
            input_ports=[PortSpec("image", "image"), PortSpec("mask", "mask")],
            output_ports=[PortSpec("image", "image")],
            params=[],
            description="Apply binary mask to image via cv2.bitwise_and(image, image, mask=mask).",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = inputs.get("image")
        mask = inputs.get("mask")
        if image is None or mask is None:
            raise ValueError("ApplyMask expects image and mask")
        img = ensure_bgr(image)
        m = ensure_gray(mask)
        out = cv2.bitwise_and(img, img, mask=m)
        return {"image": out}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        return (
            "# Apply Mask (Bitwise AND)\n"
            "image_out = cv2.bitwise_and(image, image, mask=mask)"
        )


class ContourCountBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ContourCount",
            title="Count Contours",
            category="Utility",
            input_ports=[PortSpec("image", "image"), PortSpec("detections", "detections")],
            output_ports=[PortSpec("image", "image"), PortSpec("detections", "detections"), PortSpec("meta", "meta")],
            params=[
                ParamSpec("label_filter", "str", "contour", label="Label Filter"),
                ParamSpec("exact_match", "bool", True, label="Exact Match"),
                ParamSpec("annotate", "bool", False, label="Draw Count Text"),
                ParamSpec("title_prefix", "str", "Contours", label="Text Prefix"),
            ],
            description="Count contour detections and pass the image downstream.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = inputs.get("image")
        if image is None:
            raise ValueError("ContourCount expects image")
        detections = inputs.get("detections") or []

        label_filter = str(params.get("label_filter", "contour")).strip()
        exact_match = bool(params.get("exact_match", True))
        annotate = bool(params.get("annotate", False))
        title_prefix = str(params.get("title_prefix", "Contours")).strip() or "Contours"

        def _label(det: Any) -> str:
            if isinstance(det, Detection):
                return det.label
            if isinstance(det, dict):
                return str(det.get("label", ""))
            return str(getattr(det, "label", ""))

        contour_count = 0
        for det in detections:
            label = _label(det)
            if not label_filter:
                contour_count += 1
                continue
            if exact_match:
                if label == label_filter:
                    contour_count += 1
            elif label_filter.lower() in label.lower():
                contour_count += 1

        out = ensure_bgr(image).copy()
        if annotate:
            cv2.putText(
                out,
                f"{title_prefix}: {contour_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

        print(f"Contour count: {contour_count}")
        return {
            "image": out,
            "detections": list(detections),
            "meta": {
                "contour_count": contour_count,
                "label_filter": label_filter,
                "exact_match": exact_match,
                "total_detections": len(detections),
            },
        }

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        label_filter = str(params.get("label_filter", "contour")).strip()
        exact_match = bool(params.get("exact_match", True))
        return (
            "# Count Contours\n"
            "detections_in = detections or []\n"
            f"label_filter = {label_filter!r}\n"
            f"exact_match = {exact_match}\n"
            "contour_count = 0\n"
            "for det in detections_in:\n"
            "    label = det.label if hasattr(det, 'label') else str(det.get('label', ''))\n"
            "    if not label_filter:\n"
            "        contour_count += 1\n"
            "    elif exact_match and label == label_filter:\n"
            "        contour_count += 1\n"
            "    elif (not exact_match) and label_filter.lower() in label.lower():\n"
            "        contour_count += 1\n"
            "print(f'Contour count: {contour_count}')\n"
            "image_out = image.copy()"
        )


class GrayConvertBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="GrayConvert",
            title="Gray Convert",
            category="Utility",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image"), PortSpec("mask", "mask")],
            description="Convert BGR image to grayscale",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = inputs.get("image")
        if image is None:
            raise ValueError("GrayConvert expects image")
        gray = ensure_gray(image)
        return {"image": cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), "mask": gray}


class ColorConvertBlock(BlockBase):
    MODES = {
        "bgr2rgb": cv2.COLOR_BGR2RGB,
        "bgr2hsv": cv2.COLOR_BGR2HSV,
        "bgr2lab": cv2.COLOR_BGR2LAB,
        "rgb2bgr": cv2.COLOR_RGB2BGR,
        "hsv2bgr": cv2.COLOR_HSV2BGR,
        "lab2bgr": cv2.COLOR_LAB2BGR,
    }

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ColorConvert",
            title="Color Convert",
            category="Utility",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[ParamSpec("mode", "enum", "bgr2hsv", options=list(cls.MODES.keys()))],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = inputs.get("image")
        if image is None:
            raise ValueError("ColorConvert expects image")
        image = ensure_bgr(image)
        mode = str(params.get("mode", "bgr2hsv"))
        code = self.MODES.get(mode, cv2.COLOR_BGR2HSV)
        out = cv2.cvtColor(image, code)
        # Keep pipeline-friendly by converting grayscale-ish outputs to BGR if needed.
        if out.ndim == 2:
            out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
        return {"image": out}


class ChannelSplitBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ChannelSplit",
            title="Channel Split (B/G/R)",
            category="Utility",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image_b", "image"), PortSpec("image_g", "image"), PortSpec("image_r", "image")],
            params=[],
            description="Split BGR image into separate single-channel images (as BGR visuals).",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = inputs.get("image")
        if image is None:
            raise ValueError("ChannelSplit expects image")
        img = ensure_bgr(image)
        b, g, r = cv2.split(img)
        return {
            "image_b": cv2.cvtColor(b, cv2.COLOR_GRAY2BGR),
            "image_g": cv2.cvtColor(g, cv2.COLOR_GRAY2BGR),
            "image_r": cv2.cvtColor(r, cv2.COLOR_GRAY2BGR),
        }


class ChannelMergeBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ChannelMerge",
            title="Channel Merge (B/G/R)",
            category="Utility",
            input_ports=[PortSpec("image_b", "image"), PortSpec("image_g", "image"), PortSpec("image_r", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[],
            description="Merge separate B/G/R channel images into one BGR image.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        b_img = inputs.get("image_b")
        g_img = inputs.get("image_g")
        r_img = inputs.get("image_r")
        if b_img is None or g_img is None or r_img is None:
            raise ValueError("ChannelMerge expects image_b, image_g, image_r")
        b = ensure_gray(b_img)
        g = ensure_gray(g_img)
        r = ensure_gray(r_img)
        if b.shape != g.shape or b.shape != r.shape:
            raise ValueError("ChannelMerge expects equal channel image sizes")
        return {"image": cv2.merge([b, g, r])}


class PSNRCompareBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="PSNRCompare",
            title="PSNR Compare",
            category="Utility",
            input_ports=[PortSpec("image_a", "image"), PortSpec("image_b", "image")],
            output_ports=[PortSpec("image", "image"), PortSpec("meta", "meta")],
            params=[
                ParamSpec("r", "float", 255.0, min_value=1.0, max_value=65535.0, step=1.0, label="R"),
                ParamSpec("use_b_as_output", "bool", False),
            ],
            description="Compute cv2.PSNR(image_a, image_b, R) and pass one image through.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        a = inputs.get("image_a")
        b = inputs.get("image_b")
        if a is None or b is None:
            raise ValueError("PSNRCompare expects image_a and image_b")
        img_a = ensure_bgr(a)
        img_b = ensure_bgr(b)
        if img_a.shape != img_b.shape:
            img_b = cv2.resize(img_b, (img_a.shape[1], img_a.shape[0]), interpolation=cv2.INTER_LINEAR)
        r = float(params.get("r", 255.0))
        psnr = float(cv2.PSNR(img_a, img_b, r))
        print(f"PSNR: {psnr:.4f} dB")
        out = img_b if bool(params.get("use_b_as_output", False)) else img_a
        return {"image": out, "meta": {"psnr": psnr, "r": r}}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        r = float(params.get("r", 255.0))
        return (
            "# PSNR Compare\n"
            f"r = {r}\n"
            "psnr = cv2.PSNR(image_a, image_b, r)\n"
            "print(f'PSNR: {psnr:.4f} dB')\n"
            "image_out = image_a"
        )
