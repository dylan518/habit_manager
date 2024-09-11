import sys
from Foundation import NSObject
from AppKit import (
    NSAlert,
    NSAlertFirstButtonReturn,
    NSAlertSecondButtonReturn,
    NSTextField,
)
import objc


class CompletionAlert(NSObject):
    @objc.python_method
    def initWithCallback_(self, callback):
        self = objc.super(CompletionAlert, self).init()
        if self is None:
            return None
        self.callback = callback
        return self

    @objc.python_method
    def showAlert(self):
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Work Session Completed")
        alert.setInformativeText_("Are you done with your task?")
        alert.addButtonWithTitle_("Yes")
        alert.addButtonWithTitle_("No, I need more time")
        response = alert.runModal()
        if response == NSAlertFirstButtonReturn:
            self.callback(True, 0)
        elif response == NSAlertSecondButtonReturn:
            self.showTimeInputAlert()

    @objc.python_method
    def showTimeInputAlert(self):
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Additional Time")
        alert.setInformativeText_("How many more minutes do you need?")
        alert.addButtonWithTitle_("Submit")
        alert.addButtonWithTitle_("Cancel")
        text_field = NSTextField.alloc().initWithFrame_(((0, 0), (200, 24)))
        alert.setAccessoryView_(text_field)
        response = alert.runModal()
        if response == NSAlertFirstButtonReturn:
            try:
                additional_time = int(text_field.stringValue())
                self.callback(False, additional_time * 60)  # Convert minutes to seconds
            except ValueError:
                self.showTimeInputAlert()  # Show the alert again if input is invalid
        else:
            self.showAlert()  # Go back to the first alert if cancelled


def main():
    def handle_alert_response(is_done, additional_time):
        if is_done:
            print("Task completed")
        else:
            print(f"Task extended by {additional_time} seconds")

    alert = CompletionAlert.alloc().initWithCallback_(handle_alert_response)
    alert.showAlert()


if __name__ == "__main__":
    main()
