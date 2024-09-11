from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication


class LockScreen:
    def __init__(self, widget):
        self.widget = widget
        self.original_flags = widget.windowFlags()
        self.original_geometry = widget.geometry()
        self.timer = QTimer(widget)
        self.timer.timeout.connect(self.stay_on_top)
        self.is_active = False

    def activate(self):
        if not self.is_active:
            self.original_geometry = self.widget.geometry()
            self.widget.setWindowFlags(
                self.original_flags
                | Qt.Window
                | Qt.FramelessWindowHint
                | Qt.WindowStaysOnTopHint
            )
            self.widget.showFullScreen()
            self.timer.start(100)
            self.is_active = True

    def deactivate(self):
        if self.is_active:
            self.timer.stop()
            self.is_active = False

            # Exit full-screen mode
            self.widget.showNormal()

            # Hide the widget before changing its properties
            self.widget.hide()

            # Restore the original window flags
            self.widget.setWindowFlags(self.original_flags)

            # Restore the original geometry
            self.widget.setGeometry(self.original_geometry)

            # Show the widget after all changes have been made
            self.widget.show()

            # Force the widget to update its layout
            self.widget.updateGeometry()
            QApplication.processEvents()

    def stay_on_top(self):
        if self.is_active:
            self.widget.raise_()
            self.widget.activateWindow()
