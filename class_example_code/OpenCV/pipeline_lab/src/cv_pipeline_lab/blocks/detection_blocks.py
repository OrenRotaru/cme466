from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from cv_pipeline_lab.blocks.base import BlockBase
from cv_pipeline_lab.blocks.utils import ensure_bgr, ensure_gray
from cv_pipeline_lab.core.types import BlockSpec, Detection, ParamSpec, PortSpec, RunContext


class HaarMultiDetectBlock(BlockBase):
    def __init__(self) -> None:
        self.cascades: dict[str, cv2.CascadeClassifier] = {}
        cascade_files = {
            "frontal": "haarcascade_frontalface_default.xml",
            "profile": "haarcascade_profileface.xml",
            "eye": "haarcascade_eye.xml",
            "smile": "haarcascade_smile.xml",
        }
        for key, filename in cascade_files.items():
            cc = cv2.CascadeClassifier(cv2.data.haarcascades + filename)
            if not cc.empty():
                self.cascades[key] = cc

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="HaarMultiDetect",
            title="Haar Multi-Detect",
            category="Detection",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image"), PortSpec("detections", "detections"), PortSpec("meta", "meta")],
            params=[
                ParamSpec("frontal", "bool", True),
                ParamSpec("profile", "bool", False),
                ParamSpec("eyes", "bool", True),
                ParamSpec("smile", "bool", False),
                ParamSpec("scale_factor", "float", 1.1, min_value=1.01, max_value=2.0, step=0.01),
                ParamSpec("min_neighbors", "int", 5, min_value=1, max_value=20, step=1),
                ParamSpec("min_size", "int", 30, min_value=10, max_value=500, step=1),
                ParamSpec("equalize_hist", "bool", True),
            ],
            description="Haar cascade detector for frontal/profile face + eyes/smile",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        if not self.cascades:
            raise RuntimeError("No Haar cascades available in cv2.data.haarcascades")

        img = ensure_bgr(inputs.get("image"))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if bool(params.get("equalize_hist", True)):
            gray = cv2.equalizeHist(gray)

        scale = max(1.01, float(params.get("scale_factor", 1.1)))
        min_neighbors = max(1, int(params.get("min_neighbors", 5)))
        min_size = max(10, int(params.get("min_size", 30)))
        min_size_tuple = (min_size, min_size)

        out = img.copy()
        detections: list[Detection] = []
        face_regions: list[tuple[int, int, int, int]] = []

        if bool(params.get("frontal", True)) and "frontal" in self.cascades:
            faces = self.cascades["frontal"].detectMultiScale(gray, scaleFactor=scale, minNeighbors=min_neighbors, minSize=min_size_tuple)
            for (x, y, w, h) in faces:
                detections.append(Detection((x, y, w, h), "frontal_face", 1.0))
                face_regions.append((x, y, w, h))
                cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if bool(params.get("profile", False)) and "profile" in self.cascades:
            prof = self.cascades["profile"].detectMultiScale(gray, scaleFactor=scale, minNeighbors=min_neighbors, minSize=min_size_tuple)
            for (x, y, w, h) in prof:
                detections.append(Detection((x, y, w, h), "profile_face", 1.0))
                face_regions.append((x, y, w, h))
                cv2.rectangle(out, (x, y), (x + w, y + h), (255, 180, 0), 2)

        if bool(params.get("eyes", True)) and "eye" in self.cascades:
            for (x, y, w, h) in face_regions:
                roi = gray[y : y + h, x : x + w]
                eyes = self.cascades["eye"].detectMultiScale(roi, scaleFactor=1.1, minNeighbors=max(2, min_neighbors // 2))
                for (ex, ey, ew, eh) in eyes:
                    detections.append(Detection((x + ex, y + ey, ew, eh), "eye", 1.0))
                    cv2.rectangle(out, (x + ex, y + ey), (x + ex + ew, y + ey + eh), (255, 0, 0), 1)

        if bool(params.get("smile", False)) and "smile" in self.cascades:
            for (x, y, w, h) in face_regions:
                roi = gray[y : y + h, x : x + w]
                smiles = self.cascades["smile"].detectMultiScale(roi, scaleFactor=1.7, minNeighbors=max(3, min_neighbors))
                for (sx, sy, sw, sh) in smiles:
                    detections.append(Detection((x + sx, y + sy, sw, sh), "smile", 1.0))
                    cv2.rectangle(out, (x + sx, y + sy), (x + sx + sw, y + sy + sh), (0, 0, 255), 1)

        meta = {
            "total_detections": len(detections),
            "concept": "Haar-like features + AdaBoost + stage cascade + sliding windows",
        }
        return {"image": out, "detections": detections, "meta": meta}


class HOGDescriptor64x128Block(BlockBase):
    def __init__(self) -> None:
        self.hog = cv2.HOGDescriptor()

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="HOGDescriptor64x128",
            title="HOG Descriptor (64x128)",
            category="Detection",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("feature_vector", "feature_vector"), PortSpec("image", "image"), PortSpec("meta", "meta")],
            params=[
                ParamSpec("roi_scale", "float", 0.6, min_value=0.1, max_value=1.0, step=0.05),
                ParamSpec("center_x", "float", 0.5, min_value=0.0, max_value=1.0, step=0.01),
                ParamSpec("center_y", "float", 0.5, min_value=0.0, max_value=1.0, step=0.01),
                ParamSpec("show_gradient", "bool", True),
            ],
            description="HOG descriptor with default OpenCV settings (3780 dims for 64x128)",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = ensure_bgr(inputs.get("image"))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]

        roi_scale = float(params.get("roi_scale", 0.6))
        cx_ratio = float(params.get("center_x", 0.5))
        cy_ratio = float(params.get("center_y", 0.5))
        show_grad = bool(params.get("show_gradient", True))

        roi_h = max(32, int(min(h, 2 * w) * roi_scale))
        roi_w = max(16, roi_h // 2)
        cx = int(cx_ratio * (w - 1))
        cy = int(cy_ratio * (h - 1))
        x1 = max(0, min(w - roi_w, cx - roi_w // 2))
        y1 = max(0, min(h - roi_h, cy - roi_h // 2))
        x2, y2 = x1 + roi_w, y1 + roi_h

        roi = gray[y1:y2, x1:x2]
        roi_64x128 = cv2.resize(roi, (64, 128), interpolation=cv2.INTER_LINEAR)
        feat = self.hog.compute(roi_64x128).reshape(-1)

        left = image.copy()
        cv2.rectangle(left, (x1, y1), (x2, y2), (0, 255, 0), 2)
        if show_grad:
            gx = cv2.Sobel(roi_64x128, cv2.CV_32F, 1, 0, ksize=1)
            gy = cv2.Sobel(roi_64x128, cv2.CV_32F, 0, 1, ksize=1)
            mag = cv2.magnitude(gx, gy)
            mag_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            right = cv2.applyColorMap(mag_u8, cv2.COLORMAP_TURBO)
        else:
            right = cv2.cvtColor(roi_64x128, cv2.COLOR_GRAY2BGR)

        right = cv2.resize(right, (left.shape[1], left.shape[0]), interpolation=cv2.INTER_NEAREST)
        vis = cv2.hconcat([left, right])

        meta = {
            "vector_length": int(len(feat)),
            "expected_default_len": 3780,
            "concept": "8x8 cells, 9 bins, 16x16 block normalization (L2-Hys)",
        }
        return {"feature_vector": feat, "image": vis, "meta": meta}


class HOGSVMDetectPeopleBlock(BlockBase):
    def __init__(self) -> None:
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="HOGSVMDetectPeople",
            title="HOG + SVM Detect People",
            category="Detection",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image"), PortSpec("detections", "detections"), PortSpec("meta", "meta")],
            params=[
                ParamSpec("hit_threshold", "float", 0.0, min_value=-2.0, max_value=2.0, step=0.1),
                ParamSpec("stride", "int", 8, min_value=4, max_value=32, step=4),
                ParamSpec("padding", "int", 8, min_value=0, max_value=32, step=4),
                ParamSpec("scale", "float", 1.05, min_value=1.01, max_value=1.5, step=0.01),
                ParamSpec("final_threshold", "int", 2, min_value=0, max_value=20, step=1),
                ParamSpec("weight_threshold", "float", 0.5, min_value=0.0, max_value=5.0, step=0.1),
            ],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = ensure_bgr(inputs.get("image"))
        hit = float(params.get("hit_threshold", 0.0))
        stride = max(4, int(params.get("stride", 8)))
        padding = max(0, int(params.get("padding", 8)))
        scale = max(1.01, float(params.get("scale", 1.05)))
        final_threshold = int(params.get("final_threshold", 2))
        weight_threshold = float(params.get("weight_threshold", 0.5))

        # OpenCV Python bindings expose this with positional args for some versions.
        rects, weights = self.hog.detectMultiScale(
            image,
            hit,
            (stride, stride),
            (padding, padding),
            scale,
            final_threshold,
        )

        out = image.copy()
        detections: list[Detection] = []
        for (x, y, w, h), score in zip(rects, weights):
            score_f = float(score)
            if score_f < weight_threshold:
                continue
            label = "person"
            detections.append(Detection((int(x), int(y), int(w), int(h)), label, score_f))
            color = (0, 255, 0) if score_f >= 1.0 else (0, 165, 255)
            cv2.rectangle(out, (int(x), int(y)), (int(x + w), int(y + h)), color, 2)
            cv2.putText(out, f"{score_f:.2f}", (int(x), max(12, int(y - 5))), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

        meta = {
            "raw_rects": int(len(rects)),
            "kept_rects": int(len(detections)),
            "concept": "HOG feature descriptor + linear SVM over sliding windows",
        }
        return {"image": out, "detections": detections, "meta": meta}


class CascadeDetectCustomBlock(BlockBase):
    SHAPE_MODES = ["rectangle", "ellipse", "circle", "none"]

    def __init__(self) -> None:
        self._cache: dict[str, cv2.CascadeClassifier] = {}

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="CascadeDetectCustom",
            title="Cascade Detect (Custom XML)",
            category="Detection",
            input_ports=[PortSpec("image", "image", "Input image for cascade detection.")],
            output_ports=[
                PortSpec("image", "image", "Image with optional drawn detections."),
                PortSpec("detections", "detections", "Detected objects from cascade."),
                PortSpec("meta", "meta", "Detection counts and cascade metadata."),
            ],
            params=[
                ParamSpec("cascade_path", "str", cv2.data.haarcascades + "haarcascade_frontalface_alt.xml"),
                ParamSpec("use_samples_findfile", "bool", False),
                ParamSpec("equalize_hist", "bool", True),
                ParamSpec("scale_factor", "float", 1.1, min_value=1.0001, max_value=2.0, step=0.01),
                ParamSpec("min_neighbors", "int", 5, min_value=0, max_value=100, step=1),
                ParamSpec("flags", "int", 0, min_value=0, max_value=100000, step=1),
                ParamSpec("min_size_w", "int", 30, min_value=0, max_value=4000, step=1),
                ParamSpec("min_size_h", "int", 30, min_value=0, max_value=4000, step=1),
                ParamSpec("max_size_w", "int", 0, min_value=0, max_value=4000, step=1),
                ParamSpec("max_size_h", "int", 0, min_value=0, max_value=4000, step=1),
                ParamSpec("label", "str", "cascade_obj"),
                ParamSpec("draw_mode", "enum", "rectangle", options=cls.SHAPE_MODES),
                ParamSpec("draw_thickness", "int", 2, min_value=1, max_value=20, step=1),
            ],
            description="Generic OpenCV CascadeClassifier block with full detectMultiScale controls.",
        )

    def _load_cascade(self, path: str, use_samples_findfile: bool) -> cv2.CascadeClassifier:
        raw_path = str(path).strip()
        if not raw_path:
            raise ValueError("CascadeDetectCustom requires cascade_path")

        if use_samples_findfile:
            try:
                resolved = cv2.samples.findFile(raw_path)
            except Exception:  # noqa: BLE001
                resolved = raw_path
        else:
            resolved = raw_path
        resolved = str(Path(resolved).expanduser())

        cached = self._cache.get(resolved)
        if cached is not None and not cached.empty():
            return cached
        cc = cv2.CascadeClassifier(resolved)
        if cc.empty():
            raise RuntimeError(f"Failed to load cascade XML: {resolved}")
        self._cache[resolved] = cc
        return cc

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = ensure_bgr(inputs.get("image"))
        cascade = self._load_cascade(str(params.get("cascade_path", "")), bool(params.get("use_samples_findfile", False)))

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if bool(params.get("equalize_hist", True)):
            gray = cv2.equalizeHist(gray)

        scale_factor = max(1.0001, float(params.get("scale_factor", 1.1)))
        min_neighbors = max(0, int(params.get("min_neighbors", 5)))
        flags = max(0, int(params.get("flags", 0)))
        min_size = (max(0, int(params.get("min_size_w", 30))), max(0, int(params.get("min_size_h", 30))))
        max_size = (max(0, int(params.get("max_size_w", 0))), max(0, int(params.get("max_size_h", 0))))

        rects = cascade.detectMultiScale(
            gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            flags=flags,
            minSize=min_size,
            maxSize=max_size,
        )

        label = str(params.get("label", "cascade_obj")).strip() or "cascade_obj"
        draw_mode = str(params.get("draw_mode", "rectangle"))
        thickness = max(1, int(params.get("draw_thickness", 2)))

        out = image.copy()
        detections: list[Detection] = []
        for (x, y, w, h) in rects:
            x, y, w, h = int(x), int(y), int(w), int(h)
            detections.append(Detection((x, y, w, h), label, 1.0))
            if draw_mode == "ellipse":
                center = (x + w // 2, y + h // 2)
                cv2.ellipse(out, center, (w // 2, h // 2), 0, 0, 360, (255, 0, 255), thickness)
            elif draw_mode == "circle":
                center = (x + w // 2, y + h // 2)
                radius = int(round((w + h) * 0.25))
                cv2.circle(out, center, radius, (255, 0, 0), thickness)
            elif draw_mode == "rectangle":
                cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), thickness)

        meta = {
            "detection_count": len(detections),
            "cascade_path": str(params.get("cascade_path", "")),
            "scale_factor": scale_factor,
            "min_neighbors": min_neighbors,
        }
        return {"image": out, "detections": detections, "meta": meta}


class HOGDescriptorConfigurableBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="HOGDescriptorConfigurable",
            title="HOG Descriptor (Configurable)",
            category="Detection",
            input_ports=[PortSpec("image", "image", "Input image for HOG feature extraction.")],
            output_ports=[
                PortSpec("feature_vector", "feature_vector", "Computed HOG descriptor vector."),
                PortSpec("image", "image", "Visualization image with ROI and gradients."),
                PortSpec("meta", "meta", "Descriptor config and vector length."),
            ],
            params=[
                ParamSpec("win_w", "int", 64, min_value=8, max_value=1024, step=1),
                ParamSpec("win_h", "int", 128, min_value=8, max_value=1024, step=1),
                ParamSpec("block_w", "int", 16, min_value=2, max_value=512, step=1),
                ParamSpec("block_h", "int", 16, min_value=2, max_value=512, step=1),
                ParamSpec("block_stride_x", "int", 8, min_value=1, max_value=256, step=1),
                ParamSpec("block_stride_y", "int", 8, min_value=1, max_value=256, step=1),
                ParamSpec("cell_w", "int", 8, min_value=1, max_value=256, step=1),
                ParamSpec("cell_h", "int", 8, min_value=1, max_value=256, step=1),
                ParamSpec("nbins", "int", 9, min_value=2, max_value=36, step=1),
                ParamSpec("deriv_aperture", "int", 1, min_value=0, max_value=7, step=1),
                ParamSpec("win_sigma", "float", -1.0, min_value=-1.0, max_value=50.0, step=0.1),
                ParamSpec("l2_hys_threshold", "float", 0.2, min_value=0.0, max_value=1.0, step=0.01),
                ParamSpec("gamma_correction", "bool", False),
                ParamSpec("nlevels", "int", 64, min_value=1, max_value=256, step=1),
                ParamSpec("signed_gradient", "bool", False),
                ParamSpec("region_mode", "enum", "center_crop_resize", options=["full_resize", "center_crop_resize"]),
                ParamSpec("roi_scale", "float", 0.6, min_value=0.1, max_value=1.0, step=0.01),
                ParamSpec("center_x", "float", 0.5, min_value=0.0, max_value=1.0, step=0.01),
                ParamSpec("center_y", "float", 0.5, min_value=0.0, max_value=1.0, step=0.01),
                ParamSpec("show_gradient", "bool", True),
            ],
            description="Fully configurable OpenCV HOGDescriptor block for feature extraction problems.",
        )

    def _validate_hog_geometry(self, win: tuple[int, int], block: tuple[int, int], stride: tuple[int, int], cell: tuple[int, int]) -> None:
        win_w, win_h = win
        bw, bh = block
        sx, sy = stride
        cw, ch = cell
        if bw > win_w or bh > win_h:
            raise ValueError("blockSize must be <= winSize")
        if bw % cw != 0 or bh % ch != 0:
            raise ValueError("blockSize must be divisible by cellSize")
        if (win_w - bw) % sx != 0 or (win_h - bh) % sy != 0:
            raise ValueError("(winSize - blockSize) must be divisible by blockStride")

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = ensure_bgr(inputs.get("image"))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]

        win = (max(8, int(params.get("win_w", 64))), max(8, int(params.get("win_h", 128))))
        block = (max(2, int(params.get("block_w", 16))), max(2, int(params.get("block_h", 16))))
        stride = (max(1, int(params.get("block_stride_x", 8))), max(1, int(params.get("block_stride_y", 8))))
        cell = (max(1, int(params.get("cell_w", 8))), max(1, int(params.get("cell_h", 8))))
        nbins = max(2, int(params.get("nbins", 9)))
        deriv_aperture = int(params.get("deriv_aperture", 1))
        win_sigma = float(params.get("win_sigma", -1.0))
        l2 = float(params.get("l2_hys_threshold", 0.2))
        gamma = bool(params.get("gamma_correction", False))
        nlevels = max(1, int(params.get("nlevels", 64)))
        signed_grad = bool(params.get("signed_gradient", False))
        self._validate_hog_geometry(win, block, stride, cell)

        hog = cv2.HOGDescriptor(
            _winSize=win,
            _blockSize=block,
            _blockStride=stride,
            _cellSize=cell,
            _nbins=nbins,
            _derivAperture=deriv_aperture,
            _winSigma=win_sigma,
            _histogramNormType=cv2.HOGDescriptor_L2Hys,
            _L2HysThreshold=l2,
            _gammaCorrection=gamma,
            _nlevels=nlevels,
            _signedGradient=signed_grad,
        )

        region_mode = str(params.get("region_mode", "center_crop_resize"))
        roi_scale = float(params.get("roi_scale", 0.6))
        cx_ratio = float(params.get("center_x", 0.5))
        cy_ratio = float(params.get("center_y", 0.5))
        show_grad = bool(params.get("show_gradient", True))

        if region_mode == "full_resize":
            x1, y1, x2, y2 = 0, 0, w, h
            roi = gray
        else:
            roi_h = max(8, int(min(h, 2 * w) * roi_scale))
            roi_w = max(8, int(max(1, roi_h * win[0] / max(1, win[1]))))
            roi_w = min(roi_w, w)
            roi_h = min(roi_h, h)
            cx = int(cx_ratio * (w - 1))
            cy = int(cy_ratio * (h - 1))
            x1 = max(0, min(w - roi_w, cx - roi_w // 2))
            y1 = max(0, min(h - roi_h, cy - roi_h // 2))
            x2, y2 = x1 + roi_w, y1 + roi_h
            roi = gray[y1:y2, x1:x2]

        roi_norm = cv2.resize(roi, win, interpolation=cv2.INTER_LINEAR)
        feat = hog.compute(roi_norm).reshape(-1)

        left = image.copy()
        cv2.rectangle(left, (x1, y1), (x2, y2), (0, 255, 0), 2)
        if show_grad:
            gx = cv2.Sobel(roi_norm, cv2.CV_32F, 1, 0, ksize=1)
            gy = cv2.Sobel(roi_norm, cv2.CV_32F, 0, 1, ksize=1)
            mag = cv2.magnitude(gx, gy)
            mag_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            right = cv2.applyColorMap(mag_u8, cv2.COLORMAP_TURBO)
        else:
            right = cv2.cvtColor(roi_norm, cv2.COLOR_GRAY2BGR)
        right = cv2.resize(right, (left.shape[1], left.shape[0]), interpolation=cv2.INTER_NEAREST)
        vis = cv2.hconcat([left, right])

        meta = {
            "vector_length": int(len(feat)),
            "win_size": {"w": win[0], "h": win[1]},
            "block_size": {"w": block[0], "h": block[1]},
            "block_stride": {"x": stride[0], "y": stride[1]},
            "cell_size": {"w": cell[0], "h": cell[1]},
            "nbins": nbins,
        }
        return {"feature_vector": feat, "image": vis, "meta": meta}


class HOGDetectMultiScaleAdvancedBlock(BlockBase):
    def __init__(self) -> None:
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="HOGDetectMultiScaleAdvanced",
            title="HOG DetectMultiScale (Advanced)",
            category="Detection",
            input_ports=[PortSpec("image", "image", "Input image for HOG+SVM person detection.")],
            output_ports=[
                PortSpec("image", "image", "Image with person detections."),
                PortSpec("detections", "detections", "Detected person bounding boxes with scores."),
                PortSpec("meta", "meta", "Raw/kept detection counts and parameters."),
            ],
            params=[
                ParamSpec("hit_threshold", "float", 0.0, min_value=-5.0, max_value=5.0, step=0.05),
                ParamSpec("win_stride_x", "int", 8, min_value=1, max_value=128, step=1),
                ParamSpec("win_stride_y", "int", 8, min_value=1, max_value=128, step=1),
                ParamSpec("padding_x", "int", 8, min_value=0, max_value=128, step=1),
                ParamSpec("padding_y", "int", 8, min_value=0, max_value=128, step=1),
                ParamSpec("scale", "float", 1.05, min_value=1.001, max_value=2.0, step=0.001),
                ParamSpec("final_threshold", "float", 2.0, min_value=0.0, max_value=20.0, step=0.1),
                ParamSpec("use_meanshift_grouping", "bool", False),
                ParamSpec("confidence_threshold", "float", 0.0, min_value=-10.0, max_value=10.0, step=0.01),
                ParamSpec("max_detections", "int", 0, min_value=0, max_value=10000, step=1),
                ParamSpec("draw_score", "bool", True),
            ],
            description="OpenCV HOGDescriptor.detectMultiScale with full key controls exposed.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = ensure_bgr(inputs.get("image"))
        hit = float(params.get("hit_threshold", 0.0))
        win_stride = (max(1, int(params.get("win_stride_x", 8))), max(1, int(params.get("win_stride_y", 8))))
        padding = (max(0, int(params.get("padding_x", 8))), max(0, int(params.get("padding_y", 8))))
        scale = max(1.001, float(params.get("scale", 1.05)))
        final_threshold = float(params.get("final_threshold", 2.0))
        meanshift = bool(params.get("use_meanshift_grouping", False))
        conf_threshold = float(params.get("confidence_threshold", 0.0))
        max_det = max(0, int(params.get("max_detections", 0)))
        draw_score = bool(params.get("draw_score", True))

        try:
            rects, weights = self.hog.detectMultiScale(
                image,
                hit,
                win_stride,
                padding,
                scale,
                final_threshold,
                meanshift,
            )
        except Exception:  # noqa: BLE001
            rects, weights = self.hog.detectMultiScale(
                image,
                hit,
                win_stride,
                padding,
                scale,
                final_threshold,
            )

        out = image.copy()
        detections: list[Detection] = []
        for (x, y, w, h), score in zip(rects, weights):
            score_f = float(score)
            if score_f < conf_threshold:
                continue
            x, y, w, h = int(x), int(y), int(w), int(h)
            detections.append(Detection((x, y, w, h), "person", score_f))
            if max_det > 0 and len(detections) > max_det:
                break
            color = (0, 255, 0) if score_f >= 0.7 else (255, 0, 0) if score_f >= 0.3 else (0, 0, 255)
            cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
            if draw_score:
                cv2.putText(out, f"{score_f:.2f}", (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        meta = {"raw_rects": int(len(rects)), "kept_rects": int(len(detections))}
        return {"image": out, "detections": detections, "meta": meta}


class DetectionStyleDrawBlock(BlockBase):
    LINE_TYPES = {"8": cv2.LINE_8, "4": cv2.LINE_4, "aa": cv2.LINE_AA}
    SHAPES = ["rectangle", "ellipse", "circle"]

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="DetectionStyleDraw",
            title="Detection Style Draw",
            category="Detection",
            input_ports=[
                PortSpec("image", "image", "Image canvas to draw detections on."),
                PortSpec("detections", "detections", "Detections list with bbox/label/score."),
            ],
            output_ports=[
                PortSpec("image", "image", "Styled detection overlay image."),
                PortSpec("detections", "detections", "Passthrough detections."),
                PortSpec("meta", "meta", "Styled drawing summary and count."),
            ],
            params=[
                ParamSpec("shape", "enum", "rectangle", options=cls.SHAPES),
                ParamSpec("line_type", "enum", "8", options=list(cls.LINE_TYPES.keys())),
                ParamSpec("thickness", "int", 2, min_value=1, max_value=20, step=1),
                ParamSpec("show_label", "bool", True),
                ParamSpec("show_score", "bool", True),
                ParamSpec("font_scale", "float", 0.45, min_value=0.1, max_value=4.0, step=0.05),
                ParamSpec("filter_by_score", "bool", False),
                ParamSpec(
                    "min_score",
                    "float",
                    -10.0,
                    min_value=-10.0,
                    max_value=10.0,
                    step=0.01,
                    visible_if={"filter_by_score": [True]},
                ),
                ParamSpec(
                    "max_score",
                    "float",
                    10.0,
                    min_value=-10.0,
                    max_value=10.0,
                    step=0.01,
                    visible_if={"filter_by_score": [True]},
                ),
                ParamSpec("score_low", "float", 0.13, min_value=-10.0, max_value=10.0, step=0.01),
                ParamSpec("score_mid", "float", 0.3, min_value=-10.0, max_value=10.0, step=0.01),
                ParamSpec("low_b", "int", 0, min_value=0, max_value=255, step=1),
                ParamSpec("low_g", "int", 0, min_value=0, max_value=255, step=1),
                ParamSpec("low_r", "int", 255, min_value=0, max_value=255, step=1),
                ParamSpec("mid_b", "int", 255, min_value=0, max_value=255, step=1),
                ParamSpec("mid_g", "int", 0, min_value=0, max_value=255, step=1),
                ParamSpec("mid_r", "int", 0, min_value=0, max_value=255, step=1),
                ParamSpec("high_b", "int", 0, min_value=0, max_value=255, step=1),
                ParamSpec("high_g", "int", 255, min_value=0, max_value=255, step=1),
                ParamSpec("high_r", "int", 0, min_value=0, max_value=255, step=1),
                ParamSpec("label_filter", "str", ""),
            ],
            description="Styled drawing block with rectangle/ellipse/circle and confidence color bands.",
        )

    def _draw_shape(
        self,
        image: np.ndarray,
        shape: str,
        bbox: tuple[int, int, int, int],
        color: tuple[int, int, int],
        thickness: int,
        line_type: int,
    ) -> None:
        x, y, w, h = bbox
        if shape == "ellipse":
            center = (x + w // 2, y + h // 2)
            cv2.ellipse(image, center, (w // 2, h // 2), 0, 0, 360, color, thickness, line_type)
        elif shape == "circle":
            center = (x + w // 2, y + h // 2)
            radius = int(round((w + h) * 0.25))
            cv2.circle(image, center, radius, color, thickness, line_type)
        else:
            cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness, line_type)

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = ensure_bgr(inputs.get("image"))
        detections_in = inputs.get("detections") or []
        shape = str(params.get("shape", "rectangle"))
        line_type = self.LINE_TYPES.get(str(params.get("line_type", "8")), cv2.LINE_8)
        thickness = max(1, int(params.get("thickness", 2)))
        show_label = bool(params.get("show_label", True))
        show_score = bool(params.get("show_score", True))
        font_scale = float(params.get("font_scale", 0.45))
        filter_by_score = bool(params.get("filter_by_score", False))
        min_score = float(params.get("min_score", -10.0))
        max_score = float(params.get("max_score", 10.0))
        if max_score < min_score:
            max_score = min_score
        score_low = float(params.get("score_low", 0.13))
        score_mid = max(score_low, float(params.get("score_mid", 0.3)))
        low_color = (int(params.get("low_b", 0)), int(params.get("low_g", 0)), int(params.get("low_r", 255)))
        mid_color = (int(params.get("mid_b", 255)), int(params.get("mid_g", 0)), int(params.get("mid_r", 0)))
        high_color = (int(params.get("high_b", 0)), int(params.get("high_g", 255)), int(params.get("high_r", 0)))
        label_filter = str(params.get("label_filter", "")).strip().lower()

        out = image.copy()
        drawn = 0
        detections: list[Detection] = []
        for det in detections_in:
            if isinstance(det, Detection):
                x, y, w, h = det.bbox
                label = det.label
                score = float(det.score)
                extra = dict(det.extra)
            else:
                x, y, w, h = tuple(det.get("bbox", (0, 0, 0, 0)))
                label = str(det.get("label", "obj"))
                score = float(det.get("score", 1.0))
                extra = dict(det.get("extra", {}))
            if label_filter and label_filter not in label.lower():
                continue
            if filter_by_score and not (min_score <= score <= max_score):
                continue

            bbox = (int(x), int(y), int(w), int(h))
            color = high_color if score >= score_mid else mid_color if score >= score_low else low_color
            self._draw_shape(out, shape, bbox, color, thickness, line_type)
            text = ""
            if show_label:
                text += label
            if show_score:
                text += (" " if text else "") + f"{score:.2f}"
            if text:
                cv2.putText(out, text, (bbox[0], max(12, bbox[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1, line_type)

            detections.append(Detection(bbox, label, score, extra))
            drawn += 1

        return {
            "image": out,
            "detections": detections,
            "meta": {
                "drawn_count": drawn,
                "shape": shape,
                "filter_by_score": filter_by_score,
                "min_score": min_score,
                "max_score": max_score,
            },
        }


class DlibHOGFaceDetectBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="DlibHOGFaceDetect",
            title="Dlib HOG Face Detect",
            category="Detection",
            input_ports=[PortSpec("image", "image", "Input image for dlib HOG face detector.")],
            output_ports=[
                PortSpec("image", "image", "Image with dlib face boxes."),
                PortSpec("detections", "detections", "Face detections from dlib HOG detector."),
                PortSpec("meta", "meta", "Face detection count and dlib metadata."),
            ],
            params=[
                ParamSpec("upsample_num_times", "int", 1, min_value=0, max_value=8, step=1),
                ParamSpec("adjust_threshold", "float", 0.0, min_value=-5.0, max_value=5.0, step=0.05),
                ParamSpec("draw_thickness", "int", 2, min_value=1, max_value=20, step=1),
            ],
            description="Optional non-OpenCV block mirroring course dlib HOG face detection examples.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        try:
            import dlib  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("dlib is not installed. Install dlib to use DlibHOGFaceDetect.") from exc

        image = ensure_bgr(inputs.get("image"))
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        upsample = max(0, int(params.get("upsample_num_times", 1)))
        adjust_threshold = float(params.get("adjust_threshold", 0.0))
        thickness = max(1, int(params.get("draw_thickness", 2)))

        detector = dlib.get_frontal_face_detector()
        rects, scores, _ = detector.run(rgb, upsample, adjust_threshold)

        out = image.copy()
        detections: list[Detection] = []
        for rect, score in zip(rects, scores):
            x1, y1, x2, y2 = int(rect.left()), int(rect.top()), int(rect.right()), int(rect.bottom())
            w = max(0, x2 - x1)
            h = max(0, y2 - y1)
            detections.append(Detection((x1, y1, w, h), "face", float(score)))
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 255), thickness)
            cv2.putText(out, f"{float(score):.2f}", (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        return {"image": out, "detections": detections, "meta": {"face_count": len(detections), "backend": "dlib_hog"}}
