import sys
import os
import threading
import uvicorn
import time
from PyQt6.QtWidgets import QApplication, QMessageBox

# Ensure project root is in sys.path to resolve module imports correctly
# This is crucial when running the script directly from different directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from legal_ai.gui.login_window import LoginWindow
from legal_ai.gui.main_window import MainWindow

def run_api():
    """
    Starts the FastAPI backend server in a separate thread.
    
    This allows the backend API and the frontend GUI to run simultaneously
    within the same process, simplifying deployment for a local standalone app.
    """
    uvicorn.run("legal_ai.api.server:app", host="127.0.0.1", port=8000, log_level="info")

def main():
    """
    Main entry point of the application.
    1. Starts the API server thread.
    2. Launches the PyQt6 GUI application.
    3. Handles the login flow before showing the main window.
    """
    # 1. Start API server in a background thread (Daemon thread dies when main program exits)
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Wait a brief moment for the server to initialize
    # In a production app, a proper health check loop would be better
    time.sleep(2)

    # 2. Initialize Qt Application
    app = QApplication(sys.argv)
    
    # 3. Show Login Window
    login = LoginWindow()
    if login.exec() == login.Accepted:
        # If login is successful, launch the Main Window
        # We pass the token and user_id to maintain session state
        window = MainWindow(token=login.token, user_id=login.user_id)
        window.show()
        
        # Start the Qt event loop
        sys.exit(app.exec())
    else:
        # If login is cancelled or failed, exit the application
        sys.exit()

if __name__ == "__main__":
    main()
