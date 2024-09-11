import sys
import requests
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QScrollArea,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
import datetime
from datetime import timedelta
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api"


class Task:
    def __init__(
        self, id, title, description, time_remaining, time_created, completed_at=None
    ):
        self.id = id
        self.title = title
        self.description = description
        self.time_remaining = self.parse_time_string(time_remaining)
        self.time_created = datetime.fromisoformat(time_created)
        self.completed_at = (
            datetime.fromisoformat(completed_at) if completed_at else None
        )

    @staticmethod
    def parse_time_string(time_str):
        hours, minutes, seconds = map(int, time_str.split(":"))
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    def __str__(self):
        hours, remainder = divmod(self.time_remaining.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{self.title} - {hours}h {minutes}m"


class TaskItem(QWidget):
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.name_label = QLabel(self.task.title)
        self.name_label.setStyleSheet(
            """
            font-size: 14px;
            color: #D4D4D4;
            background-color: transparent;
            padding: 2px 0;
            line-height: 1.4;
            """
        )
        layout.addWidget(self.name_label)

        hours, remainder = divmod(self.task.time_remaining.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        time_str = f"{hours}h {minutes}m"
        self.time_label = QLabel(time_str)
        self.time_label.setStyleSheet(
            """
            font-size: 12px;
            color: #569CD6;
            background-color: transparent;
            padding: 2px 0;
            line-height: 1.4;
            """
        )
        layout.addWidget(self.time_label)

        layout.addStretch()

        self.remove_button = QPushButton("×")
        self.remove_button.setFixedSize(QSize(16, 16))
        self.remove_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.remove_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                color: #D4D4D4;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            """
        )
        self.remove_button.hide()
        layout.addWidget(self.remove_button)

        self.setStyleSheet("background-color: transparent;")

    def enterEvent(self, event):
        self.remove_button.show()

    def leaveEvent(self, event):
        self.remove_button.hide()


class TaskQueue(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.initUI()
        self.load_tasks()
        self.load_latest_notes()

    def initUI(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Input fields
        input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Task name")
        self.hours_input = QLineEdit()
        self.hours_input.setPlaceholderText("Hours")
        self.hours_input.setFixedWidth(60)
        self.minutes_input = QLineEdit()
        self.minutes_input.setPlaceholderText("Minutes")
        self.minutes_input.setFixedWidth(60)
        self.add_button = QPushButton("Add Task")
        self.add_button.clicked.connect(self.add_task)

        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.hours_input)
        input_layout.addWidget(self.minutes_input)
        input_layout.addWidget(self.add_button)

        # Task list
        self.task_list = QListWidget()
        self.task_list.setDragDropMode(QListWidget.InternalMove)
        self.task_list.setStyleSheet(
            """
            QListWidget {
                background-color: #252526;
                border: 1px solid #3C3C3C;
            }
            QListWidget::item {
                background-color: #1E1E1E;
                border-radius: 0px;
                margin-bottom: 0px;
                padding: 0px 0;
            }
            QListWidget::item:selected {
                background-color: #2D2D2D;
            }
            QListWidget::item:hover {
                background-color: #2A2A2A;
            }
        """
        )

        # Wrap the task list in a QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.task_list)

        # Total time and Get to Work button
        total_layout = QHBoxLayout()
        self.total_time_label = QLabel("Total time: 0 hours 0 minutes")
        self.total_time_label.setObjectName("totalTimeLabel")

        self.get_to_work_button = QPushButton("Get to Work")
        self.get_to_work_button.setStyleSheet(
            """
            QPushButton {
                background-color: #800080;  /* Purple background */
                color: #FFFFFF;  /* White text */
                border: none;
                padding: 6px 12px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #993399;  /* Lighter purple when hovered */
            }
            QPushButton:pressed {
                background-color: #660066;  /* Darker purple when pressed */
            }
            """
        )
        # Add the total time label and button to the layout
        total_layout.addWidget(self.total_time_label)
        total_layout.addWidget(self.get_to_work_button)

        left_layout.addLayout(input_layout)
        left_layout.addWidget(scroll_area)
        left_layout.addLayout(total_layout)

        # Latest Reminder and Todo
        self.latest_reminder_label = QLabel("Reminder:")
        self.latest_reminder_text = QTextEdit()

        self.latest_todo_label = QLabel("Goals:")
        self.latest_todo_text = QTextEdit()

        right_layout.addWidget(self.latest_reminder_label)
        right_layout.addWidget(self.latest_reminder_text)
        right_layout.addWidget(self.latest_todo_label)
        right_layout.addWidget(self.latest_todo_text)

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)
        self.setWindowTitle("Task Queue")
        self.setGeometry(300, 300, 800, 500)

        # Connect the close event to save_notes method
        self.closeEvent = self.save_notes

        self.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-size: 14px;
            }
            QScrollArea {
                background-color: #252526;
                border: 1px solid #3C3C3C;
            }
            QLabel {
                color: #D4D4D4;
            }
            QLineEdit, QTextEdit {
                background-color: #3C3C3C;
                border: 1px solid #555555;
                border-radius: 2px;
                padding: 4px;
                color: #D4D4D4;
            }
            QPushButton {
                background-color: #0E639C;
                color: #FFFFFF;
                border: none;
                padding: 6px 12px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #0D5689;
            }
            #totalTimeLabel {
                color: #D4D4D4;
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
            }
            QScrollBar:vertical {
                background: #1E1E1E;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """
        )

        # Connect the model's row moved signal to update task order
        self.task_list.model().rowsMoved.connect(self.update_task_order)

    def load_latest_notes(self):
        try:
            response = requests.get(f"{API_BASE_URL}/latest")
            response.raise_for_status()
            data = response.json()
            print(data)

            if data.get("latest_reminder"):
                self.latest_reminder_text.setText(data["latest_reminder"]["content"])
            else:
                self.latest_reminder_text.setText("Add reminders here.")

            if data.get("latest_goal"):
                goal = data["latest_goal"]
                self.latest_todo_text.setText(goal["content"])

            else:
                self.latest_todo_text.setText("Add your goals here.")
        except requests.RequestException as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load latest notes: {str(e)}"
            )

    def save_notes(self, event):
        reminder_content = self.latest_reminder_text.toPlainText()
        todo_content = self.latest_todo_text.toPlainText()
        print(reminder_content)
        try:
            # Update reminder
            if reminder_content:
                reminder_response = requests.post(
                    f"{API_BASE_URL}/reminders", json={"content": reminder_content}
                )
                reminder_response.raise_for_status()

            # Update goal
            if todo_content:
                goal_response = requests.post(
                    f"{API_BASE_URL}/goals",
                    json={"content": todo_content},
                )
                goal_response.raise_for_status()

            # If both updates are successful, accept the close event
            QMessageBox.information(self, "Success", "Notes saved successfully!")
            event.accept()
        except requests.RequestException as e:
            # If there's an error, show a message and ignore the close event
            QMessageBox.critical(self, "Error", f"Failed to save notes: {str(e)}")
            event.ignore()

        event.accept()

    def load_tasks(self):
        try:
            response = requests.get(f"{API_BASE_URL}/tasks/incomplete")
            response.raise_for_status()
            tasks_data = response.json()
            self.tasks = [
                Task(
                    t["id"],
                    t["title"],
                    t["description"],
                    t["time_remaining"],
                    t["time_created"],
                    t.get("completed_at"),
                )
                for t in tasks_data
            ]
            self.update_task_list()
            self.update_total_time()
        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to load tasks: {str(e)}")

    def add_task(self):
        title = self.task_input.text()
        try:
            hours = int(self.hours_input.text() or 0)
            minutes = int(self.minutes_input.text() or 0)
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter valid numbers for hours and minutes.",
            )
            return

        if title and (hours > 0 or minutes > 0):
            original_length = f"{hours:02d}:{minutes:02d}:00"
            try:
                response = requests.post(
                    f"{API_BASE_URL}/tasks",
                    json={
                        "title": title,
                        "description": f"Task duration: {hours} hours and {minutes} minutes",
                        "original_length": original_length,
                    },
                )
                response.raise_for_status()
                new_task = response.json()
                self.tasks.append(
                    Task(
                        new_task["id"],
                        new_task["title"],
                        new_task["description"],
                        new_task["time_remaining"],
                        new_task["time_created"],
                        new_task.get("completed_at"),
                    )
                )
                self.update_task_list()
                self.update_total_time()

                self.task_input.clear()
                self.hours_input.clear()
                self.minutes_input.clear()
            except requests.RequestException as e:
                QMessageBox.critical(self, "Error", f"Failed to add task: {str(e)}")

    def remove_task(self, list_item):
        row = self.task_list.row(list_item)
        task = self.tasks[row]
        try:
            response = requests.delete(f"{API_BASE_URL}/tasks/{task.id}")
            response.raise_for_status()
            self.tasks.pop(row)
            self.task_list.takeItem(row)
            self.update_total_time()
            self.update_task_order()
        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to remove task: {str(e)}")

    def update_task_order(self):
        new_order = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            task_item = self.task_list.itemWidget(item)
            new_order.append(task_item.task.id)

        try:
            response = requests.put(
                f"{API_BASE_URL}/tasks/reorder", json={"task_ids": new_order}
            )
            response.raise_for_status()
        except requests.RequestException as e:
            QMessageBox.critical(
                self, "Error", f"Failed to update task order: {str(e)}"
            )

    def update_task_list(self):
        self.task_list.clear()
        for task in self.tasks:
            item_widget = TaskItem(task)
            list_item = QListWidgetItem(self.task_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.task_list.addItem(list_item)
            self.task_list.setItemWidget(list_item, item_widget)
            item_widget.remove_button.clicked.connect(
                lambda: self.remove_task(list_item)
            )

    def update_total_time(self):
        total_seconds = sum(task.time_remaining.total_seconds() for task in self.tasks)
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, _ = divmod(remainder, 60)
        self.total_time_label.setText(f"Total time: {hours} hours {minutes} minutes")

    def dropEvent(self, event):
        super().dropEvent(event)
        self.update_task_order()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TaskQueue()
    ex.show()
    sys.exit(app.exec_())
