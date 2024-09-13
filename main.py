import os
import sys

def set_python_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    print(f"Python path set to: {sys.path}")

# Call this function at the start
set_python_path()

import logging
import time
import multiprocessing
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
import requests
import uvicorn
from fastapi import FastAPI
from backend.app import app
from backend.database.database import engine
from backend.database.models import Base
from front_end.page_cordinator import PageCoordinator

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set timezone
os.environ["TZ"] = "America/Los_Angeles"  # Replace with your desired time zone


class ActivityMonitor(QObject):
    activity_received = pyqtSignal(dict)

    def __init__(self, api_base_url):
        super().__init__()
        self.api_base_url = api_base_url

    def check_activity(self):
        try:
            response = requests.get(f"{self.api_base_url}/current-activity")
            if response.status_code == 200:
                data = response.json()
                self.activity_received.emit(data)
                return data
            else:
                logger.error(
                    f"Failed to get current activity. Status code: {response.status_code}"
                )
        except requests.RequestException as e:
            logger.error(f"Error checking current activity: {str(e)}")
        return None


def run_backend():
    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Run the FastAPI server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        access_log=True,
        use_colors=True,
    )


def run_frontend():
    app = QApplication(sys.argv)
    coordinator = PageCoordinator()
    coordinator.show()

    activity_monitor = ActivityMonitor("http://localhost:8000/api")
    activity_monitor.activity_received.connect(coordinator.handle_activity)

    return app.exec_()


def monitor_and_relaunch_frontend():
    while True:
        process = multiprocessing.Process(target=run_frontend)
        process.start()
        process.join()  # Wait for the process to finish

        logger.info("Frontend closed. Checking activity in 5 seconds...")
        time.sleep(5)  # Wait 5 seconds before checking activity

        activity_monitor = ActivityMonitor("http://localhost:8000/api")
        current_activity = activity_monitor.check_activity()

        if current_activity and current_activity.get("activity_type") != "queue":
            logger.info("Relaunching frontend...")
        else:
            logger.info(
                "No relaunch-triggering activity detected. Continuing to monitor..."
            )


def main():
    # Start the backend process
    backend_process = multiprocessing.Process(target=run_backend)
    backend_process.start()

    # Wait for the backend to start up
    time.sleep(5)

    # Start the frontend process with monitoring
    frontend_process = multiprocessing.Process(target=monitor_and_relaunch_frontend)
    frontend_process.start()

    # Wait for the processes to finish
    backend_process.join()
    frontend_process.join()


if __name__ == "__main__":
    main()
