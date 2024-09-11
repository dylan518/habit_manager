import sys
import logging
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QLabel,
    QTimeEdit,
    QMessageBox,
    QScrollArea,
    QColorDialog,
    QFrame,
)
from PyQt5.QtCore import (
    Qt,
    QDate,
    QTime,
    QRect,
    pyqtSignal,
    QPropertyAnimation,
    QEasingCurve,
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
import requests

API_BASE_URL = "http://localhost:8000/api"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DayView(QWidget):
    activityClicked = pyqtSignal(dict)
    activityCreated = pyqtSignal(str, str)
    activityMoved = pyqtSignal(dict, str, str)
    activityDragging = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dayView")
        self.setMinimumSize(300, 1440)  # 1 pixel per minute
        self.activities = []
        self.drag_start = None
        self.drag_end = None
        self.dragged_activity = None
        self.selected_activity = None
        self.hover_activity = None
        self.new_activity_selection = None
        self.setMouseTracking(True)  # Enable mouse tracking for hover effects
        self.event_color = QColor("#116711")  # Green for event mode
        self.work_color = QColor("#007AFF")  # Blue for work mode
        self.current_mode = "event"  # Default mode

    def draw_activity(self, painter, activity, is_selected=False, is_hovered=False):
        start_time = QTime.fromString(activity["start_time"], "HH:mm:ss")
        end_time = QTime.fromString(activity["end_time"], "HH:mm:ss")

        # Ensure minimum duration of 15 minutes
        if start_time == end_time:
            end_time = end_time.addSecs(900)

        start_y = (start_time.hour() * 60 + start_time.minute()) * self.height() / 1440
        end_y = (end_time.hour() * 60 + end_time.minute()) * self.height() / 1440

        height = max(end_y - start_y, 20)  # Minimum height of 20 pixels

        rect = QRect(50, int(start_y), self.width() - 60, int(height))

        # Use the activity's mode to determine color
        if activity["mode"] == "work":
            base_color = self.work_color
        else:
            base_color = self.event_color

        if is_selected:
            color = base_color.lighter(120)
        elif is_hovered:
            color = base_color.lighter(110)
        else:
            color = base_color

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 2))
        painter.drawRoundedRect(rect, 5, 5)

        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Arial", 14))
        text_rect = rect.adjusted(5, 5, -5, -5)

        text = f"{activity['title']}\n{start_time.toString('HH:mm')} - {end_time.toString('HH:mm')}"
        elided_text = painter.fontMetrics().elidedText(
            text, Qt.ElideRight, text_rect.width()
        )

        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_text)

    def pos_to_time(self, y):
        minutes = int(y * 1440 / self.height())
        hours, minutes = divmod(minutes, 60)
        minutes = (minutes // 15) * 15  # Round to nearest 15 minutes
        return QTime(hours, minutes)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.draw_time_slots(painter)

        sorted_activities = sorted(
            self.activities, key=lambda x: QTime.fromString(x["start_time"], "HH:mm:ss")
        )

        for activity in sorted_activities:
            is_selected = activity == self.selected_activity
            is_hovered = activity == self.hover_activity
            self.draw_activity(painter, activity, is_selected, is_hovered)

        if self.new_activity_selection:
            self.draw_new_activity_selection(painter)

    def add_activity(self, activity):
        start_time = QTime.fromString(activity["start_time"], "HH:mm:ss")
        end_time = QTime.fromString(activity["end_time"], "HH:mm:ss")

        # Ensure minimum duration of 15 minutes
        if start_time == end_time:
            end_time = end_time.addSecs(900)

        activity["start_time"] = start_time.toString("HH:mm:ss")
        activity["end_time"] = end_time.toString("HH:mm:ss")

        self.activities.append(activity)
        self.update()

    def clear_activities(self):
        self.activities.clear()
        self.update()

    def draw_time_slots(self, painter):
        for hour in range(24):
            y = int(hour * 60 * self.height() / 1440)
            painter.setPen(QPen(QColor("#404040")))
            painter.drawLine(0, y, self.width(), y)
            painter.setPen(QColor("#b3b3b3"))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(5, y + 15, f"{hour:02d}:00")

    def draw_new_activity_selection(self, painter):
        if self.new_activity_selection:
            start_time = QTime.fromString(
                self.new_activity_selection["start_time"], "HH:mm:ss"
            )
            end_time = QTime.fromString(
                self.new_activity_selection["end_time"], "HH:mm:ss"
            )

            start_y = (
                (start_time.hour() * 60 + start_time.minute()) * self.height() / 1440
            )
            end_y = (end_time.hour() * 60 + end_time.minute()) * self.height() / 1440

            rect = QRect(50, int(start_y), self.width() - 60, int(end_y - start_y))

            # Use the current mode to determine both fill and outline colors
            color = self.work_color if self.current_mode == "work" else self.event_color

            # Create a semi-transparent version of the color for the fill
            fill_color = QColor(color)
            fill_color.setAlpha(128)  # Set alpha to 128 for 50% transparency

            painter.setBrush(QBrush(fill_color))
            painter.setPen(QPen(color, 2, Qt.DashLine))
            painter.drawRoundedRect(rect, 5, 5)

    def set_mode(self, mode):
        self.current_mode = mode
        self.update()

    def mousePressEvent(self, event):
        self.drag_start = event.pos()
        self.drag_end = None
        clicked_activity = self.get_activity_at_pos(event.pos())
        if clicked_activity:
            self.selected_activity = clicked_activity
            self.activityClicked.emit(clicked_activity)
        else:
            self.selected_activity = None
        self.dragged_activity = clicked_activity
        self.new_activity_selection = None
        self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:  # Dragging
            self.drag_end = event.pos()
            if self.dragged_activity:
                self.update_activity_times()
                self.activityDragging.emit(
                    self.dragged_activity["start_time"],
                    self.dragged_activity["end_time"],
                )
            else:
                self.update_new_activity_selection()
                if self.new_activity_selection:
                    self.activityDragging.emit(
                        self.new_activity_selection["start_time"],
                        self.new_activity_selection["end_time"],
                    )
        else:  # Hovering
            self.hover_activity = self.get_activity_at_pos(event.pos())
        self.update()

    def mouseReleaseEvent(self, event):
        if self.drag_start and self.drag_end:
            if self.dragged_activity:
                self.activityMoved.emit(
                    self.dragged_activity,
                    self.dragged_activity["start_time"],
                    self.dragged_activity["end_time"],
                )
            elif self.new_activity_selection:
                self.activityCreated.emit(
                    self.new_activity_selection["start_time"],
                    self.new_activity_selection["end_time"],
                )
        elif self.drag_start == event.pos():
            clicked_activity = self.get_activity_at_pos(event.pos())
            if clicked_activity:
                self.selected_activity = clicked_activity
                self.activityClicked.emit(clicked_activity)

        self.drag_start = None
        self.drag_end = None
        self.dragged_activity = None
        self.update()

    def get_activity_at_pos(self, pos):
        for activity in self.activities:
            start_time = QTime.fromString(activity["start_time"], "HH:mm:ss")
            end_time = QTime.fromString(activity["end_time"], "HH:mm:ss")

            start_y = (
                (start_time.hour() * 60 + start_time.minute()) * self.height() / 1440
            )
            end_y = (end_time.hour() * 60 + end_time.minute()) * self.height() / 1440

            rect = QRect(50, int(start_y), self.width() - 60, int(end_y - start_y))

            if rect.contains(pos):
                return activity

        return None

    def update_new_activity_selection(self):
        if self.drag_start and self.drag_end:
            start_y = min(self.drag_start.y(), self.drag_end.y())
            end_y = max(self.drag_start.y(), self.drag_end.y())

            start_time = self.pos_to_time(start_y)
            end_time = self.pos_to_time(end_y)

            # Ensure minimum duration of 15 minutes
            if start_time == end_time:
                end_time = end_time.addSecs(900)

            self.new_activity_selection = {
                "start_time": start_time.toString("HH:mm:00"),
                "end_time": end_time.toString("HH:mm:00"),
            }

    def update_activity_times(self):
        if self.drag_start and self.drag_end and self.dragged_activity:
            delta_y = self.drag_end.y() - self.drag_start.y()
            minutes_delta = int(delta_y * 1440 / self.height() / 15) * 15

            start_time = QTime.fromString(
                self.dragged_activity["start_time"], "HH:mm:ss"
            ).addSecs(minutes_delta * 60)
            end_time = QTime.fromString(
                self.dragged_activity["end_time"], "HH:mm:ss"
            ).addSecs(minutes_delta * 60)

            # Ensure the activity stays within the day
            if start_time < QTime(0, 0):
                diff = QTime(0, 0).secsTo(start_time)
                start_time = QTime(0, 0)
                end_time = end_time.addSecs(-diff)
            elif end_time > QTime(23, 59, 59):
                diff = end_time.secsTo(QTime(23, 59, 59))
                end_time = QTime(23, 59, 59)
                start_time = start_time.addSecs(diff)

            self.dragged_activity["start_time"] = start_time.toString("HH:mm:ss")
            self.dragged_activity["end_time"] = end_time.toString("HH:mm:ss")

    def clear_new_activity_selection(self):
        self.new_activity_selection = None
        self.update()


class ToggleSwitch(QWidget):
    switched = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self.mode = "work"
        self.is_checked = False
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setEasingCurve(QEasingCurve.InOutExpo)
        self.animation.setDuration(300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        if self.is_checked:
            background_color = QColor("#007AFF")  # Blue when checked (Work mode)
        else:
            background_color = QColor("#116711")  # Green when unchecked (Event mode)

        painter.setBrush(QBrush(background_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)

        # Draw knob
        knob_position = 30 if self.is_checked else 0
        painter.setBrush(QBrush(Qt.white))
        painter.drawEllipse(knob_position, 0, 30, 30)

    def mousePressEvent(self, event):
        self.toggle()

    def toggle(self):
        self.is_checked = not self.is_checked
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.pos())
        self.animation.start()
        self.update()
        self.switched.emit(self.is_checked)


class TimeBlockingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set up the main window properties
        self.setWindowTitle("Daily Time Blocking")
        self.setGeometry(100, 100, 1200, 700)  # Position and size of the window

        # Initialize important attributes
        self.current_date = QDate.currentDate()
        self.mode = "event"  # Default mode (can be "event" or "work")
        self.event_color = QColor("#116711")  # Green for event mode
        self.work_color = QColor("#007AFF")  # Blue for work mode

        # Apply dark theme to the entire application
        self.set_dark_theme()

        # Create the central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Set up the user interface
        self.setup_ui()

        # Load additional stylesheet (if any)
        self.load_stylesheet()

        # Load existing activities
        self.load_activities()

        # Initialize attendees input field (will be set up later)
        self.attendees_input = None

    def set_dark_theme(self):
        # Define and apply the dark theme stylesheet
        dark_theme = """
            QMainWindow, QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QLineEdit, QTextEdit, QTimeEdit {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                padding: 5px;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #0D0D0D;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2D2D2D;
            }
            QScrollArea {
                border: none;
            }
            QLabel {
                color: #B3B3B3;
            }
        """
        self.setStyleSheet(dark_theme)

    def setup_ui(self):
        # Set up the left side of the UI (Day View)
        left_widget = self.setup_left_panel()

        # Set up the right side of the UI (Controls and Activity Details)
        right_widget = self.setup_right_panel()

        # Add both panels to the main layout
        self.main_layout.addWidget(left_widget, 2)  # Left panel takes 2/3 of the space
        self.main_layout.addWidget(
            right_widget, 1
        )  # Right panel takes 1/3 of the space

    def setup_left_panel(self):
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Add date label
        self.date_label = QLabel(self.current_date.toString("dddd, MMMM d, yyyy"))
        self.date_label.setObjectName("dateLabel")
        left_layout.addWidget(self.date_label)

        # Create and set up the day view
        self.day_view = DayView()
        self.day_view.activityCreated.connect(self.on_activity_created)
        self.day_view.activityClicked.connect(self.on_activity_clicked)
        self.day_view.activityMoved.connect(self.on_activity_moved)
        self.day_view.activityDragging.connect(self.on_activity_dragging)

        # Add day view to a scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.day_view)
        left_layout.addWidget(self.scroll_area)

        return left_widget

    def setup_right_panel(self):
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)

        # Add mode selection switch
        self.add_mode_switch()

        # Add separator line
        self.add_separator()

        # Create a widget for dynamic content (activity details)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.right_layout.addWidget(self.details_widget)

        # Add stretch to push content to the top
        self.right_layout.addStretch()

        # Set up the details panel
        self.setup_details_panel()

        return right_widget

    def add_mode_switch(self):
        mode_layout = QHBoxLayout()
        mode_layout.addStretch()
        mode_layout.addWidget(QLabel("Event Mode"))
        self.mode_switch = ToggleSwitch()
        self.mode_switch.switched.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_switch)
        mode_layout.addWidget(QLabel("Work Mode"))
        mode_layout.addStretch()
        self.right_layout.addLayout(mode_layout)

    def add_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.right_layout.addWidget(separator)

    def setup_details_panel(self):
        # Clear existing widgets in the details layout
        for i in reversed(range(self.details_layout.count())):
            item = self.details_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                # Clear items from nested layouts
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)

        # Create and set up buttons
        self.create_action_buttons()

        # Create a horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.complete_button)

        # Add button layout to the top of the details layout
        self.details_layout.addLayout(button_layout)

        # Create and set up input fields
        self.create_input_fields()

        # Add input fields to the layout
        self.add_input_fields_to_layout()

        # Add stretch to push everything to the top
        self.details_layout.addStretch()

        # Set button colors and styles
        self.set_button_styles()

    def on_mode_changed(self, is_checked):
        self.mode = "work" if is_checked else "event"
        self.setup_details_panel()
        self.day_view.set_mode(self.mode)
        self.update()  # Force a repaint of the window

    def create_action_buttons(self):
        self.add_button = QPushButton(
            "Block Work" if self.mode == "work" else "Add Activity"
        )
        self.add_button.clicked.connect(self.add_activity)

        self.delete_button = QPushButton("Delete Activity")
        self.delete_button.clicked.connect(self.delete_activity)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_new_activity)

        self.complete_button = QPushButton("Complete Activity")
        self.complete_button.clicked.connect(self.complete_activity)

    def create_input_fields(self):
        self.activity_input = QLineEdit()
        if self.mode == "work":
            self.activity_input.setText("Work")
        else:
            self.activity_input.setPlaceholderText("Activity name")

        self.start_time = QTimeEdit()
        self.end_time = QTimeEdit()

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description")

        if self.mode == "event":
            self.attendees_input = QLineEdit()
            self.attendees_input.setPlaceholderText(
                "Attendees (comma-separated emails)"
            )

    def add_input_fields_to_layout(self):
        self.details_layout.addWidget(QLabel("Activity:"))
        self.details_layout.addWidget(self.activity_input)
        self.details_layout.addWidget(QLabel("Start Time:"))
        self.details_layout.addWidget(self.start_time)
        self.details_layout.addWidget(QLabel("End Time:"))
        self.details_layout.addWidget(self.end_time)

        if self.mode == "event":
            self.details_layout.addWidget(QLabel("Description:"))
            self.details_layout.addWidget(self.description_input)
            self.details_layout.addWidget(QLabel("Attendees:"))
            self.details_layout.addWidget(self.attendees_input)

    def set_button_styles(self):
        button_style = """
            QPushButton {
                background-color: %s;
                color: white;
                border: none;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: %s;
            }
        """

        add_color = self.work_color if self.mode == "work" else self.event_color
        self.add_button.setStyleSheet(
            button_style % (add_color.name(), add_color.lighter().name())
        )

        delete_color = QColor("#FF3B30")  # Red color for delete button
        self.delete_button.setStyleSheet(
            button_style % (delete_color.name(), delete_color.lighter().name())
        )

        cancel_color = QColor("#FF9500")  # Orange color for cancel button
        self.cancel_button.setStyleSheet(
            button_style % (cancel_color.name(), cancel_color.lighter().name())
        )

        complete_color = QColor("#AF52DE")  # Purple color for complete button
        self.complete_button.setStyleSheet(
            button_style % (complete_color.name(), complete_color.lighter().name())
        )

    def complete_activity(self):
        print("complete")
        pass

    def clear_inputs(self):
        self.activity_input.clear()
        self.start_time.setTime(QTime(0, 0))
        self.end_time.setTime(QTime(0, 0))
        self.description_input.clear()
        if self.attendees_input:
            self.attendees_input.clear()
        self.day_view.selected_activity = None
        self.day_view.clear_new_activity_selection()
        self.day_view.update()

    def on_activity_clicked(self, activity):
        logger.debug(f"Activity clicked: {activity}")
        self.activity_input.setText(activity["title"])
        self.start_time.setTime(QTime.fromString(activity["start_time"], "HH:mm:ss"))
        self.end_time.setTime(QTime.fromString(activity["end_time"], "HH:mm:ss"))
        self.description_input.setPlainText(activity.get("description", ""))
        if self.mode == "event" and self.attendees_input:
            self.attendees_input.setText(", ".join(activity.get("attendees", [])))
        self.day_view.selected_activity = activity
        self.day_view.update()

    def load_stylesheet(self):
        try:
            with open("front_end/components/stylesheet.css", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            logger.warning("CSS file not found. Using default styles.")

    def load_activities(self):
        self.day_view.clear_activities()
        try:
            response = requests.get(f"{API_BASE_URL}/dayplans")
            response.raise_for_status()
            activities = response.json()
            logger.debug(f"Loaded activities: {activities}")
            for activity in activities:
                formatted_activity = {
                    "id": activity["id"],
                    "title": activity["title"],
                    "start_time": activity["start_time"],
                    "end_time": activity["end_time"],
                    "description": activity.get("description", ""),
                    "mode": activity.get("mode", "event"),
                    "status": activity.get("status", "pending"),
                }
                self.day_view.add_activity(formatted_activity)
            logger.info(f"Added {len(self.day_view.activities)} activities to DayView")
            self.day_view.update()
            self.scroll_area.updateGeometry()
            self.update()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to load activities: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load activities: {str(e)}")

    def on_activity_created(self, start_time, end_time):
        self.start_time.setTime(QTime.fromString(start_time, "HH:mm"))
        self.end_time.setTime(QTime.fromString(end_time, "HH:mm"))
        self.activity_input.setFocus()

    def on_activity_moved(self, activity, new_start_time, new_end_time):
        updated_activity = {
            "title": activity["title"],
            "start_time": new_start_time,
            "end_time": new_end_time,
            "description": activity.get("description", ""),
            "mode": activity["mode"],
            "status": activity.get("status", "pending"),
        }
        try:
            response = requests.put(
                f"{API_BASE_URL}/dayplans/{activity['id']}", json=updated_activity
            )
            response.raise_for_status()
            self.load_activities()
            self.on_activity_clicked(response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update activity: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to update activity: {str(e)}")

    def add_activity(self):
        activity_name = self.activity_input.text()
        if activity_name:
            new_activity = {
                "title": activity_name,
                "start_time": self.start_time.time().toString("HH:mm:ss"),
                "end_time": self.end_time.time().toString("HH:mm:ss"),
                "description": (
                    self.description_input.toPlainText() if self.mode == "event" else ""
                ),
                "mode": self.mode,  # Use self.mode instead of self.mode_switch.mode
                "status": "pending",
            }
            print(f"adding activity {new_activity}")
            try:
                response = requests.post(f"{API_BASE_URL}/dayplans", json=new_activity)
                response.raise_for_status()
                self.clear_inputs()
                self.day_view.clear_new_activity_selection()
                self.load_activities()
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to add activity: {str(e)}")
                QMessageBox.warning(self, "Error", f"Failed to add activity: {str(e)}")

    def delete_activity(self):
        if self.day_view.selected_activity:
            confirm = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete '{self.day_view.selected_activity['title']}'?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                try:
                    response = requests.delete(
                        f"{API_BASE_URL}/dayplans/{self.day_view.selected_activity['id']}"
                    )
                    response.raise_for_status()
                    self.load_activities()
                    self.clear_inputs()
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to delete activity: {str(e)}")
                    QMessageBox.warning(
                        self, "Error", f"Failed to delete activity: {str(e)}"
                    )

    def cancel_new_activity(self):
        self.clear_inputs()
        self.day_view.clear_new_activity_selection()

    def on_activity_dragging(self, start_time, end_time):
        self.start_time.setTime(QTime.fromString(start_time, "HH:mm:ss"))
        self.end_time.setTime(QTime.fromString(end_time, "HH:mm:ss"))


def main():
    app = QApplication(sys.argv)
    window = TimeBlockingApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
