import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt
from front_end.components.table_components import (
    FlexibleTable,
    ActionButton,
    COMMON_STYLES,
    run_app,
)

API_BASE_URL = (
    "http://localhost:8000/api"  
)


class DailyHabitsUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.habits = self.load_habits()
        self.init_ui()

    def load_habits(self):
        try:
            response = requests.get(f"{API_BASE_URL}/habits/today")
            data = response.json()
            return data["habits"]
        except requests.RequestException as e:
            print(f"Error loading habits: {e}")
            return []

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Title
        title = QLabel("Daily Habit Checker")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Habit Table
        columns = [
            {"name": "Habit", "key": "name", "type": "text", "width": 2},
            {"name": "Status", "key": "completed", "type": "status", "width": 1},
            {
                "name": "Run App",
                "key": "associated_app",
                "type": "action",
                "text": "Run",
                "width": 1,
                "action": self.run_associated_app,
            },
        ]
        self.habit_table = FlexibleTable(columns)
        self.populate_habit_table()
        layout.addWidget(self.habit_table)

        # Buttons
        button_layout = QHBoxLayout()
        self.confirm_button = ActionButton("Confirm and Close", self.close)
        button_layout.addWidget(self.confirm_button)
        layout.addLayout(button_layout)

        # Window settings
        self.setMinimumSize(600, 400)
        self.setWindowTitle("Daily Habit Checker")
        self.setStyleSheet(COMMON_STYLES)

    def populate_habit_table(self):
        self.habit_table.populate_table(self.habits)

    def run_associated_app(self, habit):
        app_name = habit["associated_app"]
        print(f"Running associated app: {app_name}")
        run_app(app_name)

        # Update habit status
        habit["completed"] = True
        print(f"Habit '{habit['name']}' marked as completed")
        self.populate_habit_table()  # Refresh the table to show the updated status

    def refresh_habits(self):
        self.habits = self.load_habits()
        self.populate_habit_table()
        print("Habits refreshed")


def main():
    app = QApplication(sys.argv)
    window = DailyHabitsUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
