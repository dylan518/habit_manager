import sys
import requests
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QApplication,
    QMainWindow,
    QTextEdit,
    QSplitter,
    QTabWidget,
    QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api"


class DeleteButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("×", parent)
        self.setStyleSheet(
            """
            DeleteButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            DeleteButton:hover {
                color: #E06C75;
            }
        """
        )
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(20, 20)
        self.hide()


class EntryItemWidget(QWidget):
    deleteClicked = pyqtSignal(QListWidgetItem)

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item = item
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        self.label = QLabel(item.text())
        self.deleteButton = DeleteButton(self)
        layout.addWidget(self.label)
        layout.addWidget(self.deleteButton)
        layout.setAlignment(self.deleteButton, Qt.AlignRight)
        self.deleteButton.clicked.connect(self.onDeleteClicked)

    def onDeleteClicked(self):
        self.deleteClicked.emit(self.item)

    def enterEvent(self, event):
        self.deleteButton.show()

    def leaveEvent(self, event):
        self.deleteButton.hide()


class EntryList(QWidget):
    entry_selected = pyqtSignal(dict)
    new_entry_requested = pyqtSignal()
    save_changes_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(2)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        self.new_button = QPushButton("New Entry")
        self.save_button = QPushButton("Complete")
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        self.new_button.clicked.connect(self.new_entry_requested.emit)
        self.save_button.clicked.connect(self.save_changes_requested.emit)

        self.setStyleSheet(
            """
            QWidget {
                background-color: #282c34;
                color: #ABB2BF;
                font-family: Arial;
                font-size: 14px;
            }
            QListWidget {
                background-color: #282c34;
                border: none;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #282c34;
                border-radius: None;
                padding: 5px;
                margin-bottom: 2px;
            }
            QListWidget::item:hover {
                background-color: #323842;
            }
            QListWidget::item:selected {
                background-color: #3A3F4B;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4CA0E0;
            }
        """
        )

        self.fetch_journals()

    def fetch_journals(self):
        try:
            response = requests.get(f"{API_BASE_URL}/journals")
            journals = response.json()
            self.list_widget.clear()
            for journal in journals:
                self.add_entry(journal)
        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch journals: {str(e)}")

    def add_entry(self, entry):
        item = QListWidgetItem(self.list_widget)
        self.list_widget.addItem(item)
        item_widget = EntryItemWidget(item)
        item_widget.label.setText(entry["date"])
        item.setData(Qt.UserRole, entry)
        item.setSizeHint(item_widget.sizeHint())
        self.list_widget.setItemWidget(item, item_widget)
        item_widget.deleteClicked.connect(self.remove_entry)

    def remove_entry(self, item):
        journal_id = item.data(Qt.UserRole)["id"]
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this journal entry?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                response = requests.delete(f"{API_BASE_URL}/journals/{journal_id}")
                if response.status_code == 200:
                    row = self.list_widget.row(item)
                    self.list_widget.takeItem(row)
                    QMessageBox.information(
                        self, "Success", "Journal entry deleted successfully."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Failed to delete journal entry. Server responded with status code {response.status_code}",
                    )
            except requests.RequestException as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An error occurred while trying to delete the journal entry: {str(e)}",
                )

    def on_item_clicked(self, item):
        entry = item.data(Qt.UserRole)
        self.entry_selected.emit(entry)


class JournalEditor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.sections = ["Reflections", "Planning", "Action Items", "Misc"]
        self.editors = {}

        for section in self.sections:
            editor = QTextEdit()
            editor.setStyleSheet(
                """
                QTextEdit {
                    background-color: #1E1E1E;
                    color: #D4D4D4;
                    border: none;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 14px;
                }
                """
            )
            self.tab_widget.addTab(editor, section)
            self.editors[section] = editor

        self.setStyleSheet(
            """
            QTabWidget::pane {
                border-top: 5px solid #252526;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #D4D4D4;
                border: 5px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                border-top: 4px solid #007ACC;
            }
            QTabBar::tab:hover:!selected {
                background-color: #2A2D2E;
            }
            """
        )

        self.current_journal_id = None

    def set_content(self, journal):
        self.current_journal_id = journal["id"]
        try:
            response = requests.get(
                f"{API_BASE_URL}/journals/{self.current_journal_id}"
            )
            if response.status_code == 200:
                journal_detail = response.json()
                for section in journal_detail["sections"]:
                    if section["header"] in self.editors:
                        self.editors[section["header"]].setPlainText(section["content"])
                    else:
                        print(f"no secftions for {journal_detail}")
            else:
                QMessageBox.warning(self, "Error", "Failed to fetch journal details.")
        except requests.RequestException as e:
            QMessageBox.critical(
                self, "Error", f"Failed to fetch journal details: {str(e)}"
            )

    def get_content(self):
        return [
            {"header": section, "content": self.editors[section].toPlainText()}
            for section in self.sections
        ]


class JournalApp(QMainWindow):
    journal_completed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dark-themed Journal App")
        self.setGeometry(100, 100, 800, 600)

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #282c34;
            }
        """
        )

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        self.entry_list = EntryList()
        self.journal_editor = JournalEditor()

        splitter.addWidget(self.entry_list)
        splitter.addWidget(self.journal_editor)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        self.entry_list.entry_selected.connect(self.display_entry)
        self.entry_list.new_entry_requested.connect(self.create_new_entry)
        self.entry_list.save_changes_requested.connect(self.save_changes)

    def display_entry(self, entry):
        self.journal_editor.set_content(entry)

    def create_new_entry(self):
        try:
            response = requests.post(f"{API_BASE_URL}/journals", json={"sections": []})
            if response.status_code == 200:
                new_journal = response.json()
                self.entry_list.fetch_journals()  # Refresh the list to include the new entry
                QMessageBox.information(
                    self, "Success", "New journal entry created successfully!"
                )
            else:
                QMessageBox.warning(
                    self, "Error", "Failed to create new journal entry."
                )
        except requests.RequestException as e:
            QMessageBox.critical(
                self, "Error", f"Failed to create new journal entry: {str(e)}"
            )

    def save_changes(self):

        sections = self.journal_editor.get_content()

        try:
            # Note: The provided API doesn't have an update endpoint, so we're using POST here.
            # In a real application, you'd want to implement a PUT or PATCH endpoint for updates.
            response = requests.post(
                f"{API_BASE_URL}/journals", json={"sections": sections}
            )
            if response.status_code == 200:
                QMessageBox.information(
                    self, "Success", "Journal entry updated successfully!"
                )
            else:
                QMessageBox.warning(self, "Error", "Faileƒd to update journal entry.")
        except requests.RequestException as e:
            QMessageBox.critical(
                self, "Error", f"Failed to update journal entry: {str(e)}"
            )
        self.journal_completed.emit()  # Emit the completion signal


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet(
        """
        QWidget {
            background-color: #1E1E1E;
            color: #ABB2BF;
        }
    """
    )

    main_window = JournalApp()
    main_window.show()
    sys.exit(app.exec_())
