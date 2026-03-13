from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox)
import requests

API_URL = "http://127.0.0.1:8000/api/user"

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Legal AI Assistant - Login")
        self.setFixedSize(300, 200)
        self.init_ui()
        self.token = None
        self.user_id = None

    def init_ui(self):
        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        self.register_btn = QPushButton("Register")
        self.register_btn.clicked.connect(self.handle_register)
        layout.addWidget(self.register_btn)

        self.setLayout(layout)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        try:
            response = requests.post(f"{API_URL}/login", data={"username": username, "password": password})
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Login failed. Check credentials.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection error: {e}")

    def handle_register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        try:
            response = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
            if response.status_code == 200:
                 QMessageBox.information(self, "Success", "Registration successful! Please login.")
            else:
                 QMessageBox.warning(self, "Error", f"Registration failed: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection error: {e}")
