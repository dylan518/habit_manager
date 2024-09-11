import sys
import requests
import time
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QMessageBox,
    QInputDialog,
)
from PyQt5.QtCore import Qt
from front_end.components.table_components import (
    FlexibleTable,
    COMMON_STYLES,
    run_app,
    TableLineEdit,
)

API_BASE_URL = "http://localhost:8000/api"


class HabitManagerUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.habits = self.load_habits()
        self.init_ui()

    def load_habits(self):
        try:
            response = requests.get(f"{API_BASE_URL}/habits/today")
            data = response.json()
            print("API Response:", data)  # Add this line to print the response
            return data.get("habits", [])  # Use .get() with a default value
        except requests.RequestException as e:
            print(f"Error loading habits: {e}")
            return []

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        title = QLabel("Habit Manager")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        columns = [
            {"name": "Habit", "type": "text", "key": "name", "width": 3},
            {
                "name": "Associated App",
                "type": "text",
                "key": "associated_app",
                "width": 3,
            },
            {"name": "Status", "type": "status", "key": "completed", "width": 2},
            {
                "name": "Edit",
                "type": "action",
                "text": "Edit",
                "action": self.edit_habit,
                "width": 1,
            },
            {
                "name": "Delete",
                "type": "action",
                "text": "Delete",
                "action": self.delete_habit,
                "width": 1,
            },
        ]

        self.habit_table = FlexibleTable(columns)
        self.habit_table.populate_table(self.habits)
        self.habit_table.update_status = self.toggle_habit_status
        layout.addWidget(self.habit_table)

        add_habit_layout = QHBoxLayout()
        self.new_habit_name = TableLineEdit()
        self.new_habit_name.setPlaceholderText("New habit name")
        self.new_habit_app = TableLineEdit()
        self.new_habit_app.setPlaceholderText("Associated app (optional)")
        add_button = QPushButton("Add Habit")
        add_button.clicked.connect(self.add_habit)
        add_habit_layout.addWidget(self.new_habit_name, 3)
        add_habit_layout.addWidget(self.new_habit_app, 3)
        add_habit_layout.addWidget(add_button, 2)
        layout.addLayout(add_habit_layout)

        self.setMinimumSize(1000, 600)
        self.setWindowTitle("Habit Manager")
        self.setStyleSheet(COMMON_STYLES)

    def add_habit(self):
        name = self.new_habit_name.text().strip()
        associated_app = self.new_habit_app.text().strip()
        if name:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/habits",
                    json={"name": name, "associated_app": associated_app},
                )
                response.raise_for_status()
                QMessageBox.information(self, "Success", "Habit added successfully.")

                self.refresh_habits()

                self.new_habit_name.clear()
                self.new_habit_app.clear()
            except requests.RequestException as e:
                QMessageBox.critical(self, "Error", f"Failed to add habit: {str(e)}")
        else:
            QMessageBox.warning(self, "Invalid Input", "Habit name cannot be empty.")

    def edit_habit(self, habit):
        new_name, ok1 = QInputDialog.getText(
            self,
            "Edit Habit",
            "Enter new habit name:",
            QLineEdit.Normal,
            habit["name"],
        )
        new_app, ok2 = QInputDialog.getText(
            self,
            "Edit Habit",
            "Enter new associated app:",
            QLineEdit.Normal,
            habit.get("associated_app", ""),
        )
        if ok1 and ok2 and new_name.strip():
            try:
                response = requests.put(
                    f"{API_BASE_URL}/habits/{habit['id']}",
                    json={"name": new_name.strip(), "associated_app": new_app.strip()},
                )
                response.raise_for_status()
                QMessageBox.information(self, "Success", "Habit updated successfully.")
                self.refresh_habits()
            except requests.RequestException as e:
                QMessageBox.critical(self, "Error", f"Failed to update habit: {str(e)}")
        elif not new_name.strip():
            QMessageBox.warning(self, "Invalid Input", "Habit name cannot be empty.")

    def delete_habit(self, habit):
        reply = QMessageBox.question(
            self,
            "Delete Habit",
            f"Are you sure you want to delete the habit '{habit['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                response = requests.put(
                    f"{API_BASE_URL}/habits/{habit['id']}",
                    json={"delete": True},
                )
                response.raise_for_status()
                QMessageBox.information(self, "Success", "Habit deleted successfully.")
                self.refresh_habits()
            except requests.RequestException as e:
                QMessageBox.critical(self, "Error", f"Failed to delete habit: {str(e)}")

    def toggle_habit_status(self, row, key, completed):
        habit = self.habits[row]
        try:
            response = requests.put(f"{API_BASE_URL}/habits/{habit['id']}/complete")
            response.raise_for_status()
            habit[key] = completed
            self.habits[row] = habit
        except requests.RequestException as e:
            QMessageBox.critical(
                self, "Error", f"Failed to update habit status: {str(e)}"
            )

    def refresh_habits(self):
        time.sleep(0.1)  # Small delay to ensure server-side updates are complete
        self.habits = self.load_habits()
        self.habit_table.populate_table(self.habits)


def main():
    app = QApplication(sys.argv)
    window = HabitManagerUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
