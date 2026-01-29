"""
Log model for displaying log entries in QML ListView.
"""

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt


class LogEntry:
    """Represents a single log entry."""

    def __init__(self, timestamp: str, message: str):
        self.timestamp = timestamp
        self.message = message


class LogModel(QAbstractListModel):
    """Model for displaying log entries in QML ListView."""

    TimestampRole = Qt.UserRole + 1
    MessageRole = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[LogEntry] = []

    def roleNames(self):
        return {
            self.TimestampRole: b"timestamp",
            self.MessageRole: b"message",
        }

    def rowCount(self, parent=QModelIndex()):
        return len(self._entries)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._entries):
            return None

        entry = self._entries[index.row()]
        if role == self.TimestampRole:
            return entry.timestamp
        elif role == self.MessageRole:
            return entry.message
        return None

    def add_entry(self, timestamp: str, message: str):
        """Add a new log entry to the model."""
        self.beginInsertRows(QModelIndex(), len(self._entries), len(self._entries))
        self._entries.append(LogEntry(timestamp, message))
        self.endInsertRows()

    def clear_entries(self):
        """Clear all log entries."""
        self.beginResetModel()
        self._entries.clear()
        self.endResetModel()
