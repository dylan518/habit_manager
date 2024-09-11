import sys
import requests
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor
from PyQt5.QtCore import (
    Qt,
    QTimer,
    QRectF,
    QPropertyAnimation,
    QEasingCurve,
    pyqtProperty,
    pyqtSignal,
)
from datetime import timedelta

API_BASE_URL = "http://localhost:8000/api"


class CircularProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.setFixedSize(300, 300)

    def setValue(self, value):
        self.animation.setStartValue(self._value)
        self.animation.setEndValue(value)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        painter.translate(rect.center())
        painter.scale(rect.width() / 200.0, rect.height() / 200.0)

        # Draw background circle
        painter.setPen(QPen(QColor("#3A3A3A"), 10))
        painter.drawEllipse(QRectF(-95, -95, 190, 190))

        # Draw progress arc
        painter.setPen(QPen(QColor("#4A90E2"), 10))
        span_angle = int(-self._value * 360 * 16)
        painter.drawArc(QRectF(-95, -95, 190, 190), 90 * 16, span_angle)

    def get_value(self):
        return self._value

    def set_value(self, value):
        if self._value != value:
            self._value = value
            self.update()

    value = pyqtProperty(float, get_value, set_value)


class CircularTimer(QWidget):
    timerComplete = pyqtSignal()
    taskFetchError = pyqtSignal(str)
    changeActivityRequested = pyqtSignal()

    def __init__(self, lock_in_mode=False):
        super().__init__()
        self.lock_in_mode = lock_in_mode
        self.task = None
        self.is_paused = True
        self.init_ui()
        self.fetch_task()

    def init_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 14px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5AA0F2;
            }
            QLabel {
                color: #FFFFFF;
            }
            """
        )

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)

        self.task_label = QLabel("Loading...")
        self.task_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        title_layout.addWidget(self.task_label)

        if not self.lock_in_mode:
            self.change_activity_link = QLabel("Change Activity")
            self.change_activity_link.setStyleSheet(
                "font-size: 14px; color: #4A90E2; text-decoration: underline; margin-left: 10px;"
            )
            self.change_activity_link.setCursor(QCursor(Qt.PointingHandCursor))
            self.change_activity_link.mousePressEvent = self.redirect_to_work_queue
            title_layout.addWidget(self.change_activity_link)

        main_layout.addLayout(title_layout)

        self.progress_bar = CircularProgressBar()
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 48px; font-weight: bold;")
        progress_layout.addWidget(self.time_label)

        main_layout.addLayout(progress_layout)

        self.pause_button = QPushButton("Start")
        self.pause_button.clicked.connect(self.toggle_pause)
        main_layout.addWidget(self.pause_button, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)

        self.setMinimumSize(350, 450)
        self.setWindowTitle("Work Mode Timer")

    def fetch_task(self):
        try:
            response = requests.get(f"{API_BASE_URL}/tasks/incomplete")
            response.raise_for_status()
            tasks = response.json()
            if tasks:
                self.task = min(tasks, key=lambda x: x["id"])
                self.task_label.setText(self.task["title"])

                time_remaining = self.parse_time(self.task["time_remaining"])
                self.time_label.setText(self.format_time(time_remaining))

                # Calculate total time including extensions
                original_length = self.parse_time(self.task["original_length"])
                extension_time = sum(
                    (
                        self.parse_time(ext["extension_length"])
                        for ext in self.task["extensions"]
                    ),
                    timedelta(),
                )
                total_time = original_length + extension_time

                # Set initial progress
                progress = 1 - (
                    time_remaining.total_seconds() / total_time.total_seconds()
                )
                self.progress_bar.setValue(progress)

                self.pause_button.setEnabled(True)
            else:
                self.taskFetchError.emit("No tasks available")
                self.task_label.setText("No tasks available")
                self.pause_button.setEnabled(False)
        except requests.RequestException as e:
            self.taskFetchError.emit(str(e))
            self.task_label.setText("Error fetching task")
            self.pause_button.setEnabled(False)

    def update_time(self):
        if self.task and not self.is_paused:
            try:
                response = requests.put(
                    f"{API_BASE_URL}/tasks/{self.task['id']}/decrement-time"
                )
                response.raise_for_status()
                updated_task = response.json()
                print(updated_task)  # For debugging

                time_remaining = timedelta(seconds=updated_task["time_remaining"])
                self.time_label.setText(self.format_time(time_remaining))

                total_time = timedelta(seconds=updated_task["total_time"])
                progress = 1 - (
                    time_remaining.total_seconds() / total_time.total_seconds()
                )
                self.progress_bar.setValue(progress)

                if time_remaining == timedelta(seconds=0):
                    self.timer.stop()
                    self.pause_button.setText("Restart")
                    self.complete_task()
                    self.timerComplete.emit()

                # Update the task information
                self.task = updated_task

            except requests.RequestException as e:
                print(f"Error decrementing task time: {e}")
                self.timer.stop()
                self.pause_button.setText("Resume")
                self.is_paused = True

    def toggle_pause(self):
        if self.is_paused:
            if not self.task:
                self.fetch_task()
            if self.task:
                self.timer.start(1000)
                self.pause_button.setText("Pause")
                self.is_paused = False
        else:
            self.timer.stop()
            self.pause_button.setText("Resume")
            self.is_paused = True

    def complete_task(self):
        if self.task:
            try:
                response = requests.put(
                    f"{API_BASE_URL}/tasks/{self.task['id']}/complete"
                )
                response.raise_for_status()
                print(f"Task {self.task['id']} completed successfully.")
                self.fetch_task()
            except requests.RequestException as e:
                print(f"Error completing task: {e}")

    def redirect_to_work_queue(self, event):
        self.changeActivityRequested.emit()

    @staticmethod
    def parse_time(time_str):
        parts = time_str.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return timedelta(minutes=minutes, seconds=seconds)
        else:
            raise ValueError(f"Invalid time format: {time_str}")

    @staticmethod
    def format_time(td):
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    app = QApplication(sys.argv)

    def on_timer_complete():
        print("Timer completed!")

    def on_task_fetch_error(error):
        print(f"Error fetching task: {error}")

    # Create a timer in normal mode (with change activity link)
    timer_normal = CircularTimer(lock_in_mode=False)
    timer_normal.timerComplete.connect(on_timer_complete)
    timer_normal.taskFetchError.connect(on_task_fetch_error)
    timer_normal.show()

    # Create a timer in lock-in mode (without change activity link)
    timer_lock_in = CircularTimer(lock_in_mode=True)
    timer_lock_in.timerComplete.connect(on_timer_complete)
    timer_lock_in.taskFetchError.connect(on_task_fetch_error)
    timer_lock_in.show()

    sys.exit(app.exec_())
