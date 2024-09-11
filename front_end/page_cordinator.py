import sys
import logging
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QMessageBox,
)
import multiprocessing
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal
from front_end.pages import welcome, schedule, queue_app, event_timer, completion_page
from front_end.pages.journal import JournalApp
import requests
from lock_screen import LockScreen
import time


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PageCoordinator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Habit Manager")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("QMainWindow { background-color: #1E1E1E; }")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Initialize pages
        self.pages = [
            welcome.WelcomePage(),  # index 0
            JournalApp(),  # index 1
            schedule.TimeBlockingApp(),  # index 2
            queue_app.TaskQueue(),  # index 3
            event_timer.CircularTimer(lock_in_mode=False),  # index 4
            completion_page.CompletionForm(),  # index 5
        ]

        # Add pages to the stacked widget
        for page in self.pages:
            self.stacked_widget.addWidget(page)

        self.lock_screen = LockScreen(self)
        self.locked_pages = [0, 1, 2]  # Pages where Lock Screen should be active

        self.setup_connections()
        self.api_base_url = "http://localhost:8000/api"
        self.check_activity_timer = QTimer(self)
        self.check_activity_timer.timeout.connect(self.check_current_activity)
        self.check_activity_timer.start(5000)  # Check every 5 seconds

        # Start by checking the current activity
        self.check_current_activity()

    def setup_connections(self):
        self.pages[0].continue_button.clicked.connect(self.next_page)
        self.pages[1].journal_completed.connect(self.next_page)
        self.pages[2].complete_button.clicked.connect(self.next_page)
        self.pages[3].get_to_work_button.clicked.connect(self.show_event_timer)
        self.pages[4].timerComplete.connect(self.show_completion)
        self.pages[4].changeActivityRequested.connect(self.show_queue)
        self.pages[5].yes_button.clicked.connect(self.show_queue)

    def check_current_activity(self):
        try:
            response = requests.get(f"{self.api_base_url}/current-activity")
            if response.status_code == 200:
                data = response.json()
                self.handle_activity(data, from_check=True)
            else:
                logger.error(
                    f"Failed to get current activity. Status code: {response.status_code}"
                )
        except requests.RequestException as e:
            logger.error(f"Error checking current activity: {str(e)}")

    def handle_activity(self, activity_data, from_check=False):
        activity_type = activity_data["activity_type"]
        page_number = activity_data.get("page_number")

        # Don't change page if currently on completion page
        if self.stacked_widget.currentIndex() == 5:  # Completion page index
            return

        if activity_type == "event":
            self.show_event(activity_data["event_info"], from_check)
        elif activity_type == "habit_page" and page_number is not None:
            self.show_habit_page(page_number, from_check)
        elif activity_type == "schedule":
            self.show_schedule(from_check)
        elif activity_type == "queue":
            self.show_queue(from_check)
        else:
            logger.error(f"Unknown activity type: {activity_type}")

    def show_event(self, event_info, from_check=False):
        logger.debug(f"Showing event: {event_info}")
        if self.stacked_widget.currentIndex() == 4:
            # If already on event timer, update the info
            self.pages[4].fetch_task()
        else:
            # Otherwise, set the info and switch to event timer
            self.set_current_page(4, from_check)

    def show_habit_page(self, page_number, from_check=False):
        logger.debug(f"Showing habit page: {page_number}")
        if page_number in self.locked_pages:
            self.set_current_page(page_number, from_check)
        else:
            logger.error(f"Invalid habit page number: {page_number}")

    def show_schedule(self, from_check=False):
        logger.debug("Showing schedule")
        self.set_current_page(2, from_check)  # Assuming schedule is at index 2

    def show_queue(self, from_check=False):
        logger.debug("Showing queue")
        self.set_current_page(3, from_check)  # Assuming queue is at index 3

    def show_event_timer(self):
        logger.debug("Showing event timer")
        self.set_current_page(4)  # Event timer is at index 4

    def show_completion(self):
        logger.debug("Showing completion page")
        self.set_current_page(5)  # Completion page is at index 5

    def next_page(self):
        logger.debug("Next page requested")
        current_index = self.stacked_widget.currentIndex()
        next_index = (current_index + 1) % len(self.pages)
        self.set_current_page(next_index)

    def set_current_page(self, page_number, from_check=False):
        self.stacked_widget.setCurrentIndex(page_number)

        # Manage LockScreen state
        if page_number in self.locked_pages:
            self.lock_screen.activate()
        else:
            self.lock_screen.deactivate()

        if not from_check:
            try:
                response = requests.put(
                    f"{self.api_base_url}/current-activity/set-page",
                    json={"page_number": page_number},
                    timeout=5,  # Add a timeout to prevent hanging
                )
                if response.status_code == 200:
                    data = response.json()
                    self.handle_activity(data, from_check=True)
                else:
                    logger.error(
                        f"Failed to set page. Status code: {response.status_code}"
                    )
                    self.show_error_message(
                        "Failed to update the current activity on the server."
                    )
            except requests.RequestException as e:
                logger.error(f"Error setting page: {str(e)}")
                self.show_error_message("Failed to communicate with the server.")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)


def run_app():
    app = QApplication(sys.argv)
    coordinator = PageCoordinator()
    coordinator.show()

    activity_monitor = ActivityMonitor("http://localhost:8000/api")
    activity_monitor.activity_received.connect(coordinator.handle_activity)

    return app.exec_()
