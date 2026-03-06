from __future__ import annotations

import uuid
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
)

from cv_pipeline_lab.core.registry import BlockRegistry
from cv_pipeline_lab.core.types import EdgeModel, NodeModel, PipelineModel


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class PortGraphicsItem(QGraphicsEllipseItem):
    def __init__(self, node_id: str, port_name: str, port_type: str, is_output: bool, parent: QGraphicsItem) -> None:
        super().__init__(-6, -6, 12, 12, parent)
        self.node_id = node_id
        self.port_name = port_name
        self.port_type = port_type
        self.is_output = is_output
        color = QColor(230, 180, 60) if is_output else QColor(80, 170, 230)
        self.setBrush(color)
        self.setPen(QPen(Qt.black, 1))
        self.setZValue(3)


class EdgeGraphicsItem(QGraphicsPathItem):
    def __init__(self, edge_id: str, src_port: PortGraphicsItem, dst_port: PortGraphicsItem) -> None:
        super().__init__()
        self.edge_id = edge_id
        self.src_port = src_port
        self.dst_port = dst_port
        self.setPen(QPen(QColor(180, 180, 180), 2))
        self.setZValue(1)
        self.update_path()

    def update_path(self) -> None:
        p1 = self.src_port.scenePos()
        p2 = self.dst_port.scenePos()
        dx = max(40.0, abs(p2.x() - p1.x()) * 0.4)

        path = QPainterPath(p1)
        path.cubicTo(p1.x() + dx, p1.y(), p2.x() - dx, p2.y(), p2.x(), p2.y())
        self.setPath(path)


class NodeGraphicsItem(QGraphicsRectItem):
    WIDTH = 230

    def __init__(
        self,
        node: NodeModel,
        title: str,
        input_ports: list[tuple[str, str, str]],
        output_ports: list[tuple[str, str, str]],
        is_concept: bool = False,
    ) -> None:
        max_ports = max(len(input_ports), len(output_ports), 1)
        self.height = 54 + max_ports * 24
        super().__init__(0, 0, self.WIDTH, self.height)
        self.node_id = node.id
        self.input_ports: dict[str, PortGraphicsItem] = {}
        self.output_ports: dict[str, PortGraphicsItem] = {}
        self.is_concept = is_concept
        self.error_state = False

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(2)

        self.title_text = QGraphicsSimpleTextItem(title, self)
        self.title_text.setPos(10, 6)

        if is_concept:
            self.setBrush(QColor(60, 55, 80))
        else:
            self.setBrush(QColor(55, 60, 65))
        self.setPen(QPen(QColor(120, 120, 120), 2))

        y0 = 32
        for i, (name, ptype, pdesc) in enumerate(input_ports):
            y = y0 + i * 24
            label = QGraphicsSimpleTextItem(f"{name}:{ptype}", self)
            label.setPos(12, y - 8)
            if pdesc:
                label.setToolTip(pdesc)
            port = PortGraphicsItem(node.id, name, ptype, is_output=False, parent=self)
            if pdesc:
                port.setToolTip(f"{name} ({ptype})\n{pdesc}")
            port.setPos(4, y)
            self.input_ports[name] = port

        for i, (name, ptype, pdesc) in enumerate(output_ports):
            y = y0 + i * 24
            label = QGraphicsSimpleTextItem(f"{name}:{ptype}", self)
            tw = label.boundingRect().width()
            label.setPos(self.WIDTH - tw - 16, y - 8)
            if pdesc:
                label.setToolTip(pdesc)
            port = PortGraphicsItem(node.id, name, ptype, is_output=True, parent=self)
            if pdesc:
                port.setToolTip(f"{name} ({ptype})\n{pdesc}")
            port.setPos(self.WIDTH - 4, y)
            self.output_ports[name] = port

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any):
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene() is not None:
            scene = self.scene()
            if isinstance(scene, NodeScene):
                scene.on_node_moved(self.node_id, self.pos())
        return super().itemChange(change, value)

    def set_error_state(self, is_error: bool) -> None:
        self.error_state = is_error
        if is_error:
            self.setPen(QPen(QColor(220, 70, 70), 3))
        else:
            self.setPen(QPen(QColor(120, 120, 120), 2))


class NodeScene(QGraphicsScene):
    node_selected = Signal(object)
    graph_changed = Signal()
    log_message = Signal(str)

    def __init__(self, registry: BlockRegistry) -> None:
        super().__init__()
        self.registry = registry
        self.node_models: dict[str, NodeModel] = {}
        self.node_items: dict[str, NodeGraphicsItem] = {}
        self.edge_models: dict[str, EdgeModel] = {}
        self.edge_items: dict[str, EdgeGraphicsItem] = {}
        self._pending_output: PortGraphicsItem | None = None
        # Keep a generous workspace so panning/zooming does not clamp to local node bounds.
        self.setSceneRect(-50000.0, -50000.0, 100000.0, 100000.0)

        self.selectionChanged.connect(self._on_selection_changed)

    def clear_all(self) -> None:
        self.clear()
        self.node_models.clear()
        self.node_items.clear()
        self.edge_models.clear()
        self.edge_items.clear()
        self._pending_output = None
        self.graph_changed.emit()

    def add_node(self, block_type: str, scene_pos: QPointF) -> str:
        spec = self.registry.get_spec(block_type)
        node_id = _id("node")
        params = self.registry.default_params(block_type)
        node = NodeModel(
            id=node_id,
            block_type=block_type,
            title=spec.title,
            x=float(scene_pos.x()),
            y=float(scene_pos.y()),
            params=params,
            enabled=True,
        )
        self.node_models[node_id] = node

        in_ports = [(p.name, p.type, self._port_desc(p.description, p.type)) for p in spec.input_ports]
        out_ports = [(p.name, p.type, self._port_desc(p.description, p.type)) for p in spec.output_ports]
        item = NodeGraphicsItem(node, spec.title, in_ports, out_ports, is_concept=spec.is_concept)
        item.setPos(scene_pos)
        self.addItem(item)
        self.node_items[node_id] = item

        self.graph_changed.emit()
        return node_id

    def _remove_edge(self, edge_id: str) -> None:
        edge_item = self.edge_items.pop(edge_id, None)
        if edge_item is not None:
            self.removeItem(edge_item)
        self.edge_models.pop(edge_id, None)

    def remove_node(self, node_id: str) -> None:
        # Remove all connected edges first.
        for edge_id, edge in list(self.edge_models.items()):
            if edge.src_node == node_id or edge.dst_node == node_id:
                self._remove_edge(edge_id)
        item = self.node_items.pop(node_id, None)
        if item is not None:
            self.removeItem(item)
        self.node_models.pop(node_id, None)
        self.graph_changed.emit()

    def remove_selected(self) -> None:
        selected_nodes = [i for i in self.selectedItems() if isinstance(i, NodeGraphicsItem)]
        for item in selected_nodes:
            self.remove_node(item.node_id)

    def _on_selection_changed(self) -> None:
        selected_nodes = [i for i in self.selectedItems() if isinstance(i, NodeGraphicsItem)]
        if selected_nodes:
            self.node_selected.emit(selected_nodes[0].node_id)
        else:
            self.node_selected.emit(None)

    def _find_dst_edge(self, dst_node: str, dst_port: str) -> str | None:
        for edge_id, edge in self.edge_models.items():
            if edge.dst_node == dst_node and edge.dst_port == dst_port:
                return edge_id
        return None

    def connect_ports(self, src: PortGraphicsItem, dst: PortGraphicsItem) -> None:
        if not src.is_output or dst.is_output:
            self.log_message.emit("Connect from output port to input port.")
            return
        if src.node_id == dst.node_id:
            self.log_message.emit("Self-connections are not allowed.")
            return
        if src.port_type != dst.port_type and not (src.port_type == "mask" and dst.port_type == "image") and dst.port_type != "meta":
            self.log_message.emit(f"Type mismatch: {src.port_type} -> {dst.port_type}")
            return

        # Keep one incoming edge per input port.
        old_id = self._find_dst_edge(dst.node_id, dst.port_name)
        if old_id is not None:
            self._remove_edge(old_id)

        edge_id = _id("edge")
        model = EdgeModel(
            id=edge_id,
            src_node=src.node_id,
            src_port=src.port_name,
            dst_node=dst.node_id,
            dst_port=dst.port_name,
        )
        item = EdgeGraphicsItem(edge_id, src, dst)
        self.addItem(item)

        self.edge_models[edge_id] = model
        self.edge_items[edge_id] = item
        self.graph_changed.emit()

    def on_node_moved(self, node_id: str, pos: QPointF) -> None:
        model = self.node_models.get(node_id)
        if model is not None:
            model.x = float(pos.x())
            model.y = float(pos.y())
        for edge in self.edge_models.values():
            if edge.src_node == node_id or edge.dst_node == node_id:
                edge_item = self.edge_items.get(edge.id)
                if edge_item:
                    edge_item.update_path()

    def set_node_error(self, node_id: str, is_error: bool) -> None:
        item = self.node_items.get(node_id)
        if item is not None:
            item.set_error_state(is_error)

    def clear_error_states(self) -> None:
        for item in self.node_items.values():
            item.set_error_state(False)

    def update_node_params(self, node_id: str, params: dict[str, Any]) -> None:
        node = self.node_models.get(node_id)
        if node is None:
            return
        node.params = dict(params)
        self.graph_changed.emit()

    def set_node_enabled(self, node_id: str, enabled: bool) -> None:
        node = self.node_models.get(node_id)
        if node is None:
            return
        node.enabled = bool(enabled)
        self.graph_changed.emit()

    def get_node(self, node_id: str) -> NodeModel | None:
        return self.node_models.get(node_id)

    def node_bounds(self) -> QRectF | None:
        rect: QRectF | None = None
        for item in self.node_items.values():
            r = item.sceneBoundingRect()
            rect = r if rect is None else rect.united(r)
        return rect

    def build_pipeline(self) -> PipelineModel:
        nodes = sorted(self.node_models.values(), key=lambda n: n.id)
        edges = sorted(self.edge_models.values(), key=lambda e: e.id)
        return PipelineModel(nodes=list(nodes), edges=list(edges), notes=[], metadata={"app_version": "0.1.0"})

    def load_pipeline(self, pipeline: PipelineModel) -> None:
        self.clear_all()
        for node in pipeline.nodes:
            if not self.registry.has(node.block_type):
                self.log_message.emit(f"Unknown block type in file: {node.block_type}")
                continue
            spec = self.registry.get_spec(node.block_type)
            self.node_models[node.id] = node
            in_ports = [(p.name, p.type, self._port_desc(p.description, p.type)) for p in spec.input_ports]
            out_ports = [(p.name, p.type, self._port_desc(p.description, p.type)) for p in spec.output_ports]
            item = NodeGraphicsItem(node, node.title, in_ports, out_ports, is_concept=spec.is_concept)
            item.setPos(QPointF(node.x, node.y))
            self.addItem(item)
            self.node_items[node.id] = item

        for edge in pipeline.edges:
            src_item = self.node_items.get(edge.src_node)
            dst_item = self.node_items.get(edge.dst_node)
            if src_item is None or dst_item is None:
                continue
            src_port = src_item.output_ports.get(edge.src_port)
            dst_port = dst_item.input_ports.get(edge.dst_port)
            if src_port is None or dst_port is None:
                continue
            edge_item = EdgeGraphicsItem(edge.id, src_port, dst_port)
            self.addItem(edge_item)
            self.edge_models[edge.id] = edge
            self.edge_items[edge.id] = edge_item

        self.graph_changed.emit()

    def _port_desc(self, explicit: str, port_type: str) -> str:
        if explicit.strip():
            return explicit.strip()
        fallback = {
            "image": "BGR image matrix (numpy array).",
            "mask": "Single-channel mask image.",
            "detections": "List of detection objects with bbox/label/score.",
            "feature_vector": "Numeric feature vector array.",
            "meta": "Metadata dictionary for counts/metrics.",
        }
        return fallback.get(port_type, "")

    def mousePressEvent(self, event):  # type: ignore[override]
        item = None
        hit_items = self.items(event.scenePos())
        if hit_items:
            item = hit_items[0]
        if isinstance(item, PortGraphicsItem):
            if item.is_output:
                self._pending_output = item
                self.log_message.emit(f"Selected output port {item.node_id}.{item.port_name}")
            else:
                if self._pending_output is None:
                    self.log_message.emit("Select an output port first, then an input port.")
                else:
                    self.connect_ports(self._pending_output, item)
                    self._pending_output = None
            event.accept()
            return
        else:
            self._pending_output = None
        super().mousePressEvent(event)


class NodeView(QGraphicsView):
    def __init__(self, scene: NodeScene) -> None:
        super().__init__(scene)
        self.setAcceptDrops(True)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._space_pan_active = False
        self._pan_active = False
        self._pan_last_pos = None
        self._zoom_step = 1.15
        self._zoom_min = 0.2
        self._zoom_max = 5.0

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasFormat("application/x-cv-block-type"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):  # type: ignore[override]
        if event.mimeData().hasFormat("application/x-cv-block-type"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # type: ignore[override]
        if not event.mimeData().hasFormat("application/x-cv-block-type"):
            super().dropEvent(event)
            return
        block_type = bytes(event.mimeData().data("application/x-cv-block-type")).decode("utf-8")
        scene_pos = self.mapToScene(event.position().toPoint())
        scene = self.scene()
        if isinstance(scene, NodeScene):
            scene.add_node(block_type, scene_pos)
            scene.log_message.emit(f"Added block: {block_type}")
        event.acceptProposedAction()

    def _current_scale(self) -> float:
        return float(self.transform().m11())

    def recenter_on_nodes(self, reset_zoom: bool = False, padding: float = 120.0) -> None:
        scene = self.scene()
        if not isinstance(scene, NodeScene):
            return
        bounds = scene.node_bounds()
        if bounds is None or bounds.isNull():
            if reset_zoom:
                self.resetTransform()
            self.centerOn(QPointF(0.0, 0.0))
            return

        target = bounds.adjusted(-padding, -padding, padding, padding)
        if reset_zoom:
            self.fitInView(target, Qt.AspectRatioMode.KeepAspectRatio)
            current = self._current_scale()
            if current < self._zoom_min:
                self.scale(self._zoom_min / max(current, 1e-9), self._zoom_min / max(current, 1e-9))
            elif current > self._zoom_max:
                self.scale(self._zoom_max / max(current, 1e-9), self._zoom_max / max(current, 1e-9))
        else:
            self.centerOn(target.center())

    def _apply_zoom_factor(self, factor: float) -> None:
        current = self._current_scale()
        target = current * factor
        if target < self._zoom_min:
            factor = self._zoom_min / max(current, 1e-9)
        elif target > self._zoom_max:
            factor = self._zoom_max / max(current, 1e-9)
        if abs(factor - 1.0) < 1e-6:
            return
        self.scale(factor, factor)

    def wheelEvent(self, event) -> None:  # type: ignore[override]
        delta_y = event.angleDelta().y()
        if delta_y == 0:
            super().wheelEvent(event)
            return
        factor = self._zoom_step if delta_y > 0 else (1.0 / self._zoom_step)
        self._apply_zoom_factor(factor)
        event.accept()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.position().toPoint())
            shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            should_pan = self._space_pan_active or (item is None and not shift)
            if should_pan:
                self._pan_active = True
                self._pan_last_pos = event.position().toPoint()
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._pan_active and self._pan_last_pos is not None:
            pos = event.position().toPoint()
            delta = pos - self._pan_last_pos
            self._pan_last_pos = pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton and self._pan_active:
            self._pan_active = False
            self._pan_last_pos = None
            if self._space_pan_active:
                self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self._apply_zoom_factor(self._zoom_step)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Minus:
            self._apply_zoom_factor(1.0 / self._zoom_step)
            event.accept()
            return
        if event.key() == Qt.Key.Key_0:
            self.resetTransform()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            if not self._space_pan_active:
                self._space_pan_active = True
                if not self._pan_active:
                    self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            if self._space_pan_active:
                self._space_pan_active = False
                if self._pan_active:
                    self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                else:
                    self.viewport().unsetCursor()
            event.accept()
            return
        super().keyReleaseEvent(event)
