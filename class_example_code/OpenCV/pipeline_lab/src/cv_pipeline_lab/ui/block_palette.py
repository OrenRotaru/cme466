from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import QByteArray, QMimeData, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem, QWidget

from cv_pipeline_lab.core.registry import BlockRegistry


class BlockTreeWidget(QTreeWidget):
    block_double_clicked = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setHeaderHidden(True)
        self.itemDoubleClicked.connect(self._on_double_clicked)

    def _on_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        block_type = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(block_type, str):
            self.block_double_clicked.emit(block_type)

    def startDrag(self, supportedActions):  # type: ignore[override]
        item = self.currentItem()
        if item is None:
            return
        block_type = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(block_type, str):
            return

        mime = QMimeData()
        mime.setData("application/x-cv-block-type", QByteArray(block_type.encode("utf-8")))

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class BlockPalette(QWidget):
    block_chosen = Signal(str)

    def __init__(self, registry: BlockRegistry) -> None:
        super().__init__()
        self.registry = registry

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        c_layout = QHBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search blocks...")
        self.tree = BlockTreeWidget()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        left = QWidget()
        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.search)

        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(self.tree)

        vertical = QWidget()
        from PySide6.QtWidgets import QVBoxLayout

        v = QVBoxLayout(vertical)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.search)
        v.addWidget(self.tree)

        layout.addWidget(vertical)

        self.search.textChanged.connect(self._apply_filter)
        self.tree.block_double_clicked.connect(self.block_chosen.emit)

        self._populate()

    def _populate(self) -> None:
        self.tree.clear()
        by_category: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        for spec in self.registry.all_specs():
            by_category[spec.category].append((spec.title, spec.type_name, spec.description))

        for category in sorted(by_category):
            cat_item = QTreeWidgetItem([category])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
            self.tree.addTopLevelItem(cat_item)
            for title, block_type, description in sorted(by_category[category], key=lambda x: x[0]):
                item = QTreeWidgetItem([title])
                item.setData(0, Qt.ItemDataRole.UserRole, block_type)
                if description:
                    item.setToolTip(0, description)
                cat_item.addChild(item)
            cat_item.setExpanded(True)

    def _apply_filter(self, text: str) -> None:
        text = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            visible_children = 0
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                label = child.text(0).lower()
                visible = not text or text in label
                child.setHidden(not visible)
                visible_children += int(visible)
            cat_item.setHidden(visible_children == 0)
