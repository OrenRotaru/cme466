#!/usr/bin/env python3
"""
Universal OpenCV GUI Lab for CME 466.

Features:
- Dynamic technique selector with live slider controls
- Fast image loading and output saving
- Techniques:
  - Preprocess pipeline (for classification workflow experiments)
  - De-noising/blurring (box, Gaussian, median, bilateral)
  - Image sharpening (Laplacian and gradient magnitude)
  - Canny edge detection
  - Simple thresholding
  - Adaptive thresholding
  - Contours + contour analysis
  - Hough circle detection
  - Haar cascade multi-detect (frontal/profile/eyes/smile)
  - HOG descriptor playground (64x128, 3780-dim)
  - HOG + SVM people detection
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Tuple

import cv2
import numpy as np


OUTPUT_WINDOW = "Universal CV Lab - Output"
CONTROLS_WINDOW = "Universal CV Lab - Controls"


@dataclass(frozen=True)
class TrackbarSpec:
    name: str
    max_value: int
    default: int


def _noop(_: int) -> None:
    return


def odd_from_slider(pos: int, min_odd: int = 1) -> int:
    value = min_odd + 2 * max(0, int(pos))
    if value % 2 == 0:
        value += 1
    return value


def ensure_bgr(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img


def gamma_correct(img: np.ndarray, gamma: float) -> np.ndarray:
    gamma = max(0.01, float(gamma))
    lut = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)
    return cv2.LUT(img, lut)


class UniversalCVLab:
    def __init__(self, image_path: str | None) -> None:
        self.mode_names: List[str] = [
            "Preprocess Pipeline",
            "Blur / Denoise",
            "Sharpen (Laplacian/Gradient)",
            "Canny Edge",
            "Simple Threshold",
            "Adaptive Threshold",
            "Contours Analysis",
            "Hough Circles",
            "Haar Multi-Detect",
            "HOG Descriptor (64x128)",
            "HOG + SVM Detector",
        ]
        self.mode_specs: Dict[str, List[TrackbarSpec]] = {
            "Preprocess Pipeline": [
                TrackbarSpec("Alpha x100", 300, 100),
                TrackbarSpec("Beta(+/-100)", 200, 100),
                TrackbarSpec("Gamma x100", 300, 100),
                TrackbarSpec("Gray", 1, 0),
                TrackbarSpec("EqHist", 1, 0),
                TrackbarSpec("BlurK", 15, 0),
            ],
            "Blur / Denoise": [
                TrackbarSpec("Method", 3, 0),  # 0 box, 1 gauss, 2 median, 3 bilateral
                TrackbarSpec("Kernel", 15, 2),
                TrackbarSpec("SigmaX", 200, 20),
                TrackbarSpec("SigmaColor", 300, 80),
                TrackbarSpec("SigmaSpace", 300, 80),
            ],
            "Sharpen (Laplacian/Gradient)": [
                TrackbarSpec("Method", 1, 0),  # 0 laplacian, 1 gradient
                TrackbarSpec("KernelIdx", 3, 1),  # maps to [1,3,5,7]
                TrackbarSpec("Alpha x100", 300, 100),
                TrackbarSpec("Blend x100", 100, 40),
            ],
            "Canny Edge": [
                TrackbarSpec("Low", 500, 100),
                TrackbarSpec("High", 500, 200),
                TrackbarSpec("ApertureIdx", 2, 0),  # maps to [3,5,7]
                TrackbarSpec("L2Grad", 1, 0),
                TrackbarSpec("Dilate", 5, 0),
                TrackbarSpec("Erode", 5, 0),
            ],
            "Simple Threshold": [
                TrackbarSpec("Thresh", 255, 127),
                TrackbarSpec("MaxVal", 255, 255),
                TrackbarSpec("Type", 4, 0),
                TrackbarSpec("PreBlur", 15, 0),
                TrackbarSpec("Otsu", 1, 0),
            ],
            "Adaptive Threshold": [
                TrackbarSpec("Method", 1, 1),  # 0 mean, 1 gaussian
                TrackbarSpec("Type", 1, 0),  # 0 binary, 1 inv
                TrackbarSpec("Block", 25, 5),
                TrackbarSpec("C(+/-25)", 50, 27),
                TrackbarSpec("PreBlur", 15, 0),
            ],
            "Contours Analysis": [
                TrackbarSpec("Source", 2, 0),  # 0 thresh, 1 canny, 2 adaptive
                TrackbarSpec("Thresh", 255, 127),
                TrackbarSpec("CannyLow", 500, 100),
                TrackbarSpec("CannyHigh", 500, 200),
                TrackbarSpec("Invert", 1, 1),
                TrackbarSpec("Retrieval", 2, 1),  # external/tree/list
                TrackbarSpec("DrawMode", 2, 2),  # contours/boxes/both
                TrackbarSpec("AreaMin x10", 2000, 20),
                TrackbarSpec("AreaMax x10", 2000, 2000),
            ],
            "Hough Circles": [
                TrackbarSpec("dp x10", 40, 12),
                TrackbarSpec("MinDist", 500, 70),
                TrackbarSpec("Param1", 500, 120),
                TrackbarSpec("Param2", 300, 35),
                TrackbarSpec("MinR", 400, 10),
                TrackbarSpec("MaxR", 500, 120),
                TrackbarSpec("BlurK", 15, 3),
            ],
            "Haar Multi-Detect": [
                TrackbarSpec("Frontal", 1, 1),
                TrackbarSpec("Profile", 1, 0),
                TrackbarSpec("Eyes", 1, 1),
                TrackbarSpec("Smile", 1, 0),
                TrackbarSpec("Scale x100", 200, 110),
                TrackbarSpec("MinNbrs", 20, 5),
                TrackbarSpec("MinSize", 400, 30),
                TrackbarSpec("EqHist", 1, 1),
            ],
            "HOG Descriptor (64x128)": [
                TrackbarSpec("ROI Scale %", 100, 60),
                TrackbarSpec("Center X %", 100, 50),
                TrackbarSpec("Center Y %", 100, 50),
                TrackbarSpec("ShowGrad", 1, 1),
            ],
            "HOG + SVM Detector": [
                TrackbarSpec("HitThr (+/-2.0)", 40, 20),
                TrackbarSpec("StrideIdx", 4, 1),  # 4,8,12,16,20
                TrackbarSpec("PaddingIdx", 4, 1),
                TrackbarSpec("Scale x100", 150, 105),
                TrackbarSpec("FinalThr", 10, 2),
                TrackbarSpec("WThr x100", 400, 50),
            ],
        }
        self.global_specs: List[TrackbarSpec] = [
            TrackbarSpec("Technique", len(self.mode_names) - 1, 0),
            TrackbarSpec("Display %", 200, 100),
        ]

        self.mode_index = 0
        self.mode_cache: Dict[str, Dict[str, int]] = {name: {} for name in self.mode_names}
        self.last_output: np.ndarray | None = None
        self.last_lines: List[str] = []
        self.current_image_path: str = ""

        self.hog_descriptor = cv2.HOGDescriptor()
        self.hog_detector = cv2.HOGDescriptor()
        self.hog_detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        self.cascades = self._load_cascades()

        img = self._load_initial_image(image_path)
        self.image = img

        cv2.namedWindow(OUTPUT_WINDOW, cv2.WINDOW_NORMAL)
        self._build_controls()
        self._print_help()

    def _load_cascades(self) -> Dict[str, cv2.CascadeClassifier]:
        cascade_files = {
            "frontal": "haarcascade_frontalface_default.xml",
            "profile": "haarcascade_profileface.xml",
            "eye": "haarcascade_eye.xml",
            "smile": "haarcascade_smile.xml",
        }
        cascades: Dict[str, cv2.CascadeClassifier] = {}
        for key, filename in cascade_files.items():
            path = Path(cv2.data.haarcascades) / filename
            cascade = cv2.CascadeClassifier(str(path))
            if not cascade.empty():
                cascades[key] = cascade
        return cascades

    def _load_initial_image(self, image_path: str | None) -> np.ndarray:
        candidates: List[Path] = []
        if image_path:
            candidates.append(Path(image_path))

        repo_root = self._find_repo_root(Path(__file__).resolve())
        if repo_root is not None:
            img_dir = repo_root / "class_example_code" / "imgs"
            candidates.extend(
                [
                    img_dir / "jackie.jpg",
                    img_dir / "people3.jpg",
                    img_dir / "people.jpg",
                    img_dir / "coins.jpg",
                ]
            )

        for candidate in candidates:
            img = cv2.imread(str(candidate))
            if img is not None:
                self.current_image_path = str(candidate)
                return img

        raise FileNotFoundError(
            "No valid image found. Pass one with --image /path/to/file.jpg."
        )

    @staticmethod
    def _find_repo_root(start: Path) -> Path | None:
        for candidate in [start, *start.parents]:
            if (candidate / "class_example_code").exists():
                return candidate
        return None

    def _build_controls(self) -> None:
        try:
            cv2.destroyWindow(CONTROLS_WINDOW)
        except cv2.error:
            pass
        cv2.namedWindow(CONTROLS_WINDOW, cv2.WINDOW_NORMAL)

        for spec in self.global_specs:
            default_value = spec.default
            if spec.name == "Technique":
                default_value = self.mode_index
            cv2.createTrackbar(
                spec.name, CONTROLS_WINDOW, default_value, spec.max_value, _noop
            )

        current_mode = self.mode_names[self.mode_index]
        current_values = self.mode_cache.get(current_mode, {})
        for spec in self.mode_specs[current_mode]:
            value = current_values.get(spec.name, spec.default)
            cv2.createTrackbar(spec.name, CONTROLS_WINDOW, value, spec.max_value, _noop)

        self._show_mode_shortcuts()

    def _read_values(self) -> Dict[str, int]:
        current_mode = self.mode_names[self.mode_index]
        values: Dict[str, int] = {}
        for spec in self.global_specs:
            values[spec.name] = cv2.getTrackbarPos(spec.name, CONTROLS_WINDOW)
        for spec in self.mode_specs[current_mode]:
            values[spec.name] = cv2.getTrackbarPos(spec.name, CONTROLS_WINDOW)
        return values

    def _cache_mode_values(self, values: Dict[str, int]) -> None:
        mode_name = self.mode_names[self.mode_index]
        cache = self.mode_cache.setdefault(mode_name, {})
        for spec in self.mode_specs[mode_name]:
            cache[spec.name] = values.get(spec.name, spec.default)

    def _set_mode(self, new_index: int) -> None:
        self.mode_index = new_index % len(self.mode_names)
        self._build_controls()

    def _open_image_macos_osascript(self) -> str:
        script = [
            "-e",
            'set selectedFile to choose file with prompt "Choose an image file"',
            "-e",
            "POSIX path of selectedFile",
        ]
        try:
            result = subprocess.run(
                ["osascript", *script],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return ""
        if result.returncode != 0:
            return ""
        return result.stdout.strip()

    def _open_image_dialog(self) -> None:
        selected_path = ""
        if sys.platform == "darwin":
            selected_path = self._open_image_macos_osascript()

        if not selected_path:
            print("[info] Enter image path (or empty to cancel):")
            try:
                selected_path = input("> ").strip()
            except EOFError:
                selected_path = ""

        if not selected_path:
            return
        selected_path = selected_path.strip().strip('"').strip("'")
        selected_path = str(Path(selected_path).expanduser())
        img = cv2.imread(selected_path)
        if img is None:
            print(f"[warn] Could not load image: {selected_path}")
            return
        self.image = img
        self.current_image_path = selected_path
        print(f"[info] Loaded image: {selected_path}")

    def _save_output(self) -> None:
        if self.last_output is None:
            print("[warn] Nothing to save yet.")
            return
        repo_root = self._find_repo_root(Path.cwd())
        if repo_root is None:
            repo_root = Path.cwd()
        out_dir = repo_root / "tmp" / "cv_gui_outputs"
        out_dir.mkdir(parents=True, exist_ok=True)
        mode_slug = self.mode_names[self.mode_index].lower().replace(" ", "_").replace("/", "_")
        out_path = out_dir / f"{mode_slug}.png"
        cv2.imwrite(str(out_path), self.last_output)
        print(f"[info] Saved output: {out_path}")

    def _resize_for_display(self, img: np.ndarray, display_pct: int) -> np.ndarray:
        display_pct = max(10, display_pct)
        scale = display_pct / 100.0
        if abs(scale - 1.0) < 1e-6:
            return img
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        return cv2.resize(img, None, fx=scale, fy=scale, interpolation=interpolation)

    def _draw_overlay(self, img: np.ndarray, mode: str, lines: List[str]) -> np.ndarray:
        out = ensure_bgr(img).copy()
        overlay_lines = [f"Mode: {mode}"] + lines
        top_h = 24 + 18 * len(overlay_lines)
        cv2.rectangle(out, (0, 0), (out.shape[1], top_h), (0, 0, 0), -1)
        for i, line in enumerate(overlay_lines):
            y = 20 + i * 18
            cv2.putText(
                out,
                line[:120],
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )
        return out

    def _apply_mode(self, mode: str, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        if mode == "Preprocess Pipeline":
            return self._apply_preprocess(values)
        if mode == "Blur / Denoise":
            return self._apply_blur(values)
        if mode == "Sharpen (Laplacian/Gradient)":
            return self._apply_sharpen(values)
        if mode == "Canny Edge":
            return self._apply_canny(values)
        if mode == "Simple Threshold":
            return self._apply_simple_threshold(values)
        if mode == "Adaptive Threshold":
            return self._apply_adaptive_threshold(values)
        if mode == "Contours Analysis":
            return self._apply_contours(values)
        if mode == "Hough Circles":
            return self._apply_hough_circles(values)
        if mode == "Haar Multi-Detect":
            return self._apply_haar_multi(values)
        if mode == "HOG Descriptor (64x128)":
            return self._apply_hog_descriptor(values)
        if mode == "HOG + SVM Detector":
            return self._apply_hog_detector(values)
        return self.image.copy(), []

    def _apply_preprocess(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        alpha = values["Alpha x100"] / 100.0
        beta = values["Beta(+/-100)"] - 100
        gamma = max(0.01, values["Gamma x100"] / 100.0)
        use_gray = values["Gray"] == 1
        eq_hist = values["EqHist"] == 1
        blur_k = odd_from_slider(values["BlurK"], 1)

        out = cv2.convertScaleAbs(self.image, alpha=alpha, beta=beta)
        out = gamma_correct(out, gamma)

        if blur_k > 1:
            out = cv2.GaussianBlur(out, (blur_k, blur_k), 0)

        if use_gray:
            gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
            if eq_hist:
                gray = cv2.equalizeHist(gray)
            out = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif eq_hist:
            ycrcb = cv2.cvtColor(out, cv2.COLOR_BGR2YCrCb)
            ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
            out = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

        lines = [
            f"alpha={alpha:.2f}, beta={beta}, gamma={gamma:.2f}",
            f"gray={int(use_gray)}, eq_hist={int(eq_hist)}, blur_k={blur_k}",
            "Pipeline intuition: preprocess -> feature extraction -> classifier",
        ]
        return out, lines

    def _apply_blur(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        method = values["Method"]
        k = odd_from_slider(values["Kernel"], 1)
        sigma_x = max(0.0, float(values["SigmaX"]))
        sigma_color = max(1.0, float(values["SigmaColor"]))
        sigma_space = max(1.0, float(values["SigmaSpace"]))

        if method == 0:
            out = cv2.blur(self.image, (k, k))
            method_name = "box"
        elif method == 1:
            out = cv2.GaussianBlur(self.image, (k, k), sigmaX=sigma_x)
            method_name = "gaussian"
        elif method == 2:
            mk = max(3, k)
            out = cv2.medianBlur(self.image, mk)
            method_name = "median"
            k = mk
        else:
            d = max(1, k)
            out = cv2.bilateralFilter(self.image, d, sigma_color, sigma_space)
            method_name = "bilateral"

        lines = [
            f"method={method_name}, kernel={k}",
            f"sigmaX={sigma_x:.1f}, sigmaColor={sigma_color:.1f}, sigmaSpace={sigma_space:.1f}",
        ]
        return out, lines

    def _apply_sharpen(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        method = values["Method"]
        kernel_map = [1, 3, 5, 7]
        ksize = kernel_map[min(values["KernelIdx"], len(kernel_map) - 1)]
        alpha = values["Alpha x100"] / 100.0
        blend = values["Blend x100"] / 100.0

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        if method == 0:
            lap = cv2.Laplacian(gray, cv2.CV_32F, ksize=ksize)
            sharp = cv2.convertScaleAbs(gray - alpha * lap)
            out = cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)
            method_name = "laplacian"
            lines = [
                f"method={method_name}, ksize={ksize}, alpha={alpha:.2f}",
                "Exam: Laplacian is strong for fine detail enhancement.",
            ]
            return out, lines

        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=ksize)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=ksize)
        mag = cv2.magnitude(gx, gy)
        mag_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        grad_vis = cv2.applyColorMap(mag_u8, cv2.COLORMAP_TURBO)
        out = cv2.addWeighted(self.image, 1.0 - blend, grad_vis, blend, 0)
        lines = [
            f"method=gradient, ksize={ksize}, blend={blend:.2f}",
            "Exam: Gradient emphasizes prominent edges.",
        ]
        return out, lines

    def _apply_canny(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        low = values["Low"]
        high = max(low + 1, values["High"])
        aperture = [3, 5, 7][min(values["ApertureIdx"], 2)]
        l2_grad = values["L2Grad"] == 1
        dilate_iter = values["Dilate"]
        erode_iter = values["Erode"]

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, low, high, apertureSize=aperture, L2gradient=l2_grad)
        if dilate_iter > 0:
            edges = cv2.dilate(edges, np.ones((3, 3), dtype=np.uint8), iterations=dilate_iter)
        if erode_iter > 0:
            edges = cv2.erode(edges, np.ones((3, 3), dtype=np.uint8), iterations=erode_iter)

        lines = [
            f"low={low}, high={high}, aperture={aperture}, L2={int(l2_grad)}",
            f"dilate={dilate_iter}, erode={erode_iter}",
        ]
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR), lines

    def _apply_simple_threshold(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        thresh = values["Thresh"]
        max_val = values["MaxVal"]
        mode_map = [
            cv2.THRESH_BINARY,
            cv2.THRESH_BINARY_INV,
            cv2.THRESH_TRUNC,
            cv2.THRESH_TOZERO,
            cv2.THRESH_TOZERO_INV,
        ]
        mode_name_map = ["BINARY", "BINARY_INV", "TRUNC", "TOZERO", "TOZERO_INV"]
        mode_idx = min(values["Type"], len(mode_map) - 1)
        mode = mode_map[mode_idx]
        mode_name = mode_name_map[mode_idx]
        pre_blur = odd_from_slider(values["PreBlur"], 1)
        use_otsu = values["Otsu"] == 1

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        if pre_blur > 1:
            gray = cv2.GaussianBlur(gray, (pre_blur, pre_blur), 0)
        if use_otsu:
            mode = mode | cv2.THRESH_OTSU
        ret, out = cv2.threshold(gray, thresh, max_val, mode)

        lines = [
            f"type={mode_name}, thresh={thresh}, maxVal={max_val}, otsu={int(use_otsu)}",
            f"pre_blur={pre_blur}, returned_thresh={ret:.2f}",
        ]
        return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR), lines

    def _apply_adaptive_threshold(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        method = (
            cv2.ADAPTIVE_THRESH_MEAN_C
            if values["Method"] == 0
            else cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        )
        method_name = "MEAN_C" if values["Method"] == 0 else "GAUSSIAN_C"
        thresh_type = cv2.THRESH_BINARY if values["Type"] == 0 else cv2.THRESH_BINARY_INV
        type_name = "BINARY" if values["Type"] == 0 else "BINARY_INV"
        block_size = odd_from_slider(values["Block"], 3)
        c_value = values["C(+/-25)"] - 25
        pre_blur = odd_from_slider(values["PreBlur"], 1)

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        if pre_blur > 1:
            gray = cv2.GaussianBlur(gray, (pre_blur, pre_blur), 0)
        out = cv2.adaptiveThreshold(
            gray, 255, method, thresh_type, block_size, c_value
        )

        lines = [
            f"method={method_name}, type={type_name}",
            f"block={block_size}, C={c_value}, pre_blur={pre_blur}",
        ]
        return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR), lines

    def _build_contour_binary(self, gray: np.ndarray, values: Dict[str, int]) -> np.ndarray:
        source = values["Source"]
        if source == 0:
            _, binary = cv2.threshold(gray, values["Thresh"], 255, cv2.THRESH_BINARY)
        elif source == 1:
            binary = cv2.Canny(gray, values["CannyLow"], max(values["CannyLow"] + 1, values["CannyHigh"]))
        else:
            binary = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2,
            )
        if values["Invert"] == 1:
            binary = cv2.bitwise_not(binary)
        return binary

    def _apply_contours(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        binary = self._build_contour_binary(gray, values)

        retrieval_map = [cv2.RETR_EXTERNAL, cv2.RETR_TREE, cv2.RETR_LIST]
        retrieval_name = ["EXTERNAL", "TREE", "LIST"][min(values["Retrieval"], 2)]
        retrieval = retrieval_map[min(values["Retrieval"], 2)]

        contours, hierarchy = cv2.findContours(binary, retrieval, cv2.CHAIN_APPROX_SIMPLE)
        draw_mode = values["DrawMode"]  # 0 contours, 1 boxes, 2 both
        area_min = values["AreaMin x10"] * 10
        area_max = max(area_min, values["AreaMax x10"] * 10)

        out = self.image.copy()
        kept = 0
        total_area = 0.0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < area_min or area > area_max:
                continue
            kept += 1
            total_area += area
            if draw_mode in (0, 2):
                cv2.drawContours(out, [cnt], -1, (0, 255, 0), 2)
            if draw_mode in (1, 2):
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(out, (x, y), (x + w, y + h), (0, 165, 255), 2)

        source_name = ["threshold", "canny", "adaptive"][min(values["Source"], 2)]
        lines = [
            f"source={source_name}, retrieval={retrieval_name}, invert={values['Invert']}",
            f"kept={kept}/{len(contours)}, area_min={area_min}, area_max={area_max}",
            f"total_kept_area={total_area:.1f}, hierarchy={'yes' if hierarchy is not None else 'no'}",
        ]
        return out, lines

    def _apply_hough_circles(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        dp = max(1.0, values["dp x10"] / 10.0)
        min_dist = max(1, values["MinDist"])
        param1 = max(1, values["Param1"])
        param2 = max(1, values["Param2"])
        min_r = values["MinR"]
        max_r = max(min_r + 1, values["MaxR"])
        blur_k = odd_from_slider(values["BlurK"], 1)

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        if blur_k > 1:
            gray = cv2.medianBlur(gray, blur_k)

        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=dp,
            minDist=min_dist,
            param1=param1,
            param2=param2,
            minRadius=min_r,
            maxRadius=max_r,
        )

        out = self.image.copy()
        count = 0
        if circles is not None:
            circles = np.uint16(np.around(circles[0]))
            for c in circles:
                count += 1
                cv2.circle(out, (c[0], c[1]), c[2], (0, 255, 0), 2)
                cv2.circle(out, (c[0], c[1]), 2, (0, 0, 255), 3)

        lines = [
            f"count={count}, dp={dp:.2f}, minDist={min_dist}",
            f"param1={param1}, param2={param2}, minR={min_r}, maxR={max_r}, blur_k={blur_k}",
        ]
        return out, lines

    def _apply_haar_multi(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        if values["EqHist"] == 1:
            gray = cv2.equalizeHist(gray)

        scale_factor = max(1.01, values["Scale x100"] / 100.0)
        min_neighbors = max(1, values["MinNbrs"])
        min_size = max(10, values["MinSize"])
        min_size_tuple = (min_size, min_size)

        out = self.image.copy()
        face_count = 0
        profile_count = 0
        eye_count = 0
        smile_count = 0
        face_regions: List[Tuple[int, int, int, int]] = []

        if values["Frontal"] == 1 and "frontal" in self.cascades:
            faces = self.cascades["frontal"].detectMultiScale(
                gray,
                scaleFactor=scale_factor,
                minNeighbors=min_neighbors,
                minSize=min_size_tuple,
            )
            for (x, y, w, h) in faces:
                cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(out, "frontal", (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
                face_regions.append((x, y, w, h))
            face_count = len(faces)

        if values["Profile"] == 1 and "profile" in self.cascades:
            profiles = self.cascades["profile"].detectMultiScale(
                gray,
                scaleFactor=scale_factor,
                minNeighbors=min_neighbors,
                minSize=min_size_tuple,
            )
            for (x, y, w, h) in profiles:
                cv2.rectangle(out, (x, y), (x + w, y + h), (255, 180, 0), 2)
                cv2.putText(out, "profile", (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 180, 0), 1)
                face_regions.append((x, y, w, h))
            profile_count = len(profiles)

        if values["Eyes"] == 1 and "eye" in self.cascades:
            for (x, y, w, h) in face_regions:
                roi = gray[y : y + h, x : x + w]
                eyes = self.cascades["eye"].detectMultiScale(
                    roi,
                    scaleFactor=1.1,
                    minNeighbors=max(2, min_neighbors // 2),
                    minSize=(max(8, w // 10), max(8, h // 10)),
                )
                for (ex, ey, ew, eh) in eyes:
                    eye_count += 1
                    cv2.rectangle(out, (x + ex, y + ey), (x + ex + ew, y + ey + eh), (255, 0, 0), 1)

        if values["Smile"] == 1 and "smile" in self.cascades:
            for (x, y, w, h) in face_regions:
                roi = gray[y : y + h, x : x + w]
                smiles = self.cascades["smile"].detectMultiScale(
                    roi,
                    scaleFactor=1.7,
                    minNeighbors=max(3, min_neighbors),
                    minSize=(max(12, w // 6), max(12, h // 8)),
                )
                for (sx, sy, sw, sh) in smiles:
                    smile_count += 1
                    cv2.rectangle(out, (x + sx, y + sy), (x + sx + sw, y + sy + sh), (0, 0, 255), 1)

        lines = [
            f"frontal={face_count}, profile={profile_count}, eyes={eye_count}, smile={smile_count}",
            f"scaleFactor={scale_factor:.2f}, minNeighbors={min_neighbors}, minSize={min_size}",
            "Haar-like features + boosted cascades + sliding windows",
        ]
        if not self.cascades:
            lines.append("No cascades loaded from cv2.data.haarcascades.")
        return out, lines

    def _apply_hog_descriptor(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        scale_pct = max(10, values["ROI Scale %"])
        cx_pct = values["Center X %"]
        cy_pct = values["Center Y %"]
        show_grad = values["ShowGrad"] == 1

        h, w = self.image.shape[:2]
        base_h = int(min(h, 2 * w))
        roi_h = max(32, int(base_h * (scale_pct / 100.0)))
        roi_w = max(16, roi_h // 2)
        cx = int((cx_pct / 100.0) * (w - 1))
        cy = int((cy_pct / 100.0) * (h - 1))
        x1 = max(0, min(w - roi_w, cx - roi_w // 2))
        y1 = max(0, min(h - roi_h, cy - roi_h // 2))
        x2, y2 = x1 + roi_w, y1 + roi_h

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        roi = gray[y1:y2, x1:x2]
        roi_64x128 = cv2.resize(roi, (64, 128), interpolation=cv2.INTER_LINEAR)
        feat = self.hog_descriptor.compute(roi_64x128)

        left = self.image.copy()
        cv2.rectangle(left, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(left, "ROI", (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        if show_grad:
            gx = cv2.Sobel(roi_64x128, cv2.CV_32F, 1, 0, ksize=1)
            gy = cv2.Sobel(roi_64x128, cv2.CV_32F, 0, 1, ksize=1)
            mag = cv2.magnitude(gx, gy)
            mag_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            right = cv2.applyColorMap(mag_u8, cv2.COLORMAP_TURBO)
        else:
            right = cv2.cvtColor(roi_64x128, cv2.COLOR_GRAY2BGR)

        right = cv2.resize(right, (left.shape[1], left.shape[0]), interpolation=cv2.INTER_NEAREST)
        out = cv2.hconcat([left, right])
        lines = [
            f"ROI=({roi_w}x{roi_h}), center=({cx_pct}%,{cy_pct}%), scale={scale_pct}%",
            f"HOG vector length={len(feat)} (64x128 defaults to 3780)",
            "HOG: 8x8 cells, 9 bins, 16x16 block normalization",
        ]
        return out, lines

    def _apply_hog_detector(self, values: Dict[str, int]) -> Tuple[np.ndarray, List[str]]:
        hit_threshold = (values["HitThr (+/-2.0)"] - 20) / 10.0
        stride = 4 * (values["StrideIdx"] + 1)
        padding = 4 * (values["PaddingIdx"] + 1)
        scale = max(1.01, values["Scale x100"] / 100.0)
        final_threshold = values["FinalThr"]
        weight_thr = values["WThr x100"] / 100.0

        rects, weights = self.hog_detector.detectMultiScale(
            self.image,
            hitThreshold=hit_threshold,
            winStride=(stride, stride),
            padding=(padding, padding),
            scale=scale,
            finalThreshold=final_threshold,
        )

        out = self.image.copy()
        kept = 0
        for (x, y, w, h), score in zip(rects, weights):
            score_val = float(score)
            if score_val < weight_thr:
                continue
            kept += 1
            color = (0, 255, 0) if score_val >= 1.0 else (0, 165, 255)
            cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                out,
                f"{score_val:.2f}",
                (x, max(12, y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
            )

        lines = [
            f"raw={len(rects)}, kept={kept}, weight_thr={weight_thr:.2f}",
            f"hitThr={hit_threshold:.2f}, stride={stride}, pad={padding}, scale={scale:.2f}, finalThr={final_threshold}",
            "HOG + linear SVM detector (default people detector)",
        ]
        return out, lines

    def _show_mode_shortcuts(self) -> None:
        mode = self.mode_names[self.mode_index]
        print(f"[mode] {mode}")

    def _print_help(self) -> None:
        print(
            "\nUniversal CV Lab controls:\n"
            "  o : open image file (mac dialog via osascript, fallback terminal input)\n"
            "  s : save current output to tmp/cv_gui_outputs/\n"
            "  n : next technique\n"
            "  p : previous technique\n"
            "  r : reset current mode sliders to defaults\n"
            "  h : print this help\n"
            "  q or ESC : quit\n"
        )

    def _reset_current_mode(self) -> None:
        mode = self.mode_names[self.mode_index]
        for spec in self.mode_specs[mode]:
            cv2.setTrackbarPos(spec.name, CONTROLS_WINDOW, spec.default)

    def run(self) -> None:
        while True:
            values = self._read_values()
            requested_mode = values["Technique"]
            if requested_mode != self.mode_index:
                self._cache_mode_values(values)
                self._set_mode(requested_mode)
                continue

            mode = self.mode_names[self.mode_index]
            out, lines = self._apply_mode(mode, values)
            out = self._draw_overlay(out, mode, lines)
            out = self._resize_for_display(out, values["Display %"])

            self.last_output = out
            self.last_lines = lines
            cv2.imshow(OUTPUT_WINDOW, out)

            key = cv2.waitKey(20) & 0xFF
            if key in (27, ord("q")):
                break
            if key == ord("o"):
                self._open_image_dialog()
            elif key == ord("s"):
                self._save_output()
            elif key == ord("h"):
                self._print_help()
            elif key == ord("n"):
                next_mode = (self.mode_index + 1) % len(self.mode_names)
                cv2.setTrackbarPos("Technique", CONTROLS_WINDOW, next_mode)
            elif key == ord("p"):
                prev_mode = (self.mode_index - 1) % len(self.mode_names)
                cv2.setTrackbarPos("Technique", CONTROLS_WINDOW, prev_mode)
            elif key == ord("r"):
                self._reset_current_mode()

        cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Universal OpenCV GUI lab for CME 466")
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Optional path to starting image",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = UniversalCVLab(args.image)
    app.run()


if __name__ == "__main__":
    main()
