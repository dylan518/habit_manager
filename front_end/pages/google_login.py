import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSignal
from google_auth_oauthlib.flow import Flow
from urllib.parse import parse_qs, urlparse

class GoogleAuthView(QMainWindow):
    auth_finished = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Google OAuth WebView")
        self.setGeometry(100, 100, 1000, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)

        self.flow = None
        self.web_view.urlChanged.connect(self.url_changed)
        self.auth_finished.connect(self.on_auth_finished)

    def showEvent(self, event):
        super().showEvent(event)
        self.start_auth()
    
    def get_credentials_file(self):
        """Returns the correct path to credentials.env file."""
        
        # Check if running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Use sys._MEIPASS to find the bundled files
            base_path = sys._MEIPASS
        else:
            # Assume the project root is two levels up from the current file's directory
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

        # Return the path to credentials.env located at the project root
        return os.path.join(base_path, 'credentials.env')

    def start_auth(self):
        try:
            credentials_file = self.get_credentials_file()  # Get the correct path to credentials.env
            self.flow = Flow.from_client_secrets_file(
                credentials_file,  # Use the dynamically located path
                scopes=["https://www.googleapis.com/auth/calendar"],
                redirect_uri="http://localhost:8080/",
            )
            auth_url, _ = self.flow.authorization_url(prompt="consent")
            print(f"Loading OAuth URL: {auth_url}")
            self.web_view.load(QUrl(auth_url))
        except Exception as e:
            print(f"Error starting authentication: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to start authentication: {str(e)}")


    def url_changed(self, url):
        if url.toString().startswith("http://localhost:8080/"):
            code = parse_qs(urlparse(url.toString()).query).get("code", [None])[0]
            if code:
                self.auth_finished.emit(code)

    def on_auth_finished(self, code):
        try:
            self.flow.fetch_token(code=code)
            credentials = self.flow.credentials

            # Save the credentials
            with open("token.json", "w") as token_file:
                token_file.write(credentials.to_json())

            print("Authentication successful. Token saved to token.json")
            self.close()
        except Exception as e:
            print(f"Error getting token: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to get token: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = GoogleAuthView()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()