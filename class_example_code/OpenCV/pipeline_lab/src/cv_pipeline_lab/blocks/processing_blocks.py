from __future__ import annotations

import json
from typing import Any

import cv2
import numpy as np

from cv_pipeline_lab.blocks.base import BlockBase
from cv_pipeline_lab.blocks.utils import ensure_bgr, ensure_gray, gamma_correct, odd_ksize
from cv_pipeline_lab.core.types import BlockSpec, Detection, ParamSpec, PortSpec, RunContext


class PreprocessPipelineBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="PreprocessPipeline",
            title="Preprocess Pipeline",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[
                ParamSpec("alpha", "float", 1.0, min_value=0.1, max_value=3.0, step=0.05),
                ParamSpec("beta", "int", 0, min_value=-100, max_value=100, step=1),
                ParamSpec("gamma", "float", 1.0, min_value=0.1, max_value=3.0, step=0.05),
                ParamSpec("gray", "bool", False),
                ParamSpec("equalize_hist", "bool", False),
                ParamSpec("blur_k", "int", 1, min_value=1, max_value=31, step=2),
            ],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        img = inputs.get("image")
        if img is None:
            raise ValueError("PreprocessPipeline expects image")
        out = ensure_bgr(img)

        alpha = float(params.get("alpha", 1.0))
        beta = int(params.get("beta", 0))
        gamma = float(params.get("gamma", 1.0))
        gray = bool(params.get("gray", False))
        eq = bool(params.get("equalize_hist", False))
        blur_k = odd_ksize(params.get("blur_k", 1), 1)

        out = cv2.convertScaleAbs(out, alpha=alpha, beta=beta)
        out = gamma_correct(out, gamma)
        if blur_k > 1:
            out = cv2.GaussianBlur(out, (blur_k, blur_k), 0)

        if gray:
            g = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
            if eq:
                g = cv2.equalizeHist(g)
            out = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
        elif eq:
            ycrcb = cv2.cvtColor(out, cv2.COLOR_BGR2YCrCb)
            ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
            out = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

        return {"image": out}


class ResizeImageBlock(BlockBase):
    INTERP_MAP = {
        "nearest": cv2.INTER_NEAREST,
        "linear": cv2.INTER_LINEAR,
        "area": cv2.INTER_AREA,
        "cubic": cv2.INTER_CUBIC,
        "lanczos4": cv2.INTER_LANCZOS4,
    }

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ResizeImage",
            title="Resize Image",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[
                ParamSpec("mode", "enum", "dsize", options=["dsize", "scale"]),
                ParamSpec("width", "int", 640, min_value=1, max_value=10000, step=1, visible_if={"mode": ["dsize"]}),
                ParamSpec("height", "int", 480, min_value=1, max_value=10000, step=1, visible_if={"mode": ["dsize"]}),
                ParamSpec("fx", "float", 1.0, min_value=0.01, max_value=20.0, step=0.01, visible_if={"mode": ["scale"]}),
                ParamSpec("fy", "float", 1.0, min_value=0.01, max_value=20.0, step=0.01, visible_if={"mode": ["scale"]}),
                ParamSpec("interpolation", "enum", "linear", options=list(cls.INTERP_MAP.keys())),
            ],
            description="cv2.resize with full dsize or fx/fy scaling options.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        img = inputs.get("image")
        if img is None:
            raise ValueError("ResizeImage expects image")
        img = ensure_bgr(img)
        mode = str(params.get("mode", "dsize"))
        interp = self.INTERP_MAP.get(str(params.get("interpolation", "linear")), cv2.INTER_LINEAR)
        if mode == "scale":
            fx = max(0.01, float(params.get("fx", 1.0)))
            fy = max(0.01, float(params.get("fy", 1.0)))
            out = cv2.resize(img, None, fx=fx, fy=fy, interpolation=interp)
        else:
            w = max(1, int(params.get("width", 640)))
            h = max(1, int(params.get("height", 480)))
            out = cv2.resize(img, (w, h), interpolation=interp)
        return {"image": out}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        mode = str(params.get("mode", "dsize"))
        interp = str(params.get("interpolation", "linear"))
        if mode == "scale":
            return (
                "# Resize Image (scale)\n"
                f"fx = {max(0.01, float(params.get('fx', 1.0)))}\n"
                f"fy = {max(0.01, float(params.get('fy', 1.0)))}\n"
                f"image_out = cv2.resize(image, None, fx=fx, fy=fy, interpolation=cv2.INTER_{interp.upper()})"
            )
        return (
            "# Resize Image (dsize)\n"
            f"width = {max(1, int(params.get('width', 640)))}\n"
            f"height = {max(1, int(params.get('height', 480)))}\n"
            f"image_out = cv2.resize(image, (width, height), interpolation=cv2.INTER_{interp.upper()})"
        )


class ImageCropBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ImageCrop",
            title="Image Crop",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image"), PortSpec("meta", "meta")],
            params=[
                ParamSpec("x", "int", 0, min_value=0, max_value=10000, step=1),
                ParamSpec("y", "int", 0, min_value=0, max_value=10000, step=1),
                ParamSpec("width", "int", 0, min_value=0, max_value=10000, step=1),
                ParamSpec("height", "int", 0, min_value=0, max_value=10000, step=1),
            ],
            description="Crop a rectangular ROI from the input image. Width/height <= 0 means use remaining image extent.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        img = inputs.get("image")
        if img is None:
            raise ValueError("ImageCrop expects image")
        img = ensure_bgr(img)
        h, w = img.shape[:2]

        x = max(0, min(w - 1, int(params.get("x", 0))))
        y = max(0, min(h - 1, int(params.get("y", 0))))
        crop_w = int(params.get("width", 0))
        crop_h = int(params.get("height", 0))
        if crop_w <= 0:
            crop_w = w - x
        if crop_h <= 0:
            crop_h = h - y

        x2 = min(w, x + max(1, crop_w))
        y2 = min(h, y + max(1, crop_h))
        if x2 <= x or y2 <= y:
            raise ValueError("Invalid crop rectangle")

        out = img[y:y2, x:x2].copy()
        meta = {
            "crop_box": {"x": x, "y": y, "width": x2 - x, "height": y2 - y},
            "source_size": {"width": w, "height": h},
        }
        return {"image": out, "meta": meta}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        x = int(params.get("x", 0))
        y = int(params.get("y", 0))
        width = int(params.get("width", 0))
        height = int(params.get("height", 0))
        return (
            "# Image Crop\n"
            f"x, y = ({x}, {y})\n"
            f"width, height = ({width}, {height})\n"
            "h, w = image.shape[:2]\n"
            "if width <= 0:\n"
            "    width = w - x\n"
            "if height <= 0:\n"
            "    height = h - y\n"
            "x2 = min(w, x + max(1, width))\n"
            "y2 = min(h, y + max(1, height))\n"
            "image_out = image[y:y2, x:x2].copy()"
        )


class ContrastAdjustmentBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ContrastAdjustment",
            title="Contrast Adjustment",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[
                ParamSpec("alpha", "float", 1.2, min_value=0.0, max_value=5.0, step=0.05, help_text="Contrast scale"),
                ParamSpec("beta", "int", 0, min_value=-255, max_value=255, step=1, help_text="Brightness shift"),
            ],
            description="Linear intensity transform: I_out = alpha * I_in + beta",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        img = inputs.get("image")
        if img is None:
            raise ValueError("ContrastAdjustment expects image")
        img = ensure_bgr(img)
        alpha = float(params.get("alpha", 1.2))
        beta = int(params.get("beta", 0))
        out = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        return {"image": out}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        alpha = float(params.get("alpha", 1.2))
        beta = int(params.get("beta", 0))
        return (
            "# Contrast Adjustment\n"
            f"alpha = {alpha}\n"
            f"beta = {beta}\n"
            "image_out = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)"
        )


class LogTransformBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="LogTransform",
            title="Log Transform",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[
                ParamSpec(
                    "gain",
                    "float",
                    1.0,
                    min_value=0.0,
                    max_value=10.0,
                    step=0.05,
                    help_text="Gain multiplier on log output",
                ),
                ParamSpec(
                    "normalize",
                    "bool",
                    True,
                    help_text="Normalize result to full 0..255 range after log",
                ),
            ],
            description="Log transform: s = c * log(1 + r), useful for dynamic range compression.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        img = inputs.get("image")
        if img is None:
            raise ValueError("LogTransform expects image")
        img = ensure_bgr(img).astype(np.float32)
        gain = float(params.get("gain", 1.0))
        do_norm = bool(params.get("normalize", True))

        c = (255.0 / np.log(256.0)) * gain
        out = c * np.log1p(img)
        if do_norm:
            out = cv2.normalize(out, None, 0, 255, cv2.NORM_MINMAX)
        out = np.clip(out, 0, 255).astype(np.uint8)
        return {"image": out}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        gain = float(params.get("gain", 1.0))
        do_norm = bool(params.get("normalize", True))
        return (
            "# Log Transform\n"
            f"gain = {gain}\n"
            f"normalize = {do_norm}\n"
            "img_f32 = image.astype(np.float32)\n"
            "c = (255.0 / np.log(256.0)) * gain\n"
            "image_out = c * np.log1p(img_f32)\n"
            "if normalize:\n"
            "    image_out = cv2.normalize(image_out, None, 0, 255, cv2.NORM_MINMAX)\n"
            "image_out = np.clip(image_out, 0, 255).astype(np.uint8)"
        )


class GammaTransformBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="GammaTransform",
            title="Gamma Transform",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[
                ParamSpec("gamma", "float", 1.0, min_value=0.05, max_value=5.0, step=0.05),
                ParamSpec("gain", "float", 1.0, min_value=0.0, max_value=5.0, step=0.05),
            ],
            description="Power-law transform: I_out = gain * (I_in / 255)^gamma * 255",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        img = inputs.get("image")
        if img is None:
            raise ValueError("GammaTransform expects image")
        img = ensure_bgr(img).astype(np.float32) / 255.0
        gamma = max(0.01, float(params.get("gamma", 1.0)))
        gain = float(params.get("gain", 1.0))
        out = gain * np.power(img, gamma) * 255.0
        out = np.clip(out, 0, 255).astype(np.uint8)
        return {"image": out}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        gamma = float(params.get("gamma", 1.0))
        gain = float(params.get("gain", 1.0))
        return (
            "# Gamma Transform\n"
            f"gamma = {max(0.01, gamma)}\n"
            f"gain = {gain}\n"
            "img_norm = image.astype(np.float32) / 255.0\n"
            "image_out = gain * np.power(img_norm, gamma) * 255.0\n"
            "image_out = np.clip(image_out, 0, 255).astype(np.uint8)"
        )


class InRangeMaskBlock(BlockBase):
    COLOR_MAP = {
        "bgr": None,
        "hsv": cv2.COLOR_BGR2HSV,
        "rgb": cv2.COLOR_BGR2RGB,
        "gray": cv2.COLOR_BGR2GRAY,
    }

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="InRangeMask",
            title="InRange Mask",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("mask", "mask"), PortSpec("image", "image")],
            params=[
                ParamSpec("color_space", "enum", "hsv", options=list(cls.COLOR_MAP.keys())),
                ParamSpec("low_0", "int", 0, min_value=0, max_value=255, step=1),
                ParamSpec("low_1", "int", 0, min_value=0, max_value=255, step=1),
                ParamSpec("low_2", "int", 0, min_value=0, max_value=255, step=1),
                ParamSpec("high_0", "int", 255, min_value=0, max_value=255, step=1),
                ParamSpec("high_1", "int", 255, min_value=0, max_value=255, step=1),
                ParamSpec("high_2", "int", 255, min_value=0, max_value=255, step=1),
            ],
            description="cv2.inRange on BGR/HSV/RGB/GRAY converted input.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        img = inputs.get("image")
        if img is None:
            raise ValueError("InRangeMask expects image")
        src = ensure_bgr(img)
        color_space = str(params.get("color_space", "hsv"))
        code = self.COLOR_MAP.get(color_space, cv2.COLOR_BGR2HSV)
        proc = src if code is None else cv2.cvtColor(src, code)

        low = [int(params.get("low_0", 0)), int(params.get("low_1", 0)), int(params.get("low_2", 0))]
        high = [int(params.get("high_0", 255)), int(params.get("high_1", 255)), int(params.get("high_2", 255))]
        if proc.ndim == 2:
            lowerb = np.array([low[0]], dtype=np.uint8)
            upperb = np.array([high[0]], dtype=np.uint8)
        else:
            lowerb = np.array(low[: proc.shape[2]], dtype=np.uint8)
            upperb = np.array(high[: proc.shape[2]], dtype=np.uint8)

        mask = cv2.inRange(proc, lowerb, upperb)
        masked = cv2.bitwise_and(src, src, mask=mask)
        return {"mask": mask, "image": masked}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        return (
            "# InRange Mask\n"
            f"color_space = {str(params.get('color_space', 'hsv'))!r}\n"
            "proc = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) if color_space == 'hsv' else image\n"
            f"lowerb = np.array([{int(params.get('low_0', 0))}, {int(params.get('low_1', 0))}, {int(params.get('low_2', 0))}], dtype=np.uint8)\n"
            f"upperb = np.array([{int(params.get('high_0', 255))}, {int(params.get('high_1', 255))}, {int(params.get('high_2', 255))}], dtype=np.uint8)\n"
            "mask = cv2.inRange(proc, lowerb, upperb)\n"
            "image_out = cv2.bitwise_and(image, image, mask=mask)"
        )


class DenoiseBlurBlock(BlockBase):
    BORDER_MAP = {
        "default": cv2.BORDER_DEFAULT,
        "reflect": cv2.BORDER_REFLECT,
        "replicate": cv2.BORDER_REPLICATE,
        "constant": cv2.BORDER_CONSTANT,
        "reflect101": cv2.BORDER_REFLECT_101,
    }

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="DenoiseBlur",
            title="Denoise / Blur",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[
                ParamSpec("method", "enum", "box", options=["box", "gaussian", "median", "bilateral"]),
                ParamSpec(
                    "box_ksize_x",
                    "int",
                    5,
                    label="Box Kernel X",
                    min_value=1,
                    max_value=101,
                    step=1,
                    visible_if={"method": ["box"]},
                ),
                ParamSpec(
                    "box_ksize_y",
                    "int",
                    5,
                    label="Box Kernel Y",
                    min_value=1,
                    max_value=101,
                    step=1,
                    visible_if={"method": ["box"]},
                ),
                ParamSpec(
                    "box_normalize",
                    "bool",
                    True,
                    label="Box Normalize",
                    visible_if={"method": ["box"]},
                ),
                ParamSpec(
                    "box_border",
                    "enum",
                    "default",
                    label="Box Border",
                    options=list(cls.BORDER_MAP.keys()),
                    visible_if={"method": ["box"]},
                ),
                ParamSpec(
                    "gauss_ksize_x",
                    "int",
                    5,
                    label="Gaussian Kernel X",
                    min_value=1,
                    max_value=101,
                    step=2,
                    visible_if={"method": ["gaussian"]},
                ),
                ParamSpec(
                    "gauss_ksize_y",
                    "int",
                    5,
                    label="Gaussian Kernel Y",
                    min_value=1,
                    max_value=101,
                    step=2,
                    visible_if={"method": ["gaussian"]},
                ),
                ParamSpec(
                    "gauss_sigma_x",
                    "float",
                    1.2,
                    label="Gaussian Sigma X",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.1,
                    visible_if={"method": ["gaussian"]},
                ),
                ParamSpec(
                    "gauss_sigma_y",
                    "float",
                    0.0,
                    label="Gaussian Sigma Y",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.1,
                    visible_if={"method": ["gaussian"]},
                ),
                ParamSpec(
                    "gauss_border",
                    "enum",
                    "default",
                    label="Gaussian Border",
                    options=list(cls.BORDER_MAP.keys()),
                    visible_if={"method": ["gaussian"]},
                ),
                ParamSpec(
                    "median_ksize",
                    "int",
                    5,
                    label="Median Kernel",
                    min_value=3,
                    max_value=101,
                    step=2,
                    visible_if={"method": ["median"]},
                ),
                ParamSpec(
                    "bilateral_d",
                    "int",
                    9,
                    label="Bilateral Diameter",
                    min_value=1,
                    max_value=101,
                    step=1,
                    visible_if={"method": ["bilateral"]},
                ),
                ParamSpec(
                    "bilateral_sigma_color",
                    "float",
                    80.0,
                    label="Bilateral Sigma Color",
                    min_value=1.0,
                    max_value=500.0,
                    step=1.0,
                    visible_if={"method": ["bilateral"]},
                ),
                ParamSpec(
                    "bilateral_sigma_space",
                    "float",
                    80.0,
                    label="Bilateral Sigma Space",
                    min_value=1.0,
                    max_value=500.0,
                    step=1.0,
                    visible_if={"method": ["bilateral"]},
                ),
                ParamSpec(
                    "bilateral_border",
                    "enum",
                    "default",
                    label="Bilateral Border",
                    options=list(cls.BORDER_MAP.keys()),
                    visible_if={"method": ["bilateral"]},
                ),
            ],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        img = inputs.get("image")
        if img is None:
            raise ValueError("DenoiseBlur expects image")
        img = ensure_bgr(img)

        method = str(params.get("method", "box"))
        if method == "gaussian":
            kx = odd_ksize(params.get("gauss_ksize_x", 5), 1)
            ky = odd_ksize(params.get("gauss_ksize_y", 5), 1)
            sigma_x = float(params.get("gauss_sigma_x", 1.2))
            sigma_y = float(params.get("gauss_sigma_y", 0.0))
            border = self.BORDER_MAP.get(str(params.get("gauss_border", "default")), cv2.BORDER_DEFAULT)
            out = cv2.GaussianBlur(img, (kx, ky), sigmaX=sigma_x, sigmaY=sigma_y, borderType=border)
        elif method == "median":
            k = odd_ksize(params.get("median_ksize", 5), 3)
            out = cv2.medianBlur(img, k)
        elif method == "bilateral":
            d = max(1, int(params.get("bilateral_d", 9)))
            sigma_color = float(params.get("bilateral_sigma_color", 80.0))
            sigma_space = float(params.get("bilateral_sigma_space", 80.0))
            border = self.BORDER_MAP.get(str(params.get("bilateral_border", "default")), cv2.BORDER_DEFAULT)
            out = cv2.bilateralFilter(img, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space, borderType=border)
        else:
            kx = max(1, int(params.get("box_ksize_x", 5)))
            ky = max(1, int(params.get("box_ksize_y", 5)))
            normalize = bool(params.get("box_normalize", True))
            border = self.BORDER_MAP.get(str(params.get("box_border", "default")), cv2.BORDER_DEFAULT)
            out = cv2.boxFilter(img, ddepth=-1, ksize=(kx, ky), normalize=normalize, borderType=border)
        return {"image": out}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        method = str(params.get("method", "box"))
        if method == "gaussian":
            return (
                "# Denoise / Blur (Gaussian)\n"
                f"kx, ky = ({odd_ksize(params.get('gauss_ksize_x', 5), 1)}, {odd_ksize(params.get('gauss_ksize_y', 5), 1)})\n"
                f"sigma_x = {float(params.get('gauss_sigma_x', 1.2))}\n"
                f"sigma_y = {float(params.get('gauss_sigma_y', 0.0))}\n"
                "image_out = cv2.GaussianBlur(image, (kx, ky), sigmaX=sigma_x, sigmaY=sigma_y)"
            )
        if method == "median":
            return (
                "# Denoise / Blur (Median)\n"
                f"k = {odd_ksize(params.get('median_ksize', 5), 3)}\n"
                "image_out = cv2.medianBlur(image, k)"
            )
        if method == "bilateral":
            return (
                "# Denoise / Blur (Bilateral)\n"
                f"d = {max(1, int(params.get('bilateral_d', 9)))}\n"
                f"sigma_color = {float(params.get('bilateral_sigma_color', 80.0))}\n"
                f"sigma_space = {float(params.get('bilateral_sigma_space', 80.0))}\n"
                "image_out = cv2.bilateralFilter(image, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)"
            )
        return (
            "# Denoise / Blur (Box)\n"
            f"kx, ky = ({max(1, int(params.get('box_ksize_x', 5)))}, {max(1, int(params.get('box_ksize_y', 5)))})\n"
            f"normalize = {bool(params.get('box_normalize', True))}\n"
            "image_out = cv2.boxFilter(image, ddepth=-1, ksize=(kx, ky), normalize=normalize)"
        )


class SharpenBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="Sharpen",
            title="Sharpen (Laplacian/Gradient)",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[
                ParamSpec("method", "enum", "laplacian", options=["laplacian", "gradient"]),
                ParamSpec("kernel_size", "enum", "3", options=["1", "3", "5", "7"]),
                ParamSpec("alpha", "float", 1.0, min_value=0.0, max_value=3.0, step=0.05),
                ParamSpec("blend", "float", 0.4, min_value=0.0, max_value=1.0, step=0.05),
            ],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        img = inputs.get("image")
        if img is None:
            raise ValueError("Sharpen expects image")
        img = ensure_bgr(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        method = str(params.get("method", "laplacian"))
        ksize = int(str(params.get("kernel_size", "3")))
        alpha = float(params.get("alpha", 1.0))
        blend = float(params.get("blend", 0.4))

        if method == "gradient":
            gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=ksize)
            gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=ksize)
            mag = cv2.magnitude(gx, gy)
            mag_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            grad_vis = cv2.applyColorMap(mag_u8, cv2.COLORMAP_TURBO)
            out = cv2.addWeighted(img, 1.0 - blend, grad_vis, blend, 0)
        else:
            lap = cv2.Laplacian(gray, cv2.CV_32F, ksize=ksize)
            out_gray = cv2.convertScaleAbs(gray - alpha * lap)
            out = cv2.cvtColor(out_gray, cv2.COLOR_GRAY2BGR)

        return {"image": out}


class Filter2DBlock(BlockBase):
    DDEPTH_MAP = {
        "-1": -1,
        "cv_8u": cv2.CV_8U,
        "cv_16u": cv2.CV_16U,
        "cv_16s": cv2.CV_16S,
        "cv_32f": cv2.CV_32F,
        "cv_64f": cv2.CV_64F,
    }
    BORDER_MAP = {
        "default": cv2.BORDER_DEFAULT,
        "constant": cv2.BORDER_CONSTANT,
        "reflect": cv2.BORDER_REFLECT,
        "replicate": cv2.BORDER_REPLICATE,
        "reflect101": cv2.BORDER_REFLECT_101,
    }

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="Filter2D",
            title="Filter2D",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image")],
            params=[
                ParamSpec("ddepth", "enum", "-1", options=list(cls.DDEPTH_MAP.keys())),
                ParamSpec("kernel_json", "str", "[[0,-1,0],[-1,5,-1],[0,-1,0]]", label="Kernel (JSON)"),
                ParamSpec("anchor_x", "int", -1, min_value=-1, max_value=100, step=1),
                ParamSpec("anchor_y", "int", -1, min_value=-1, max_value=100, step=1),
                ParamSpec("delta", "float", 0.0, min_value=-255.0, max_value=255.0, step=0.1),
                ParamSpec("border_type", "enum", "default", options=list(cls.BORDER_MAP.keys())),
            ],
            description="Full cv2.filter2D with editable kernel, anchor, delta, and borderType.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = inputs.get("image")
        if image is None:
            raise ValueError("Filter2D expects image")
        img = ensure_bgr(image)

        kernel_json = str(params.get("kernel_json", "[[0,-1,0],[-1,5,-1],[0,-1,0]]")).strip()
        try:
            kernel_arr = np.array(json.loads(kernel_json), dtype=np.float32)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid kernel_json: {exc}") from exc
        if kernel_arr.ndim != 2 or kernel_arr.size == 0:
            raise ValueError("kernel_json must decode to a non-empty 2D matrix")

        ddepth = self.DDEPTH_MAP.get(str(params.get("ddepth", "-1")), -1)
        anchor_x = int(params.get("anchor_x", -1))
        anchor_y = int(params.get("anchor_y", -1))
        anchor = (anchor_x, anchor_y)
        delta = float(params.get("delta", 0.0))
        border = self.BORDER_MAP.get(str(params.get("border_type", "default")), cv2.BORDER_DEFAULT)

        out = cv2.filter2D(img, ddepth=ddepth, kernel=kernel_arr, anchor=anchor, delta=delta, borderType=border)
        return {"image": out}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        return (
            "# Filter2D\n"
            f"kernel = np.array({str(params.get('kernel_json', '[[0,-1,0],[-1,5,-1],[0,-1,0]]'))}, dtype=np.float32)\n"
            f"image_out = cv2.filter2D(image, ddepth={cls.DDEPTH_MAP.get(str(params.get('ddepth', '-1')), -1)}, "
            f"kernel=kernel, anchor=({int(params.get('anchor_x', -1))}, {int(params.get('anchor_y', -1))}), "
            f"delta={float(params.get('delta', 0.0))})"
        )


class CannyEdgeBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="CannyEdge",
            title="Canny Edge",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("mask", "mask"), PortSpec("image", "image")],
            params=[
                ParamSpec("low", "int", 100, min_value=0, max_value=500, step=1),
                ParamSpec("high", "int", 200, min_value=1, max_value=500, step=1),
                ParamSpec("aperture", "enum", "3", options=["3", "5", "7"]),
                ParamSpec("l2gradient", "bool", False),
                ParamSpec("dilate", "int", 0, min_value=0, max_value=5, step=1),
                ParamSpec("erode", "int", 0, min_value=0, max_value=5, step=1),
            ],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        img = inputs.get("image")
        if img is None:
            raise ValueError("CannyEdge expects image")
        gray = ensure_gray(img)
        low = int(params.get("low", 100))
        high = max(low + 1, int(params.get("high", 200)))
        aperture = int(str(params.get("aperture", "3")))
        l2 = bool(params.get("l2gradient", False))
        dilate = int(params.get("dilate", 0))
        erode = int(params.get("erode", 0))

        mask = cv2.Canny(gray, low, high, apertureSize=aperture, L2gradient=l2)
        if dilate > 0:
            mask = cv2.dilate(mask, np.ones((3, 3), dtype=np.uint8), iterations=dilate)
        if erode > 0:
            mask = cv2.erode(mask, np.ones((3, 3), dtype=np.uint8), iterations=erode)

        return {"mask": mask, "image": cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)}


class SimpleThresholdBlock(BlockBase):
    THRESH_MODES = {
        "binary": cv2.THRESH_BINARY,
        "binary_inv": cv2.THRESH_BINARY_INV,
        "trunc": cv2.THRESH_TRUNC,
        "tozero": cv2.THRESH_TOZERO,
        "tozero_inv": cv2.THRESH_TOZERO_INV,
    }

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="SimpleThreshold",
            title="Simple Threshold",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("mask", "mask"), PortSpec("image", "image")],
            params=[
                ParamSpec("thresh", "int", 127, min_value=0, max_value=255, step=1),
                ParamSpec("max_value", "int", 255, min_value=0, max_value=255, step=1),
                ParamSpec("type", "enum", "binary", options=list(cls.THRESH_MODES.keys())),
                ParamSpec("pre_blur", "int", 1, min_value=1, max_value=31, step=2),
                ParamSpec("otsu", "bool", False),
            ],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        gray = ensure_gray(inputs.get("image"))
        if gray is None:
            raise ValueError("SimpleThreshold expects image")

        thresh = int(params.get("thresh", 127))
        max_value = int(params.get("max_value", 255))
        mode_name = str(params.get("type", "binary"))
        mode = self.THRESH_MODES.get(mode_name, cv2.THRESH_BINARY)
        pre_blur = odd_ksize(params.get("pre_blur", 1), 1)
        otsu = bool(params.get("otsu", False))

        if pre_blur > 1:
            gray = cv2.GaussianBlur(gray, (pre_blur, pre_blur), 0)
        if otsu:
            mode = mode | cv2.THRESH_OTSU
        _, mask = cv2.threshold(gray, thresh, max_value, mode)
        return {"mask": mask, "image": cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)}


class AdaptiveThresholdBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="AdaptiveThreshold",
            title="Adaptive Threshold",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("mask", "mask"), PortSpec("image", "image")],
            params=[
                ParamSpec("method", "enum", "gaussian", options=["mean", "gaussian"]),
                ParamSpec("type", "enum", "binary", options=["binary", "binary_inv"]),
                ParamSpec("block_size", "int", 11, min_value=3, max_value=51, step=2),
                ParamSpec("c", "int", 2, min_value=-25, max_value=25, step=1),
                ParamSpec("pre_blur", "int", 1, min_value=1, max_value=31, step=2),
            ],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        gray = ensure_gray(inputs.get("image"))
        method_name = str(params.get("method", "gaussian"))
        type_name = str(params.get("type", "binary"))
        block_size = odd_ksize(params.get("block_size", 11), 3)
        c = int(params.get("c", 2))
        pre_blur = odd_ksize(params.get("pre_blur", 1), 1)

        if pre_blur > 1:
            gray = cv2.GaussianBlur(gray, (pre_blur, pre_blur), 0)

        method = cv2.ADAPTIVE_THRESH_MEAN_C if method_name == "mean" else cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        thresh_type = cv2.THRESH_BINARY if type_name == "binary" else cv2.THRESH_BINARY_INV

        mask = cv2.adaptiveThreshold(gray, 255, method, thresh_type, block_size, c)
        return {"mask": mask, "image": cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)}


class BinaryMorphologyBlock(BlockBase):
    SHAPE_MAP = {
        "rect": cv2.MORPH_RECT,
        "ellipse": cv2.MORPH_ELLIPSE,
        "cross": cv2.MORPH_CROSS,
    }
    BORDER_MAP = {
        "default": cv2.BORDER_DEFAULT,
        "constant": cv2.BORDER_CONSTANT,
        "reflect": cv2.BORDER_REFLECT,
        "replicate": cv2.BORDER_REPLICATE,
        "reflect101": cv2.BORDER_REFLECT_101,
    }
    OP_MAP = {
        "dilate": cv2.MORPH_DILATE,
        "erode": cv2.MORPH_ERODE,
        "open": cv2.MORPH_OPEN,
        "close": cv2.MORPH_CLOSE,
        "gradient": cv2.MORPH_GRADIENT,
        "tophat": cv2.MORPH_TOPHAT,
        "blackhat": cv2.MORPH_BLACKHAT,
    }

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="BinaryMorphology",
            title="Binary Morphology",
            category="Image Processing",
            input_ports=[PortSpec("mask", "mask")],
            output_ports=[PortSpec("mask", "mask"), PortSpec("image", "image"), PortSpec("meta", "meta")],
            params=[
                ParamSpec("operation", "enum", "dilate", options=list(cls.OP_MAP.keys())),
                ParamSpec("kernel_shape", "enum", "rect", options=list(cls.SHAPE_MAP.keys())),
                ParamSpec("kernel_w", "int", 3, min_value=1, max_value=101, step=1),
                ParamSpec("kernel_h", "int", 3, min_value=1, max_value=101, step=1),
                ParamSpec("iterations", "int", 1, min_value=1, max_value=50, step=1),
                ParamSpec("anchor_x", "int", -1, min_value=-1, max_value=100, step=1),
                ParamSpec("anchor_y", "int", -1, min_value=-1, max_value=100, step=1),
                ParamSpec("border_type", "enum", "constant", options=list(cls.BORDER_MAP.keys())),
                ParamSpec("border_value", "int", 0, min_value=0, max_value=255, step=1, visible_if={"border_type": ["constant"]}),
                ParamSpec("ensure_binary", "bool", True),
                ParamSpec("binary_thresh", "int", 127, min_value=0, max_value=255, step=1, visible_if={"ensure_binary": [True]}),
                ParamSpec("invert_before", "bool", False),
            ],
            description="OpenCV morphology for binary-mask post-processing: dilation, erosion, opening, closing, and more.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        mask_in = inputs.get("mask")
        if mask_in is None:
            raise ValueError("BinaryMorphology expects mask")
        mask = ensure_gray(mask_in)

        ensure_binary = bool(params.get("ensure_binary", True))
        if ensure_binary:
            thresh = int(params.get("binary_thresh", 127))
            _, mask = cv2.threshold(mask, thresh, 255, cv2.THRESH_BINARY)

        if bool(params.get("invert_before", False)):
            mask = cv2.bitwise_not(mask)

        op_name = str(params.get("operation", "dilate"))
        op = self.OP_MAP.get(op_name, cv2.MORPH_DILATE)
        shape = self.SHAPE_MAP.get(str(params.get("kernel_shape", "rect")), cv2.MORPH_RECT)
        kw = max(1, int(params.get("kernel_w", 3)))
        kh = max(1, int(params.get("kernel_h", 3)))
        kernel = cv2.getStructuringElement(shape, (kw, kh))

        iterations = max(1, int(params.get("iterations", 1)))
        anchor_x = int(params.get("anchor_x", -1))
        anchor_y = int(params.get("anchor_y", -1))
        if anchor_x >= kw or anchor_x < -1:
            anchor_x = -1
        if anchor_y >= kh or anchor_y < -1:
            anchor_y = -1
        anchor = (anchor_x, anchor_y)

        border_type_name = str(params.get("border_type", "constant"))
        border_type = self.BORDER_MAP.get(border_type_name, cv2.BORDER_CONSTANT)
        border_value = int(params.get("border_value", 0))

        out_mask = cv2.morphologyEx(
            mask,
            op,
            kernel,
            anchor=anchor,
            iterations=iterations,
            borderType=border_type,
            borderValue=border_value,
        )

        meta = {
            "operation": op_name,
            "kernel_shape": str(params.get("kernel_shape", "rect")),
            "kernel_size": {"w": kw, "h": kh},
            "iterations": iterations,
            "anchor": {"x": anchor_x, "y": anchor_y},
        }
        return {"mask": out_mask, "image": cv2.cvtColor(out_mask, cv2.COLOR_GRAY2BGR), "meta": meta}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        op_name = str(params.get("operation", "dilate"))
        op_const = {
            "dilate": "cv2.MORPH_DILATE",
            "erode": "cv2.MORPH_ERODE",
            "open": "cv2.MORPH_OPEN",
            "close": "cv2.MORPH_CLOSE",
            "gradient": "cv2.MORPH_GRADIENT",
            "tophat": "cv2.MORPH_TOPHAT",
            "blackhat": "cv2.MORPH_BLACKHAT",
        }.get(op_name, "cv2.MORPH_DILATE")
        shape_const = {
            "rect": "cv2.MORPH_RECT",
            "ellipse": "cv2.MORPH_ELLIPSE",
            "cross": "cv2.MORPH_CROSS",
        }.get(str(params.get("kernel_shape", "rect")), "cv2.MORPH_RECT")
        return (
            "# Binary Morphology\n"
            "mask = input_mask.copy()\n"
            f"if {bool(params.get('ensure_binary', True))}:\n"
            f"    _, mask = cv2.threshold(mask, {int(params.get('binary_thresh', 127))}, 255, cv2.THRESH_BINARY)\n"
            f"if {bool(params.get('invert_before', False))}:\n"
            "    mask = cv2.bitwise_not(mask)\n"
            f"kernel = cv2.getStructuringElement({shape_const}, ({max(1, int(params.get('kernel_w', 3)))}, {max(1, int(params.get('kernel_h', 3)))}))\n"
            f"out_mask = cv2.morphologyEx(mask, {op_const}, kernel, iterations={max(1, int(params.get('iterations', 1)))})"
        )


class ContoursAnalysisBlock(BlockBase):
    RETR_MAP = {
        "external": cv2.RETR_EXTERNAL,
        "list": cv2.RETR_LIST,
        "ccomp": cv2.RETR_CCOMP,
        "tree": cv2.RETR_TREE,
        "floodfill": cv2.RETR_FLOODFILL,
    }
    CHAIN_MAP = {
        "none": cv2.CHAIN_APPROX_NONE,
        "simple": cv2.CHAIN_APPROX_SIMPLE,
        "tc89_l1": cv2.CHAIN_APPROX_TC89_L1,
        "tc89_kcos": cv2.CHAIN_APPROX_TC89_KCOS,
    }

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="ContoursAnalysis",
            title="Contours Analysis",
            category="Image Processing",
            input_ports=[PortSpec("mask", "mask")],
            output_ports=[PortSpec("image", "image"), PortSpec("mask", "mask"), PortSpec("detections", "detections"), PortSpec("meta", "meta")],
            params=[
                ParamSpec("ensure_binary", "bool", True),
                ParamSpec("binary_thresh", "int", 127, min_value=0, max_value=255, step=1, visible_if={"ensure_binary": [True]}),
                ParamSpec("invert", "bool", False),
                ParamSpec("retrieval", "enum", "tree", options=["external", "list", "ccomp", "tree", "floodfill"]),
                ParamSpec("approx_mode", "enum", "simple", options=["none", "simple", "tc89_l1", "tc89_kcos"]),
                ParamSpec("offset_x", "int", 0, min_value=-5000, max_value=5000, step=1),
                ParamSpec("offset_y", "int", 0, min_value=-5000, max_value=5000, step=1),
                ParamSpec("draw_mode", "enum", "both", options=["contours", "boxes", "both"]),
                ParamSpec("draw_thickness", "int", 2, min_value=1, max_value=20, step=1),
                ParamSpec("filter_by_area", "bool", True),
                ParamSpec("area_min", "int", 200, min_value=0, max_value=500000, step=10, visible_if={"filter_by_area": [True]}),
                ParamSpec("area_max", "int", 1000000, min_value=1, max_value=5000000, step=10, visible_if={"filter_by_area": [True]}),
                ParamSpec("filter_by_aspect_ratio", "bool", False),
                ParamSpec(
                    "aspect_ratio_min",
                    "float",
                    0.1,
                    min_value=0.01,
                    max_value=100.0,
                    step=0.05,
                    visible_if={"filter_by_aspect_ratio": [True]},
                ),
                ParamSpec(
                    "aspect_ratio_max",
                    "float",
                    10.0,
                    min_value=0.01,
                    max_value=100.0,
                    step=0.05,
                    visible_if={"filter_by_aspect_ratio": [True]},
                ),
            ],
            description="Contour extraction from binary masks with full OpenCV retrieval/approx controls and geometric filtering.",
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        mask_input = inputs.get("mask")
        if mask_input is None:
            raise ValueError("ContoursAnalysis expects mask")
        mask = ensure_gray(mask_input)
        if bool(params.get("ensure_binary", True)):
            thresh = int(params.get("binary_thresh", 127))
            _, mask = cv2.threshold(mask, thresh, 255, cv2.THRESH_BINARY)
        if bool(params.get("invert", False)):
            mask = cv2.bitwise_not(mask)

        retrieval_name = str(params.get("retrieval", "tree"))
        approx_name = str(params.get("approx_mode", "simple"))
        retrieval = self.RETR_MAP.get(retrieval_name, cv2.RETR_TREE)
        approx_mode = self.CHAIN_MAP.get(approx_name, cv2.CHAIN_APPROX_SIMPLE)
        offset = (int(params.get("offset_x", 0)), int(params.get("offset_y", 0)))
        find_mask = mask.astype(np.int32) if retrieval == cv2.RETR_FLOODFILL else mask.copy()

        # OpenCV can return either 2 or 3 values depending on version.
        found = cv2.findContours(find_mask, retrieval, approx_mode, offset=offset)
        if len(found) == 3:
            _, contours, hierarchy = found
        else:
            contours, hierarchy = found

        filter_by_area = bool(params.get("filter_by_area", True))
        area_min = int(params.get("area_min", 200))
        area_max = max(area_min, int(params.get("area_max", 1000000)))
        filter_by_aspect = bool(params.get("filter_by_aspect_ratio", False))
        aspect_min = float(params.get("aspect_ratio_min", 0.1))
        aspect_max = max(aspect_min, float(params.get("aspect_ratio_max", 10.0)))
        draw_mode = str(params.get("draw_mode", "both"))
        thickness = max(1, int(params.get("draw_thickness", 2)))

        out = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        detections: list[Detection] = []
        kept = 0
        total_area = 0.0
        rejected_area = 0
        rejected_aspect = 0

        for cnt in contours:
            area = float(cv2.contourArea(cnt))
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / float(h) if h > 0 else 9999.0
            perimeter = float(cv2.arcLength(cnt, True))

            if filter_by_area and (area < area_min or area > area_max):
                rejected_area += 1
                continue
            if filter_by_aspect and (aspect_ratio < aspect_min or aspect_ratio > aspect_max):
                rejected_aspect += 1
                continue

            kept += 1
            total_area += area
            detections.append(
                Detection(
                    bbox=(x, y, w, h),
                    label="contour",
                    score=1.0,
                    extra={"area": area, "aspect_ratio": aspect_ratio, "perimeter": perimeter},
                )
            )
            if draw_mode in ("contours", "both"):
                cv2.drawContours(out, [cnt], -1, (0, 255, 0), thickness)
            if draw_mode in ("boxes", "both"):
                cv2.rectangle(out, (x, y), (x + w, y + h), (0, 165, 255), thickness)

        meta = {
            "total_contours": len(contours),
            "kept_contours": kept,
            "rejected_by_area": rejected_area,
            "rejected_by_aspect_ratio": rejected_aspect,
            "total_kept_area": total_area,
            "has_hierarchy": hierarchy is not None,
            "retrieval": retrieval_name,
            "approx_mode": approx_name,
            "offset": {"x": offset[0], "y": offset[1]},
        }
        return {"image": out, "mask": mask, "detections": detections, "meta": meta}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        retrieval_name = str(params.get("retrieval", "tree"))
        approx_name = str(params.get("approx_mode", "simple"))
        retrieval_const = {
            "external": "cv2.RETR_EXTERNAL",
            "list": "cv2.RETR_LIST",
            "ccomp": "cv2.RETR_CCOMP",
            "tree": "cv2.RETR_TREE",
            "floodfill": "cv2.RETR_FLOODFILL",
        }.get(retrieval_name, "cv2.RETR_TREE")
        approx_const = {
            "none": "cv2.CHAIN_APPROX_NONE",
            "simple": "cv2.CHAIN_APPROX_SIMPLE",
            "tc89_l1": "cv2.CHAIN_APPROX_TC89_L1",
            "tc89_kcos": "cv2.CHAIN_APPROX_TC89_KCOS",
        }.get(approx_name, "cv2.CHAIN_APPROX_SIMPLE")
        return (
            "# Contours Analysis\n"
            "mask = input_mask.copy()\n"
            f"if {bool(params.get('ensure_binary', True))}:\n"
            f"    _, mask = cv2.threshold(mask, {int(params.get('binary_thresh', 127))}, 255, cv2.THRESH_BINARY)\n"
            f"if {bool(params.get('invert', False))}:\n"
            "    mask = cv2.bitwise_not(mask)\n"
            f"cnts, hierarchy = cv2.findContours(mask.copy(), {retrieval_const}, {approx_const}, "
            f"offset=({int(params.get('offset_x', 0))}, {int(params.get('offset_y', 0))}))\n"
            f"filter_by_area = {bool(params.get('filter_by_area', True))}\n"
            f"area_min, area_max = ({int(params.get('area_min', 200))}, {int(params.get('area_max', 1000000))})\n"
            f"filter_by_aspect = {bool(params.get('filter_by_aspect_ratio', False))}\n"
            f"aspect_min, aspect_max = ({float(params.get('aspect_ratio_min', 0.1))}, {float(params.get('aspect_ratio_max', 10.0))})\n"
            "kept = []\n"
            "for c in cnts:\n"
            "    area = cv2.contourArea(c)\n"
            "    x, y, w, h = cv2.boundingRect(c)\n"
            "    ar = w / max(h, 1)\n"
            "    if filter_by_area and not (area_min <= area <= area_max):\n"
            "        continue\n"
            "    if filter_by_aspect and not (aspect_min <= ar <= aspect_max):\n"
            "        continue\n"
            "    kept.append(c)\n"
            "vis = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)\n"
            "cv2.drawContours(vis, kept, -1, (0, 255, 0), 2)"
        )


class HoughCirclesBlock(BlockBase):
    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name="HoughCircles",
            title="Hough Circles",
            category="Image Processing",
            input_ports=[PortSpec("image", "image")],
            output_ports=[PortSpec("image", "image"), PortSpec("detections", "detections"), PortSpec("meta", "meta")],
            params=[
                ParamSpec("dp", "float", 1.2, min_value=1.0, max_value=5.0, step=0.1),
                ParamSpec("min_dist", "int", 70, min_value=1, max_value=500, step=1),
                ParamSpec("param1", "int", 120, min_value=1, max_value=500, step=1),
                ParamSpec("param2", "int", 35, min_value=1, max_value=300, step=1),
                ParamSpec("min_radius", "int", 10, min_value=0, max_value=500, step=1),
                ParamSpec("max_radius", "int", 120, min_value=1, max_value=800, step=1),
                ParamSpec("blur_k", "int", 5, min_value=1, max_value=31, step=2),
            ],
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        image = ensure_bgr(inputs.get("image"))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur_k = odd_ksize(params.get("blur_k", 5), 1)
        if blur_k > 1:
            gray = cv2.medianBlur(gray, blur_k)

        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=max(1.0, float(params.get("dp", 1.2))),
            minDist=max(1, int(params.get("min_dist", 70))),
            param1=max(1, int(params.get("param1", 120))),
            param2=max(1, int(params.get("param2", 35))),
            minRadius=max(0, int(params.get("min_radius", 10))),
            maxRadius=max(1, int(params.get("max_radius", 120))),
        )

        out = image.copy()
        detections: list[Detection] = []
        if circles is not None:
            circles = np.uint16(np.around(circles[0]))
            for c in circles:
                x, y, r = int(c[0]), int(c[1]), int(c[2])
                cv2.circle(out, (x, y), r, (0, 255, 0), 2)
                cv2.circle(out, (x, y), 2, (0, 0, 255), 3)
                detections.append(Detection(bbox=(x - r, y - r, 2 * r, 2 * r), label="circle", score=1.0, extra={"radius": r}))

        return {"image": out, "detections": detections, "meta": {"circle_count": len(detections)}}
