import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QStyle,
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QSize


class WelcomePage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Welcome")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QPushButton#continueButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                padding: 10px 20px;
                min-width: 150px;
            }
            QPushButton#continueButton:hover {
                background-color: #1E90FF;
            }
            QLabel#welcomeLabel {
                font-size: 36px;
                font-weight: bold;
                margin: 0;
                padding: 0;
            }
        """
        )

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        central_widget.setLayout(layout)

        # Welcome message with info icon
        welcome_container = QWidget()
        welcome_layout = QHBoxLayout(welcome_container)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(0)

        welcome_label = QLabel("Welcome", self)
        welcome_label.setObjectName("welcomeLabel")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(welcome_label)

        info_button = QPushButton()
        info_icon = self.style().standardIcon(QStyle.SP_MessageBoxInformation)
        info_button.setIcon(info_icon)
        info_button.setIconSize(QSize(16, 16))
        info_button.setFixedSize(20, 20)
        info_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                margin: 0;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
        """
        )
        info_button.clicked.connect(self.show_info)

        # Create a container for the info button to position it precisely
        info_container = QWidget()
        info_container.setFixedSize(30, 36)  # Adjust this size as needed
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.addWidget(info_button, alignment=Qt.AlignTop | Qt.AlignLeft)

        welcome_layout.addWidget(info_container)

        layout.addWidget(welcome_container, alignment=Qt.AlignCenter)

        # Spacer
        layout.addSpacing(20)

        # Continue button
        self.continue_button = QPushButton("Continue", self)
        self.continue_button.setObjectName("continueButton")
        self.continue_button.clicked.connect(self.on_continue)
        layout.addWidget(self.continue_button, alignment=Qt.AlignCenter)

    def show_info(self):
        info_box = QMessageBox(self)
        info_box.setWindowTitle("App Information")
        info_box.setText(
            "The digital era has overwhelmed our brain's capacity to filter and focus, fragmenting our attention across countless distractions. Our app guides your online experience towards what truly matters. By thoughtfully curating options and reinforcing intentional choices, we help align the power of digital tools with your core aspirations."
        )
        info_box.setIcon(QMessageBox.Information)
        info_box.setStyleSheet(
            """
            QMessageBox {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                padding: 5px 10px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """
        )
        info_box.exec_()

    def on_continue(self):
        print("continue")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    welcome_window = WelcomePage()
    welcome_window.show()
    sys.exit(app.exec_())
