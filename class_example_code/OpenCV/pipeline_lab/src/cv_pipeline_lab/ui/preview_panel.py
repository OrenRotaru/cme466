from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QSplitter, QTextEdit, QVBoxLayout, QWidget

from cv_pipeline_lab.core.types import NodeRunResult


def _image_to_pixmap(img: np.ndarray) -> QPixmap:
    if img.ndim == 2:
        rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    else:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    qimg = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


class PreviewImageWidget(QWidget):
    crop_committed = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(260)
        self.setMouseTracking(True)
        self._pixmap: QPixmap | None = None
        self._img_w = 0
        self._img_h = 0
        self._editable = False
        self._crop_rect_img = QRectF()
        self._drag_mode: str | None = None
        self._drag_start = QPointF()
        self._drag_orig_rect = QRectF()
        self._min_size = 4.0
        self._tol = 8.0

    def set_image(self, img: np.ndarray | None, crop_params: dict[str, Any] | None = None, editable: bool = False) -> None:
        if img is None:
            self._pixmap = None
            self._img_w = 0
            self._img_h = 0
            self._editable = False
            self._crop_rect_img = QRectF()
            self.update()
            return

        self._pixmap = _image_to_pixmap(img)
        self._img_w = int(self._pixmap.width())
        self._img_h = int(self._pixmap.height())
        self._editable = editable

        if crop_params:
            x = float(crop_params.get("x", 0))
            y = float(crop_params.get("y", 0))
            w = float(crop_params.get("width", 0))
            h = float(crop_params.get("height", 0))
            if w <= 0:
                w = self._img_w - x
            if h <= 0:
                h = self._img_h - y
            x = max(0.0, min(x, self._img_w - 1.0))
            y = max(0.0, min(y, self._img_h - 1.0))
            w = max(self._min_size, min(w, self._img_w - x))
            h = max(self._min_size, min(h, self._img_h - y))
            self._crop_rect_img = QRectF(x, y, w, h)
        else:
            self._crop_rect_img = QRectF(0.0, 0.0, float(self._img_w), float(self._img_h))
        self.update()

    def set_editable(self, editable: bool) -> None:
        self._editable = editable
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(32, 32, 32))

        if self._pixmap is None:
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No preview")
            return

        disp = self._display_rect()
        painter.drawPixmap(disp.toRect(), self._pixmap)

        if self._editable and self._crop_rect_img.isValid():
            crop_v = self._img_to_view_rect(self._crop_rect_img)
            shade = QColor(0, 0, 0, 110)
            painter.fillRect(QRectF(disp.left(), disp.top(), disp.width(), max(0.0, crop_v.top() - disp.top())), shade)
            painter.fillRect(QRectF(disp.left(), crop_v.bottom(), disp.width(), max(0.0, disp.bottom() - crop_v.bottom())), shade)
            painter.fillRect(QRectF(disp.left(), crop_v.top(), max(0.0, crop_v.left() - disp.left()), crop_v.height()), shade)
            painter.fillRect(QRectF(crop_v.right(), crop_v.top(), max(0.0, disp.right() - crop_v.right()), crop_v.height()), shade)

            painter.setPen(QPen(QColor(0, 220, 255), 2))
            painter.drawRect(crop_v)

            for handle in self._handle_rects(crop_v):
                painter.fillRect(handle, QColor(0, 220, 255))

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self.update()
        super().resizeEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if not self._editable or self._pixmap is None or event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        mode = self._hit_mode(event.position())
        if mode is None:
            super().mousePressEvent(event)
            return
        self._drag_mode = mode
        self._drag_start = self._view_to_img_point(event.position())
        self._drag_orig_rect = QRectF(self._crop_rect_img)
        event.accept()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._pixmap is None:
            super().mouseMoveEvent(event)
            return

        if self._drag_mode is None:
            mode = self._hit_mode(event.position()) if self._editable else None
            self._set_cursor_for_mode(mode)
            super().mouseMoveEvent(event)
            return

        p = self._view_to_img_point(event.position())
        dx = p.x() - self._drag_start.x()
        dy = p.y() - self._drag_start.y()
        l = self._drag_orig_rect.left()
        t = self._drag_orig_rect.top()
        r = self._drag_orig_rect.right()
        b = self._drag_orig_rect.bottom()

        if self._drag_mode == "move":
            w = self._drag_orig_rect.width()
            h = self._drag_orig_rect.height()
            nl = min(max(0.0, l + dx), max(0.0, self._img_w - w))
            nt = min(max(0.0, t + dy), max(0.0, self._img_h - h))
            self._crop_rect_img = QRectF(nl, nt, w, h)
            self.update()
            return

        if "left" in self._drag_mode:
            l = p.x()
        if "right" in self._drag_mode:
            r = p.x()
        if "top" in self._drag_mode:
            t = p.y()
        if "bottom" in self._drag_mode:
            b = p.y()

        if l > r:
            l, r = r, l
        if t > b:
            t, b = b, t

        if r - l < self._min_size:
            if "left" in self._drag_mode:
                l = r - self._min_size
            else:
                r = l + self._min_size
        if b - t < self._min_size:
            if "top" in self._drag_mode:
                t = b - self._min_size
            else:
                b = t + self._min_size

        l = max(0.0, min(l, self._img_w - self._min_size))
        t = max(0.0, min(t, self._img_h - self._min_size))
        r = max(self._min_size, min(r, self._img_w))
        b = max(self._min_size, min(b, self._img_h))
        if r - l < self._min_size:
            r = min(self._img_w, l + self._min_size)
        if b - t < self._min_size:
            b = min(self._img_h, t + self._min_size)

        self._crop_rect_img = QRectF(l, t, r - l, b - t)
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_mode is not None and event.button() == Qt.MouseButton.LeftButton:
            self._drag_mode = None
            self._set_cursor_for_mode(None)
            self.crop_committed.emit(self._crop_params())
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _display_rect(self) -> QRectF:
        if self._pixmap is None:
            return QRectF()
        margin = 8.0
        aw = max(1.0, self.width() - 2.0 * margin)
        ah = max(1.0, self.height() - 2.0 * margin)
        iw = float(self._pixmap.width())
        ih = float(self._pixmap.height())
        s = min(aw / iw, ah / ih)
        dw = iw * s
        dh = ih * s
        x = (self.width() - dw) * 0.5
        y = (self.height() - dh) * 0.5
        return QRectF(x, y, dw, dh)

    def _img_to_view_rect(self, r: QRectF) -> QRectF:
        disp = self._display_rect()
        sx = disp.width() / max(1.0, float(self._img_w))
        sy = disp.height() / max(1.0, float(self._img_h))
        return QRectF(
            disp.left() + r.left() * sx,
            disp.top() + r.top() * sy,
            r.width() * sx,
            r.height() * sy,
        )

    def _view_to_img_point(self, p: QPointF) -> QPointF:
        disp = self._display_rect()
        if disp.width() <= 0 or disp.height() <= 0:
            return QPointF(0.0, 0.0)
        cx = min(max(p.x(), disp.left()), disp.right())
        cy = min(max(p.y(), disp.top()), disp.bottom())
        x = (cx - disp.left()) * float(self._img_w) / disp.width()
        y = (cy - disp.top()) * float(self._img_h) / disp.height()
        x = min(max(0.0, x), float(max(0, self._img_w - 1)))
        y = min(max(0.0, y), float(max(0, self._img_h - 1)))
        return QPointF(x, y)

    def _handle_rects(self, crop_v: QRectF) -> list[QRectF]:
        s = 8.0
        hs = s * 0.5
        pts = [
            QPointF(crop_v.left(), crop_v.top()),
            QPointF(crop_v.right(), crop_v.top()),
            QPointF(crop_v.left(), crop_v.bottom()),
            QPointF(crop_v.right(), crop_v.bottom()),
        ]
        return [QRectF(p.x() - hs, p.y() - hs, s, s) for p in pts]

    def _hit_mode(self, view_pos: QPointF) -> str | None:
        if not self._editable or self._pixmap is None or not self._crop_rect_img.isValid():
            return None
        crop_v = self._img_to_view_rect(self._crop_rect_img)
        x = view_pos.x()
        y = view_pos.y()
        l = crop_v.left()
        r = crop_v.right()
        t = crop_v.top()
        b = crop_v.bottom()
        tol = self._tol

        near_l = abs(x - l) <= tol
        near_r = abs(x - r) <= tol
        near_t = abs(y - t) <= tol
        near_b = abs(y - b) <= tol
        inside = crop_v.contains(view_pos)

        if near_l and near_t:
            return "top_left"
        if near_r and near_t:
            return "top_right"
        if near_l and near_b:
            return "bottom_left"
        if near_r and near_b:
            return "bottom_right"
        if near_l and t + tol < y < b - tol:
            return "left"
        if near_r and t + tol < y < b - tol:
            return "right"
        if near_t and l + tol < x < r - tol:
            return "top"
        if near_b and l + tol < x < r - tol:
            return "bottom"
        if inside:
            return "move"
        return None

    def _set_cursor_for_mode(self, mode: str | None) -> None:
        if mode in ("top_left", "bottom_right"):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif mode in ("top_right", "bottom_left"):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif mode in ("left", "right"):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif mode in ("top", "bottom"):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif mode == "move":
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.unsetCursor()

    def _crop_params(self) -> dict[str, int]:
        r = self._crop_rect_img
        return {
            "x": int(round(r.left())),
            "y": int(round(r.top())),
            "width": max(1, int(round(r.width()))),
            "height": max(1, int(round(r.height()))),
        }


class PreviewPanel(QWidget):
    crop_params_changed = Signal(str, dict)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_widget = PreviewImageWidget()
        self.image_widget.setStyleSheet("background: #202020; border: 1px solid #444;")
        self.image_widget.crop_committed.connect(self._on_crop_committed)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setMinimumHeight(70)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.image_widget)
        self.splitter.addWidget(self.text)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, True)
        self.splitter.setStretchFactor(0, 10)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([760, 120])

        layout.addWidget(self.splitter)

        self._crop_node_id: str | None = None
        self._base_lines: list[str] = []
        self._focus_mode = False

    def clear(self) -> None:
        self.image_widget.set_image(None)
        self.text.setPlainText("")
        self._crop_node_id = None
        self._base_lines = []

    def set_result(self, node_id: str, result: NodeRunResult | None) -> None:
        self._crop_node_id = None
        self._base_lines = []

        if result is None:
            self.image_widget.set_image(None)
            self._base_lines = [f"Node {node_id}: no result yet"]
            self.text.setPlainText("\n".join(self._base_lines))
            return

        if result.error:
            self.image_widget.set_image(None)
            self._base_lines = [f"Node {node_id} error:", result.error]
            self.text.setPlainText("\n".join(self._base_lines))
            return

        img = result.outputs.get("image") if result.outputs else None
        if isinstance(img, np.ndarray):
            self.image_widget.set_image(img, editable=False)
        else:
            self.image_widget.set_image(None)

        self._base_lines = [f"Node {node_id} outputs: {list(result.outputs.keys())}"]
        meta = result.outputs.get("meta") if result.outputs else None
        if meta is not None:
            self._base_lines.append(f"meta: {meta}")
        dets = result.outputs.get("detections") if result.outputs else None
        if dets is not None:
            self._base_lines.append(f"detections: {len(dets)}")
        fv = result.outputs.get("feature_vector") if result.outputs else None
        if fv is not None:
            try:
                self._base_lines.append(f"feature_vector_length: {len(fv)}")
            except Exception:  # noqa: BLE001
                pass
        self.text.setPlainText("\n".join(self._base_lines))

    def set_crop_editor(self, node_id: str | None, source_image: np.ndarray | None, params: dict[str, Any] | None) -> None:
        if node_id is None or source_image is None or params is None:
            self._crop_node_id = None
            self.image_widget.set_editable(False)
            self.text.setPlainText("\n".join(self._base_lines))
            return

        self._crop_node_id = node_id
        self.image_widget.set_image(source_image, crop_params=params, editable=True)
        lines = list(self._base_lines)
        lines.append("Crop editor: drag inside box to move, drag edges/corners to resize.")
        self.text.setPlainText("\n".join(lines))

    def _on_crop_committed(self, params: dict[str, int]) -> None:
        if self._crop_node_id is None:
            return
        self.crop_params_changed.emit(self._crop_node_id, params)

    def set_focus_mode(self, enabled: bool) -> None:
        self._focus_mode = bool(enabled)
        if self._focus_mode:
            self.text.setMaximumHeight(140)
            self.splitter.setSizes([max(500, self.height() - 120), 110])
        else:
            self.text.setMaximumHeight(16777215)
            self.splitter.setSizes([760, 120])
