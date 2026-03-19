from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QTextBrowser, QMessageBox, QHBoxLayout, QFileDialog, QListWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
import asyncio
import uuid

class AgentSignals(QObject):
    log_updated = pyqtSignal(str)
    node_changed = pyqtSignal(str)
    verifier_updated = pyqtSignal(dict)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

class AgentWorker(QThread):
    def __init__(self, question):
        super().__init__()
        self.question = question
        self._is_running = True
        self.signals = AgentSignals()

    def run(self):
        try:
            # We use asyncio.run to execute the async LangGraph workflow
            asyncio.run(self._run_workflow())
        except Exception as e:
            if self._is_running:
                self.signals.error.emit(str(e))
                
    async def _run_workflow(self):
        from legal_ai.service.agents.multi_agent_orchestrator import orchestrator
        from legal_ai.service.agent_log_service import save_execution_log
        
        initial_state = {
            "question": self.question,
            "parsed_info": {}, "goal_consensus": {}, "node_plan": [],
            "sub_results": [], "vote_records": [], "verifier_result": {},
            "loop_count": 0, "execution_log": [], "model_history": set()
        }
        task_id = str(uuid.uuid4())
        final_state = initial_state.copy()
        
        try:
            async for event in orchestrator.app.astream(initial_state, stream_mode="updates"):
                if not self._is_running:
                    break
                
                for node_name, state_update in event.items():
                    self.signals.node_changed.emit(node_name)
                    # Merge update into final_state
                    for k, v in state_update.items():
                        if k == "execution_log":
                            final_state["execution_log"].extend(v)
                            # Emit the newly added log
                            for log_entry in v:
                                self.signals.log_updated.emit(f"[{log_entry['node']}] {log_entry['summary']}")
                        elif k == "model_history":
                            final_state["model_history"].update(v)
                        else:
                            final_state[k] = v
                    
                    if "verifier_result" in state_update:
                        self.signals.verifier_updated.emit(state_update["verifier_result"])
                        
            if self._is_running:
                save_execution_log(task_id, self.question, final_state)
                self.signals.finished.emit(final_state)
        except Exception as e:
            if self._is_running:
                self.signals.error.emit(str(e))

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
        
        self.metrics_label = QLabel("<b>Metrics:</b> N/A")
        dash_layout.addWidget(self.metrics_label)
        
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
        
        report_header = QHBoxLayout()
        report_header.addWidget(QLabel("<h3>Analysis Report</h3>"))
        self.export_btn = QPushButton("Export Report")
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setEnabled(False)
        report_header.addWidget(self.export_btn)
        
        report_layout.addLayout(report_header)
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
        self.export_btn.setEnabled(False)
        self.run_btn.setText("Running...")
        self.status_label.setText("<b>Status:</b> Running workflow...")
        self.metrics_label.setText("<b>Metrics:</b> N/A")
        
        self.output_browser.clear()
        self.log_list.clear()
        self.log_list.addItem("Starting LangGraph multi-agent workflow...")

        self.worker = AgentWorker(question)
        self.worker.signals.log_updated.connect(self.update_log)
        self.worker.signals.node_changed.connect(self.update_node_status)
        self.worker.signals.verifier_updated.connect(self.update_verifier_metrics)
        self.worker.signals.finished.connect(self.handle_result)
        self.worker.signals.error.connect(self.handle_error)
        self.worker.start()
        
    def cancel_agent(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.status_label.setText("<b>Status:</b> Cancelled by user.")
            self.log_list.addItem("Workflow cancelled.")
            self.reset_buttons()

    def update_log(self, log_msg):
        self.log_list.addItem(log_msg)
        self.log_list.scrollToBottom()
        
    def update_node_status(self, node_name):
        self.status_label.setText(f"<b>Status:</b> Executing {node_name} node...")
        
    def update_verifier_metrics(self, verifier_data):
        score = verifier_data.get("score", 0)
        passed = verifier_data.get("passed", False)
        self.metrics_label.setText(f"<b>Metrics:</b> Verifier Score: {score}/10, Passed: {passed}")

    def handle_result(self, result):
        self.reset_buttons()
        self.status_label.setText("<b>Status:</b> Completed")
        self.export_btn.setEnabled(True)
        self.last_result = result
        
        self.log_list.addItem("Workflow completed successfully.")
            
        final_answer = result.get("final_answer", "")
        try:
            import markdown
            html = markdown.markdown(final_answer, extensions=['tables'])
            self.output_browser.setHtml(html)
        except ImportError:
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

    def export_report(self):
        if not hasattr(self, 'last_result') or not self.last_result:
            return
            
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Report", "legal_report.md", "Markdown Files (*.md)")
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.last_result.get("final_answer", ""))
                QMessageBox.information(self, "Success", "Report exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save report: {e}")
