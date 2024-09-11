import sys
import subprocess
from PyQt5.QtWidgets import (
    QPushButton,
    QWidget,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QLineEdit,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor


def run_app(app_name):
    process = subprocess.run(
        [sys.executable, f"sub_apps/{app_name}/main.py"], capture_output=True, text=True
    )
    print(f"Run output from {app_name}:")
    print(f"stderr: {process.stderr}")
    print(f"stdout: {process.stdout}")


class TableLineEdit(QLineEdit):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            """
            QLineEdit {
                background-color: #282828;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 14px;
            }
        """
        )


class ActionButton(QPushButton):
    def __init__(self, text, action, parent=None):
        super().__init__(text, parent)
        self.action = action
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #1DB954;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 12px;
                font-size: 14px;
                min-width: 80px;
                max-width: 120px;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
        """
        )
        self.clicked.connect(self.action)


class StatusButton(QPushButton):
    status_changed = pyqtSignal(bool)

    def __init__(self, completed=False, parent=None):
        super().__init__(parent)
        self.completed = completed
        self.update_text()
        self.clicked.connect(self.toggle_status)

    def update_text(self):
        self.setText("Completed" if self.completed else "Not Completed")
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {'#1DB954' if self.completed else '#282828'};
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 12px;
                font-size: 14px;
                min-width: 120px;
                max-width: 150px;
            }}
            QPushButton:hover {{
                background-color: {'#1ED760' if self.completed else '#383838'};
            }}
        """
        )

    def toggle_status(self):
        self.completed = not self.completed
        self.update_text()
        self.status_changed.emit(self.completed)


class CenteredWidget(QWidget):
    def __init__(self, widget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.addWidget(widget, alignment=Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)


class FlexibleTable(QTableWidget):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels([col["name"] for col in columns])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet(
            """
            QTableWidget {
                background-color: #121212;
                border: none;
            }
            QHeaderView::section {
                background-color: #282828;
                padding: 10px;
                border: none;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #282828;
            }
        """
        )
        self.set_column_widths()

    def set_column_widths(self):
        total_width = self.viewport().width()
        width_units = sum(col.get("width", 1) for col in self.columns)
        for index, column in enumerate(self.columns):
            width = int((column.get("width", 1) / width_units) * total_width)
            self.setColumnWidth(index, width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_column_widths()

    def populate_table(self, data):
        self.setRowCount(len(data))
        for row, item in enumerate(data):
            for col, column in enumerate(self.columns):
                if column["type"] == "text":
                    cell_item = QTableWidgetItem(str(item.get(column["key"], "")))
                    cell_item.setTextAlignment(Qt.AlignCenter)
                    self.setItem(row, col, cell_item)
                elif column["type"] == "action":
                    button = ActionButton(
                        column["text"],
                        lambda checked, r=row, action=column["action"]: action(data[r]),
                    )
                    self.setCellWidget(row, col, CenteredWidget(button))
                elif column["type"] == "status":
                    status_button = StatusButton(item.get(column["key"], False))
                    status_button.status_changed.connect(
                        lambda completed, r=row, key=column["key"]: self.update_status(
                            r, key, completed
                        )
                    )
                    self.setCellWidget(row, col, CenteredWidget(status_button))
            self.setRowHeight(row, 50)


# Common styles
COMMON_STYLES = """
    QWidget {
        background-color: #121212;
        color: white;
        font-family: Arial, sans-serif;
    }
    QLabel {
        font-size: 14px;
    }
    QPushButton {
        background-color: #1DB954;
        color: white;
        border: none;
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
        min-width: 100px;
    }
    QPushButton:hover {
        background-color: #1ED760;
    }
"""
