import json
from datetime import date
from pathlib import Path
from typing import Dict, Any


def update_habits(file_path: str) -> None:
    """
    Update habits for the current date in the specified JSON file.

    This function reads the JSON file, sets all habits for the current date to False,
    and writes the updated data back to the file. If the current date doesn't exist
    in the data, it creates a new entry with the same habits as the most recent date,
    all set to False.

    Args:
        file_path (str): Relative path to the JSON file containing habit data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON data.
        KeyError: If the expected data structure is not found in the JSON.
    """
    try:
        # Construct the full path
        full_path = Path(file_path).resolve()

        # Read the JSON data
        with open(full_path, "r") as file:
            data = json.load(file)

        if "history" not in data:
            raise KeyError("The JSON file does not contain a 'history' key.")

        history = data["history"]

        # Get today's date
        today = date.today().strftime("%Y-%m-%d")

        if not history:
            raise KeyError("The 'history' in the JSON file is empty.")

        if today not in history:
            # If today's date doesn't exist, find the most recent date
            most_recent_date = max(history.keys())
            if "habits" not in history[most_recent_date]:
                raise KeyError(
                    f"'habits' key not found in history for {most_recent_date}"
                )

            # Copy habits from the most recent date
            history[today] = {"habits": []}
            for habit in history[most_recent_date]["habits"]:
                new_habit = habit.copy()
                new_habit["completed"] = False
                history[today]["habits"].append(new_habit)
        else:
            if "habits" not in history[today]:
                raise KeyError(f"'habits' key not found in history for {today}")

            # If today's date exists, set all habits to False
            for habit in history[today]["habits"]:
                habit["completed"] = False

        # Write the updated data back to the file
        with open(full_path, "w") as file:
            json.dump(data, file, indent=2)

        print(f"Habits for {today} have been updated successfully.")

    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} contains invalid JSON data.")
    except KeyError as e:
        print(f"Error: Invalid data structure in the JSON file. {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print(
            "Please check your JSON file structure and ensure it contains the expected data."
        )


if __name__ == "__main__":
    relative_path = "habits_management/app_data/habits.json"
    update_habits(relative_path)
