from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QTextBrowser, QMessageBox, QHBoxLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import requests
import json

API_URL = "http://127.0.0.1:8000/api/agent"

class AgentWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, question):
        super().__init__()
        self.question = question

    def run(self):
        try:
            response = requests.post(f"{API_URL}/run", json={"question": self.question})
            if response.status_code == 200:
                self.finished.emit(response.json())
            else:
                self.error.emit(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            self.error.emit(str(e))

class AgentWorkflow(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        layout.addWidget(QLabel("<h2>Legal Agent Workflow</h2>"))
        layout.addWidget(QLabel("Multi-agent system powered by LangGraph"))

        # Input Area
        input_layout = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Enter your legal question or file path here...")
        input_layout.addWidget(self.question_input)

        self.run_btn = QPushButton("Test Agent Flow")
        self.run_btn.clicked.connect(self.run_agent)
        input_layout.addWidget(self.run_btn)
        
        layout.addLayout(input_layout)

        # Output Area
        layout.addWidget(QLabel("<h3>Analysis Report</h3>"))
        self.output_browser = QTextBrowser()
        layout.addWidget(self.output_browser)

        # Debug/Log Area (optional, maybe just show in output for now)
        
        self.setLayout(layout)

    def run_agent(self):
        question = self.question_input.text().strip()
        if not question:
            QMessageBox.warning(self, "Warning", "Please enter a question.")
            return

        self.run_btn.setEnabled(False)
        self.run_btn.setText("Running...")
        self.output_browser.setText("Agent is thinking... (Parser -> Retriever -> Analysis)")

        self.worker = AgentWorker(question)
        self.worker.finished.connect(self.handle_result)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def handle_result(self, result):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Test Agent Flow")
        
        final_answer = result.get("final_answer", "")
        # Format for display
        parsed = result.get("parsed_info", {})
        
        display_text = f"""
        <b>Parsed Intent:</b> {parsed.get('intent', 'N/A')}<br>
        <b>Keywords:</b> {parsed.get('keywords', [])}<br>
        <hr>
        {final_answer.replace(chr(10), '<br>')}
        """
        self.output_browser.setHtml(display_text)

    def handle_error(self, error_msg):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Test Agent Flow")
        QMessageBox.critical(self, "Error", f"Agent execution failed: {error_msg}")
