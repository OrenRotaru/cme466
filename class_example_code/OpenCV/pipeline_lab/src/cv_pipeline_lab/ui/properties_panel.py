from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cv_pipeline_lab.core.registry import BlockRegistry
from cv_pipeline_lab.core.types import BlockSpec, NodeModel, ParamSpec


class PropertiesPanel(QWidget):
    params_changed = Signal(str, dict)
    enabled_changed = Signal(str, bool)

    def __init__(self, registry: BlockRegistry) -> None:
        super().__init__()
        self.registry = registry
        self._node: NodeModel | None = None
        self._spec: BlockSpec | None = None
        self._editors: dict[str, QWidget] = {}
        self._param_specs: dict[str, ParamSpec] = {}
        self._row_widgets: dict[str, tuple[QLabel, QWidget]] = {}

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(4, 4, 4, 4)

        self.title_label = QLabel("No node selected")
        self.title_label.setWordWrap(True)
        root_layout.addWidget(self.title_label)

        self.block_help_label = QLabel("")
        self.block_help_label.setWordWrap(True)
        self.block_help_label.setTextFormat(Qt.TextFormat.RichText)
        root_layout.addWidget(self.block_help_label)

        self.io_help_label = QLabel("")
        self.io_help_label.setWordWrap(True)
        self.io_help_label.setTextFormat(Qt.TextFormat.RichText)
        root_layout.addWidget(self.io_help_label)

        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(True)
        self.enabled_checkbox.toggled.connect(self._on_enabled_toggled)
        root_layout.addWidget(self.enabled_checkbox)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        root_layout.addWidget(self.scroll)

        self.form_holder = QWidget()
        self.form_layout = QFormLayout(self.form_holder)
        self.scroll.setWidget(self.form_holder)

        self.hint_label = QLabel("Select a block to edit parameters.")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        root_layout.addWidget(self.hint_label)

    def clear(self) -> None:
        self._node = None
        self._spec = None
        self._editors.clear()
        self._param_specs.clear()
        self._row_widgets.clear()
        self.title_label.setText("No node selected")
        self.block_help_label.setText("")
        self.io_help_label.setText("")
        self.enabled_checkbox.setChecked(True)
        self._clear_form()

    def _clear_form(self) -> None:
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)

    def set_node(self, node: NodeModel | None) -> None:
        self._node = node
        self._editors.clear()
        self._param_specs.clear()
        self._row_widgets.clear()
        self._clear_form()

        if node is None:
            self.title_label.setText("No node selected")
            self.block_help_label.setText("")
            self.io_help_label.setText("")
            self.hint_label.setText("Select a block to edit parameters.")
            return

        self._spec = self.registry.normalized_spec(node.block_type)
        self.title_label.setText(f"{node.title}\n({node.block_type})")
        self.block_help_label.setText(f"<b>What It Does:</b> {self._spec.description or 'No description provided.'}")
        self.io_help_label.setText(self._format_port_help(self._spec))

        self.enabled_checkbox.blockSignals(True)
        self.enabled_checkbox.setChecked(node.enabled)
        self.enabled_checkbox.blockSignals(False)

        if not self._spec.params:
            self.hint_label.setText("This block has no editable parameters.")
            return

        self.hint_label.setText(self._spec.description or "")

        for ps in self._spec.params:
            editor = self._make_editor(ps, node.params.get(ps.name, ps.default))
            label = QLabel(ps.label or ps.name)
            if ps.help_text:
                label.setToolTip(ps.help_text)
                editor.setToolTip(ps.help_text)
            self._editors[ps.name] = editor
            self._param_specs[ps.name] = ps
            self._row_widgets[ps.name] = (label, editor)
            self.form_layout.addRow(label, editor)

        self._update_visibility()

    def _make_editor(self, ps: ParamSpec, value: Any) -> QWidget:
        if ps.type == "bool":
            w = QCheckBox()
            w.setChecked(bool(value))
            w.toggled.connect(self._emit_params)
            return w

        if ps.type == "int":
            w = QSpinBox()
            w.setRange(int(ps.min_value if ps.min_value is not None else -1000000), int(ps.max_value if ps.max_value is not None else 1000000))
            w.setSingleStep(int(ps.step if ps.step is not None else 1))
            w.setValue(int(value))
            w.valueChanged.connect(self._emit_params)
            return w

        if ps.type == "float":
            w = QDoubleSpinBox()
            w.setRange(float(ps.min_value if ps.min_value is not None else -1e9), float(ps.max_value if ps.max_value is not None else 1e9))
            w.setSingleStep(float(ps.step if ps.step is not None else 0.1))
            w.setDecimals(4)
            w.setValue(float(value))
            w.valueChanged.connect(self._emit_params)
            return w

        if ps.type == "enum":
            w = QComboBox()
            for opt in ps.options:
                w.addItem(opt)
            if str(value) in ps.options:
                w.setCurrentText(str(value))
            w.currentIndexChanged.connect(self._emit_params)
            return w

        w = QLineEdit(str(value))
        w.editingFinished.connect(self._emit_params)
        return w

    def _collect_params(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for name, editor in self._editors.items():
            ps = self._param_specs[name]
            if isinstance(editor, QCheckBox):
                values[name] = editor.isChecked()
            elif isinstance(editor, QSpinBox):
                values[name] = int(editor.value())
            elif isinstance(editor, QDoubleSpinBox):
                values[name] = float(editor.value())
            elif isinstance(editor, QComboBox):
                values[name] = editor.currentText()
            elif isinstance(editor, QLineEdit):
                values[name] = editor.text()
            else:
                values[name] = ps.default
        return values

    def _emit_params(self) -> None:
        if self._node is None:
            return
        params = self._collect_params()
        self._update_visibility(params)
        self.params_changed.emit(self._node.id, params)

    def _on_enabled_toggled(self, value: bool) -> None:
        if self._node is None:
            return
        self.enabled_changed.emit(self._node.id, value)

    def _update_visibility(self, current_params: dict[str, Any] | None = None) -> None:
        if current_params is None:
            current_params = self._collect_params()

        for name, ps in self._param_specs.items():
            label, editor = self._row_widgets[name]
            visible = True
            if ps.visible_if:
                for key, allowed_values in ps.visible_if.items():
                    if current_params.get(key) not in allowed_values:
                        visible = False
                        break
            label.setVisible(visible)
            editor.setVisible(visible)

    def _format_port_help(self, spec: BlockSpec) -> str:
        type_help = {
            "image": "BGR image matrix (numpy array).",
            "mask": "Single-channel binary/grayscale mask.",
            "detections": "List of detections with bbox/label/score.",
            "feature_vector": "Numeric feature vector (numpy array).",
            "meta": "Dictionary of metrics and metadata.",
        }
        parts: list[str] = []
        if spec.input_ports:
            parts.append("<b>Inputs:</b>")
            for p in spec.input_ports:
                desc = p.description or type_help.get(p.type, "")
                parts.append(f"&nbsp;&nbsp;• <code>{p.name}</code> (<code>{p.type}</code>) - {desc}")
        else:
            parts.append("<b>Inputs:</b> none")
        if spec.output_ports:
            parts.append("<b>Outputs:</b>")
            for p in spec.output_ports:
                desc = p.description or type_help.get(p.type, "")
                parts.append(f"&nbsp;&nbsp;• <code>{p.name}</code> (<code>{p.type}</code>) - {desc}")
        else:
            parts.append("<b>Outputs:</b> none")
        return "<br>".join(parts)
