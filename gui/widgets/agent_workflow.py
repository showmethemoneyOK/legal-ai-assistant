from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QTextBrowser, QMessageBox, QHBoxLayout, QFileDialog, QListWidget)
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
        self._is_running = True

    def run(self):
        try:
            if not self._is_running:
                return
            response = requests.post(f"{API_URL}/run", json={"question": self.question})
            if response.status_code == 200:
                if self._is_running:
                    self.finished.emit(response.json())
            else:
                if self._is_running:
                    self.error.emit(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))
                
    def cancel(self):
        self._is_running = False

class AgentWorkflow(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        layout.addWidget(QLabel("<h2>Legal Agent Workflow</h2>"))
        layout.addWidget(QLabel("Multi-agent system powered by LangGraph"))

        # Input Area
        input_layout = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Enter your legal question or select a file...")
        input_layout.addWidget(self.question_input)

        # Browse File Button
        self.browse_btn = QPushButton("Upload File")
        self.browse_btn.clicked.connect(self.browse_file)
        input_layout.addWidget(self.browse_btn)

        self.run_btn = QPushButton("Test Agent Flow")
        self.run_btn.clicked.connect(self.run_agent)
        input_layout.addWidget(self.run_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_agent)
        input_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(input_layout)

        # Dashboard / Metrics Area
        dash_layout = QHBoxLayout()
        self.status_label = QLabel("<b>Status:</b> Idle")
        dash_layout.addWidget(self.status_label)
        layout.addLayout(dash_layout)

        # Split output area into Execution Log and Final Report
        output_layout = QHBoxLayout()
        
        # Execution Log (Left)
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel("<h3>Execution Log</h3>"))
        self.log_list = QListWidget()
        log_layout.addWidget(self.log_list)
        output_layout.addLayout(log_layout, 1)
        
        # Analysis Report (Right)
        report_layout = QVBoxLayout()
        report_layout.addWidget(QLabel("<h3>Analysis Report</h3>"))
        self.output_browser = QTextBrowser()
        report_layout.addWidget(self.output_browser)
        output_layout.addLayout(report_layout, 2)

        layout.addLayout(output_layout)
        self.setLayout(layout)

    def browse_file(self):
        """Open file dialog to select a document."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Legal Document", "", "Documents (*.docx *.pdf)")
        if file_name:
            self.question_input.setText(file_name)

    def run_agent(self):
        question = self.question_input.text().strip()
        if not question:
            QMessageBox.warning(self, "Warning", "Please enter a question.")
            return

        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.run_btn.setText("Running...")
        self.status_label.setText("<b>Status:</b> Running workflow...")
        
        self.output_browser.clear()
        self.log_list.clear()
        self.log_list.addItem("Starting LangGraph multi-agent workflow...")

        self.worker = AgentWorker(question)
        self.worker.finished.connect(self.handle_result)
        self.worker.error.connect(self.handle_error)
        self.worker.start()
        
    def cancel_agent(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.status_label.setText("<b>Status:</b> Cancelled by user.")
            self.log_list.addItem("Workflow cancelled.")
            self.reset_buttons()

    def handle_result(self, result):
        self.reset_buttons()
        self.status_label.setText("<b>Status:</b> Completed")
        
        final_answer = result.get("final_answer", "")
        # Populate Execution Log if available from Phase 3 state
        # In a real streaming app, this would be updated via SSE. 
        # Here we show the final state log.
        if "execution_log" in result:
            self.log_list.clear()
            for log in result["execution_log"]:
                node = log.get("node", "unknown")
                summary = log.get("summary", "")
                self.log_list.addItem(f"[{node}] {summary}")
        else:
            self.log_list.addItem("Workflow completed successfully.")
            
        display_text = final_answer.replace('\n', '<br>')
        self.output_browser.setHtml(display_text)

    def handle_error(self, error_msg):
        self.reset_buttons()
        self.status_label.setText("<b>Status:</b> Error")
        self.log_list.addItem(f"ERROR: {error_msg}")
        QMessageBox.critical(self, "Error", f"Agent execution failed: {error_msg}")
        
    def reset_buttons(self):
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.run_btn.setText("Test Agent Flow")
