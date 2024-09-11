from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QApplication,
    QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import sys
import requests


class CompletionForm(QMainWindow):
    task_completed = pyqtSignal()
    add_time = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Task Completion")
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                padding: 10px 20px;
                min-width: 150px;
                max-width: 200px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
            QLabel {
                font-size: 24px;
                margin-bottom: 20px;
            }
            QLineEdit {
                background-color: #2D2D2D;
                border: 1px solid #3A3A3A;
                border-radius: 5px;
                padding: 10px;
                font-size: 18px;
                color: #FFFFFF;
                max-width: 200px;
            }
        """
        )

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setSpacing(20)

        self.question_label = QLabel("Are you done with your task?")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.question_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignCenter)
        self.yes_button = QPushButton("Yes")
        self.no_button = QPushButton("No")
        self.button_layout.addWidget(self.yes_button)
        self.button_layout.addWidget(self.no_button)
        self.main_layout.addLayout(self.button_layout)

        self.time_input_label = QLabel("How much more time do you need? (minutes)")
        self.time_input_label.setAlignment(Qt.AlignCenter)
        self.time_input = QLineEdit()
        self.time_input.setAlignment(Qt.AlignCenter)
        self.time_input.setFixedWidth(200)  # Set fixed width for input box
        self.submit_button = QPushButton("Submit")

        self.main_layout.addWidget(self.time_input_label)
        self.main_layout.addWidget(self.time_input, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.submit_button, alignment=Qt.AlignCenter)

        self.time_input_label.hide()
        self.time_input.hide()
        self.submit_button.hide()

        self.yes_button.clicked.connect(self.on_yes_clicked)
        self.no_button.clicked.connect(self.on_no_clicked)
        self.submit_button.clicked.connect(self.on_submit_clicked)

        self.showMaximized()

    def on_yes_clicked(self):
        self.task_completed.emit()
        self.close()

    def on_no_clicked(self):
        self.question_label.hide()
        self.yes_button.hide()
        self.no_button.hide()
        self.time_input_label.show()
        self.time_input.show()
        self.submit_button.show()

    def on_submit_clicked(self):
        try:
            additional_minutes = int(self.time_input.text())
            additional_seconds = additional_minutes * 60
            extension_length = (
                f"{additional_minutes // 60:02d}:{additional_minutes % 60:02d}:00"
            )

            # Make API request to extend the task
            response = self.extend_task(extension_length)

            if response.status_code == 200:
                self.add_time.emit(additional_seconds)
                self.close()
            else:
                QMessageBox.warning(
                    self, "Error", f"Failed to extend task: {response.text}"
                )
        except ValueError:
            self.time_input.setText("Please enter a valid number")
            self.time_input.setStyleSheet("border: 2px solid red;")

    def extend_task(self, extension_length):
        api_url = f"http://your-api-url/tasks/{self.task_id}/extend"  # Replace with your actual API URL
        payload = {"extension_length": extension_length}

        try:
            response = requests.post(api_url, json=payload)
            return response
        except requests.RequestException as e:
            print(f"Error making API request: {e}")
            return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = CompletionForm()
    ex.show()
    sys.exit(app.exec_())
