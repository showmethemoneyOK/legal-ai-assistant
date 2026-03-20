from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
import requests

API_URL = "http://127.0.0.1:8000/api/user"

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("法律AI助手 - 登录")
        self.setFixedSize(400, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-family: 'Segoe UI', 'Microsoft YaHei';
                color: #333;
            }
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
            QPushButton {
                padding: 12px;
                min-height: 25px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-family: 'Microsoft YaHei';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton#registerBtn {
                background-color: transparent;
                color: #4CAF50;
                border: 1px solid #4CAF50;
            }
            QPushButton#registerBtn:hover {
                background-color: #e8f5e9;
            }
        """)
        self.init_ui()
        self.token = None
        self.user_id = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Title Area
        title_label = QLabel("欢迎使用法律AI助手")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #4CAF50;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("请登录或注册以继续")
        subtitle_label.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 10px;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # Form Area
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("")
        layout.addWidget(QLabel("用户名:"))
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("密码:"))
        layout.addWidget(self.password_input)

        layout.addSpacing(10)

        # Buttons
        self.login_btn = QPushButton("登录")
        self.login_btn.setMinimumHeight(25)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        self.register_btn = QPushButton("注册")
        self.register_btn.setMinimumHeight(25)
        self.register_btn.setObjectName("registerBtn")
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
                QMessageBox.warning(self, "登录失败", "用户名或密码错误。")
        except Exception as e:
            QMessageBox.critical(self, "网络错误", f"连接服务器失败: {e}")

    def handle_register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        try:
            response = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
            if response.status_code == 200:
                 QMessageBox.information(self, "成功", "注册成功！请登录。")
            else:
                 QMessageBox.warning(self, "注册失败", f"错误信息: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "网络错误", f"连接服务器失败: {e}")
