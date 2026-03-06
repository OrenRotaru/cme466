from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cv_pipeline_lab.core.executor import PipelineExecutor
from cv_pipeline_lab.core.export_notebook import write_notebook_export
from cv_pipeline_lab.core.export_python import export_python_script, write_python_export
from cv_pipeline_lab.core.registry import BlockRegistry
from cv_pipeline_lab.core.serialization import load_pipeline, save_pipeline
from cv_pipeline_lab.core.snippets import node_snippet
from cv_pipeline_lab.ui.block_palette import BlockPalette
from cv_pipeline_lab.ui.node_scene import NodeScene, NodeView
from cv_pipeline_lab.ui.preview_panel import PreviewPanel
from cv_pipeline_lab.ui.properties_panel import PropertiesPanel


class MainWindow(QMainWindow):
    def __init__(self, registry: BlockRegistry, image_override: str | None = None, pipeline_path: str | None = None) -> None:
        super().__init__()
        self.registry = registry
        self.executor = PipelineExecutor(registry)
        self.image_override = image_override
        self.current_pipeline_path: str | None = pipeline_path
        self.last_result = None
        self._auto_run_delay_ms = 200
        self._auto_run_timer = QTimer(self)
        self._auto_run_timer.setSingleShot(True)
        self._auto_run_timer.timeout.connect(self._auto_run_triggered)
        self._auto_run_force_full = False
        self._auto_run_changed_nodes: set[str] = set()
        self._param_update_in_progress = False
        self._saved_center_split_sizes: list[int] | None = None
        self._saved_right_split_sizes: list[int] | None = None
        self._saved_right_split_orientation: Qt.Orientation | None = None
        self._saved_tab_index: int = 0
        self._saved_tabs_bar_visible: bool = True
        self._entered_fullscreen_for_preview_focus = False

        self.setWindowTitle("CV Pipeline Lab")
        self.resize(1680, 960)

        self.palette = BlockPalette(self.registry)
        self.scene = NodeScene(self.registry)
        self.view = NodeView(self.scene)
        self.properties = PropertiesPanel(self.registry)

        self.preview_panel = PreviewPanel()
        self.snippet_text = QPlainTextEdit()
        self.snippet_text.setReadOnly(True)
        self.pipeline_code_text = QPlainTextEdit()
        self.pipeline_code_text.setReadOnly(True)
        self.run_log_text = QPlainTextEdit()
        self.run_log_text.setReadOnly(True)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.preview_panel, "Preview")
        self.tabs.addTab(self.snippet_text, "Code Snippet")
        self.tabs.addTab(self.pipeline_code_text, "Pipeline Code")
        self.tabs.addTab(self.run_log_text, "Run Log")

        self.right_top = QWidget()
        right_top_layout = QVBoxLayout(self.right_top)
        right_top_layout.setContentsMargins(0, 0, 0, 0)
        right_top_layout.addWidget(self.properties)

        self.right_bottom = QWidget()
        right_bottom_layout = QVBoxLayout(self.right_bottom)
        right_bottom_layout.setContentsMargins(0, 0, 0, 0)
        right_bottom_layout.addWidget(self.tabs)

        self.right_split = QSplitter(Qt.Orientation.Vertical)
        self.right_split.addWidget(self.right_top)
        self.right_split.addWidget(self.right_bottom)
        self.right_split.setSizes([360, 600])

        self.center_split = QSplitter(Qt.Orientation.Horizontal)
        self.center_split.addWidget(self.palette)
        self.center_split.addWidget(self.view)
        self.center_split.addWidget(self.right_split)
        self.center_split.setSizes([300, 900, 480])

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.addWidget(self.center_split)
        self.setCentralWidget(root)

        self._build_actions()
        self._wire_signals()

        if pipeline_path:
            self._open_pipeline_path(pipeline_path)

        self._refresh_pipeline_code_preview()

    def _build_actions(self) -> None:
        tb = self.addToolBar("Main")

        self.new_action = QAction("New", self)
        self.open_action = QAction("Open", self)
        self.save_action = QAction("Save", self)
        self.save_as_action = QAction("Save As", self)
        self.run_action = QAction("Run", self)
        self.auto_run_action = QAction("Auto Run", self)
        self.auto_run_action.setCheckable(True)
        self.preview_focus_action = QAction("Preview Fullscreen", self)
        self.preview_focus_action.setCheckable(True)
        self.recenter_action = QAction("Recenter", self)
        self.reset_view_action = QAction("Reset View", self)
        self.export_py_action = QAction("Export .py", self)
        self.export_nb_action = QAction("Export .ipynb", self)
        self.export_all_action = QAction("Export All", self)
        self.delete_action = QAction("Delete Selected", self)

        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.run_action.setShortcut("Ctrl+R")
        self.auto_run_action.setShortcut("Ctrl+Shift+R")
        self.preview_focus_action.setShortcut("F11")
        self.reset_view_action.setShortcut("Ctrl+0")
        self.delete_action.setShortcut(QKeySequence(Qt.Key.Key_Delete))

        for action in [
            self.new_action,
            self.open_action,
            self.save_action,
            self.save_as_action,
            self.run_action,
            self.auto_run_action,
            self.preview_focus_action,
            self.recenter_action,
            self.reset_view_action,
            self.export_py_action,
            self.export_nb_action,
            self.export_all_action,
            self.delete_action,
        ]:
            tb.addAction(action)

        self.new_action.triggered.connect(self.new_pipeline)
        self.open_action.triggered.connect(self.open_pipeline)
        self.save_action.triggered.connect(self.save_pipeline)
        self.save_as_action.triggered.connect(self.save_pipeline_as)
        self.run_action.triggered.connect(self.run_pipeline)
        self.auto_run_action.toggled.connect(self._on_auto_run_toggled)
        self.preview_focus_action.toggled.connect(self._on_preview_focus_toggled)
        self.recenter_action.triggered.connect(self.recenter_view)
        self.reset_view_action.triggered.connect(self.reset_view)
        self.export_py_action.triggered.connect(self.export_python)
        self.export_nb_action.triggered.connect(self.export_notebook)
        self.export_all_action.triggered.connect(self.export_all)
        self.delete_action.triggered.connect(self.scene.remove_selected)

    def _wire_signals(self) -> None:
        self.palette.block_chosen.connect(self._add_block_center)
        self.scene.node_selected.connect(self._on_node_selected)
        self.scene.log_message.connect(self._log)
        self.scene.graph_changed.connect(self._on_graph_changed)
        self.properties.params_changed.connect(self._on_params_changed)
        self.properties.enabled_changed.connect(self.scene.set_node_enabled)
        self.preview_panel.crop_params_changed.connect(self._on_crop_params_changed)

    def _add_block_center(self, block_type: str) -> None:
        center = self.view.mapToScene(self.view.viewport().rect().center())
        self.scene.add_node(block_type, center)

    def _on_node_selected(self, node_id: str | None) -> None:
        node = self.scene.get_node(node_id) if node_id else None
        self.properties.set_node(node)

        if node is None:
            self.snippet_text.setPlainText("")
            self.preview_panel.clear()
            return

        self.snippet_text.setPlainText(node_snippet(self.registry, node.block_type, node.params))
        self._refresh_preview_for_node(node.id)

    def _on_params_changed(self, node_id: str, params: dict) -> None:
        self._param_update_in_progress = True
        self.scene.update_node_params(node_id, params)
        self._param_update_in_progress = False
        self._auto_run_changed_nodes.add(node_id)
        self._schedule_auto_run()
        node = self.scene.get_node(node_id)
        if node is not None:
            self.snippet_text.setPlainText(node_snippet(self.registry, node.block_type, node.params))
            if node.block_type == "ImageCrop":
                source = self._crop_source_image(node.id)
                self.preview_panel.set_crop_editor(node.id, source, node.params)

    def _on_crop_params_changed(self, node_id: str, crop_params: dict) -> None:
        node = self.scene.get_node(node_id)
        if node is None:
            return
        merged = dict(node.params)
        merged.update(crop_params)
        self._param_update_in_progress = True
        self.scene.update_node_params(node_id, merged)
        self._param_update_in_progress = False
        self._auto_run_changed_nodes.add(node_id)
        self._schedule_auto_run()
        node = self.scene.get_node(node_id)
        if node is None:
            return
        self.properties.set_node(node)
        self.snippet_text.setPlainText(node_snippet(self.registry, node.block_type, node.params))
        source = self._crop_source_image(node_id)
        self.preview_panel.set_crop_editor(node_id, source, node.params)

    def _crop_source_image(self, node_id: str) -> np.ndarray | None:
        if self.last_result is None:
            return None
        for edge in self.scene.edge_models.values():
            if edge.dst_node != node_id or edge.dst_port != "image":
                continue
            src_res = self.last_result.node_results.get(edge.src_node)
            if src_res is None or src_res.error is not None or src_res.skipped:
                continue
            val = src_res.outputs.get(edge.src_port)
            if isinstance(val, np.ndarray):
                return val
        return None

    def _refresh_preview_for_node(self, node_id: str) -> None:
        node = self.scene.get_node(node_id)
        if node is None:
            self.preview_panel.clear()
            return
        node_res = self.last_result.node_results.get(node.id) if self.last_result is not None else None
        self.preview_panel.set_result(node.id, node_res)
        if node.block_type == "ImageCrop":
            source = self._crop_source_image(node.id)
            self.preview_panel.set_crop_editor(node.id, source, node.params)

    def _refresh_pipeline_code_preview(self) -> None:
        pipeline = self.scene.build_pipeline()
        self.pipeline_code_text.setPlainText(export_python_script(pipeline, self.registry))

    def _on_graph_changed(self) -> None:
        self._refresh_pipeline_code_preview()
        if self._param_update_in_progress:
            return
        self._auto_run_force_full = True
        self._schedule_auto_run()

    def _schedule_auto_run(self, delay_ms: int | None = None) -> None:
        if not self.auto_run_action.isChecked():
            return
        d = self._auto_run_delay_ms if delay_ms is None else max(0, int(delay_ms))
        self._auto_run_timer.start(d)

    def _on_auto_run_toggled(self, enabled: bool) -> None:
        if enabled:
            self._log("Auto Run enabled")
            self._auto_run_force_full = True
            self._schedule_auto_run(delay_ms=0)
        else:
            self._auto_run_timer.stop()
            self._auto_run_force_full = False
            self._auto_run_changed_nodes.clear()
            self._log("Auto Run disabled")

    def _on_preview_focus_toggled(self, enabled: bool) -> None:
        if enabled:
            self._saved_center_split_sizes = self.center_split.sizes()
            self._saved_right_split_sizes = self.right_split.sizes()
            self._saved_right_split_orientation = self.right_split.orientation()
            self._saved_tab_index = self.tabs.currentIndex()
            self._saved_tabs_bar_visible = self.tabs.tabBar().isVisible()

            self.tabs.setCurrentWidget(self.preview_panel)
            self.tabs.tabBar().setVisible(False)
            self.preview_panel.set_focus_mode(True)
            self.palette.setVisible(False)
            self.view.setVisible(False)
            self.center_split.setSizes([0, 0, 1])
            self.right_split.setOrientation(Qt.Orientation.Horizontal)
            self.right_top.setMinimumWidth(220)
            self.right_top.setMaximumWidth(560)
            prop_w = max(260, int(self.width() * 0.2))
            self.right_split.setSizes([prop_w, max(900, self.width() - prop_w)])

            if not self.isFullScreen():
                self._entered_fullscreen_for_preview_focus = True
                self.showFullScreen()
            else:
                self._entered_fullscreen_for_preview_focus = False
            self._log("Preview fullscreen mode enabled")
            return

        self.palette.setVisible(True)
        self.view.setVisible(True)
        if self._saved_tab_index < self.tabs.count():
            self.tabs.setCurrentIndex(self._saved_tab_index)
        self.tabs.tabBar().setVisible(self._saved_tabs_bar_visible)
        self.preview_panel.set_focus_mode(False)
        if self._saved_right_split_orientation is not None:
            self.right_split.setOrientation(self._saved_right_split_orientation)
        self.right_top.setMinimumWidth(0)
        self.right_top.setMaximumWidth(16777215)
        if self._saved_center_split_sizes is not None:
            self.center_split.setSizes(self._saved_center_split_sizes)
        if self._saved_right_split_sizes is not None:
            self.right_split.setSizes(self._saved_right_split_sizes)
        if self._entered_fullscreen_for_preview_focus and self.isFullScreen():
            self.showNormal()
        self._entered_fullscreen_for_preview_focus = False
        self._log("Preview fullscreen mode disabled")

    def _auto_run_triggered(self) -> None:
        if not self.auto_run_action.isChecked():
            return

        changed_nodes = set(self._auto_run_changed_nodes)
        force_full = self._auto_run_force_full
        self._auto_run_changed_nodes.clear()
        self._auto_run_force_full = False
        self._execute_pipeline(auto=True, changed_nodes=changed_nodes, force_full=force_full)

    def _execute_pipeline(self, auto: bool = False, changed_nodes: set[str] | None = None, force_full: bool = False) -> None:
        pipeline = self._require_pipeline()
        self.scene.clear_error_states()
        if not auto:
            self.run_log_text.clear()

        if auto and not force_full and changed_nodes and self.last_result is not None:
            result = self.executor.run_incremental(
                pipeline,
                changed_nodes=changed_nodes,
                previous_result=self.last_result,
                image_override=self.image_override,
                pipeline_path=self.current_pipeline_path,
            )
        else:
            result = self.executor.run(
                pipeline,
                image_override=self.image_override,
                pipeline_path=self.current_pipeline_path,
            )
        self.last_result = result

        if result.validation_errors:
            if auto:
                self.statusBar().showMessage(f"Auto-run validation: {result.validation_errors[0]}", 2500)
            else:
                for err in result.validation_errors:
                    self._log(f"[validation] {err}")
            return

        for node_id in result.order:
            node_res = result.node_results.get(node_id)
            if node_res and node_res.error:
                self.scene.set_node_error(node_id, True)

        if not auto:
            for line in result.logs:
                self._log(line)

        selected = self.scene.selectedItems()
        if selected:
            selected_node = selected[0].node_id if hasattr(selected[0], "node_id") else None
            if selected_node:
                self._refresh_preview_for_node(selected_node)
        else:
            for node_id in reversed(result.order):
                node_res = result.node_results.get(node_id)
                if node_res and not node_res.error and "image" in node_res.outputs:
                    self.preview_panel.set_result(node_id, node_res)
                    self.preview_panel.set_crop_editor(None, None, None)
                    break

    def recenter_view(self) -> None:
        self.view.recenter_on_nodes(reset_zoom=False)
        self._log("Recentered view")

    def reset_view(self) -> None:
        self.view.recenter_on_nodes(reset_zoom=True)
        self._log("Reset view")

    def _log(self, text: str) -> None:
        self.run_log_text.appendPlainText(text)
        self.statusBar().showMessage(text, 3000)

    def new_pipeline(self) -> None:
        self.scene.clear_all()
        self.current_pipeline_path = None
        self.last_result = None
        self.preview_panel.clear()
        self.run_log_text.clear()
        self._log("New pipeline")

    def _open_pipeline_path(self, path: str) -> None:
        pipeline = load_pipeline(path)
        self.scene.load_pipeline(pipeline)
        self.current_pipeline_path = path
        self.last_result = None
        self.preview_panel.clear()
        self._log(f"Opened: {path}")

    def open_pipeline(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Pipeline", str(Path.cwd()), "Pipeline JSON (*.json)")
        if not path:
            return
        self._open_pipeline_path(path)

    def save_pipeline(self) -> None:
        if not self.current_pipeline_path:
            self.save_pipeline_as()
            return
        pipeline = self.scene.build_pipeline()
        save_pipeline(pipeline, self.current_pipeline_path)
        self._log(f"Saved: {self.current_pipeline_path}")

    def save_pipeline_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Pipeline", str(Path.cwd() / "pipeline.json"), "Pipeline JSON (*.json)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        self.current_pipeline_path = path
        self.save_pipeline()

    def _require_pipeline(self):
        return self.scene.build_pipeline()

    def run_pipeline(self) -> None:
        self._execute_pipeline(auto=False)

    def export_python(self) -> None:
        pipeline = self._require_pipeline()
        path, _ = QFileDialog.getSaveFileName(self, "Export Python", str(Path.cwd() / "pipeline_export.py"), "Python (*.py)")
        if not path:
            return
        if not path.lower().endswith(".py"):
            path += ".py"
        write_python_export(path, pipeline, self.registry)
        self._log(f"Exported Python: {path}")

    def export_notebook(self) -> None:
        pipeline = self._require_pipeline()
        path, _ = QFileDialog.getSaveFileName(self, "Export Notebook", str(Path.cwd() / "pipeline_export.ipynb"), "Notebook (*.ipynb)")
        if not path:
            return
        if not path.lower().endswith(".ipynb"):
            path += ".ipynb"
        write_notebook_export(path, pipeline, self.registry)
        self._log(f"Exported Notebook: {path}")

    def export_all(self) -> None:
        base_dir = QFileDialog.getExistingDirectory(self, "Export All", str(Path.cwd()))
        if not base_dir:
            return
        base = Path(base_dir)
        pipeline = self._require_pipeline()

        json_path = base / "pipeline.json"
        py_path = base / "pipeline_export.py"
        nb_path = base / "pipeline_export.ipynb"

        save_pipeline(pipeline, json_path)
        write_python_export(py_path, pipeline, self.registry)
        write_notebook_export(nb_path, pipeline, self.registry)

        self._log(f"Exported JSON: {json_path}")
        self._log(f"Exported Python: {py_path}")
        self._log(f"Exported Notebook: {nb_path}")

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Escape and self.preview_focus_action.isChecked():
            self.preview_focus_action.setChecked(False)
            event.accept()
            return
        super().keyPressEvent(event)
