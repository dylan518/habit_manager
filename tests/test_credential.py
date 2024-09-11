import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow


def test_credentials():
    try:
        # Load the JSON from the .env file
        with open("credentials.env", "r") as file:
            creds_data = json.load(file)

        # Extract credentials
        client_config = creds_data["installed"]
        client_id = client_config["client_id"]
        client_secret = client_config["client_secret"]

        print("Credentials loaded successfully.")
        print(f"Client ID: {client_id[:5]}...{client_id[-5:]}")
        print(f"Client Secret: {client_secret[:5]}...{client_secret[-5:]}")

        # Try to initialize OAuth2 flow
        try:
            flow = Flow.from_client_config(
                {"installed": client_config},
                scopes=["https://www.googleapis.com/auth/calendar.readonly"],
            )
            print("OAuth2 flow initialized successfully.")
        except Exception as e:
            print(f"Error initializing OAuth2 flow: {str(e)}")

    except FileNotFoundError:
        print("Error: credentials.env file not found.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON in credentials.env file.")
    except KeyError as e:
        print(f"Error: Missing key in credentials.env: {str(e)}")


if __name__ == "__main__":
    test_credentials()
