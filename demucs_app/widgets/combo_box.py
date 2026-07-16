"""Consistent combo-box controls and popups across macOS Qt styles."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QComboBox, QListView, QStyledItemDelegate, QStyleOptionViewItem, QWidget


class ComboItemDelegate(QStyledItemDelegate):
    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        hint = super().sizeHint(option, index)
        hint.setHeight(34)
        return hint


class ModernComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(36)

        popup = QListView()
        popup.setObjectName("comboPopup")
        popup.setMouseTracking(True)
        popup.viewport().setMouseTracking(True)
        popup.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        popup.setUniformItemSizes(True)
        popup.setItemDelegate(ComboItemDelegate(popup))
        self.setView(popup)
