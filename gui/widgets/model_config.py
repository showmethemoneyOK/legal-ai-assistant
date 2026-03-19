from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox)
from PyQt6.QtCore import Qt
import requests

class ModelConfig(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.config_url = "http://127.0.0.1:8000/api/config"
        self.proxy_url = "http://127.0.0.1:8000/api/proxy"
        self.init_ui()
        self.load_models()
        self.load_default_model()
        self.load_execution_mode()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("<h2>Local & Online Model Management</h2>"))
        layout.addWidget(QLabel("Add models to connect directly (e.g., DeepSeek API, local Ollama) and set your default model."))

        # Execution Mode Toggle
        mode_layout = QHBoxLayout()
        self.async_checkbox = QCheckBox("Enable Async Execution Mode")
        self.async_checkbox.setToolTip("If checked, the system will use asynchronous requests for faster processing when calling LLMs.")
        self.async_checkbox.toggled.connect(self.toggle_async_mode)
        mode_layout.addWidget(self.async_checkbox)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # Top section: Add New Model Form
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("<h3>Add New Model Configuration</h3>"))

        # Model Name (Frontend ID)
        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("e.g., my-qwen, online-deepseek")
        form_layout.addWidget(QLabel("Model Alias (Unique Name):"))
        form_layout.addWidget(self.model_name_input)

        # Target Model
        self.litellm_model_input = QLineEdit()
        self.litellm_model_input.setPlaceholderText("e.g., qwen2.5:7b, deepseek-chat, gpt-4o")
        form_layout.addWidget(QLabel("Actual Target Model Name:"))
        form_layout.addWidget(self.litellm_model_input)

        # API Base
        self.api_base_input = QLineEdit()
        self.api_base_input.setPlaceholderText("e.g., http://127.0.0.1:11434/v1 or https://api.deepseek.com/v1")
        form_layout.addWidget(QLabel("API Base URL (Required for Ollama and DeepSeek):"))
        form_layout.addWidget(self.api_base_input)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("API Key (Required for online models like DeepSeek)")
        form_layout.addWidget(QLabel("API Key (Optional for local):"))
        form_layout.addWidget(self.api_key_input)

        layout.addLayout(form_layout)

        # Buttons Layout for Form
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Save Model Configuration")
        self.add_btn.clicked.connect(self.add_model_to_proxy)
        btn_layout.addWidget(self.add_btn)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("<hr>"))
        layout.addWidget(QLabel("<h3>Available Models in Database</h3>"))

        # Table to show all current models
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(2)
        self.model_table.setHorizontalHeaderLabels(["Model Alias", "Target Model"])
        self.model_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.model_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.model_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.model_table.itemSelectionChanged.connect(self.on_table_select)
        layout.addWidget(self.model_table)

        # Buttons for Table actions
        action_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.clicked.connect(self.load_models)
        self.test_btn = QPushButton("Test Connectivity")
        self.test_btn.clicked.connect(self.test_selected_model)
        self.set_default_btn = QPushButton("Set as Default Model")
        self.set_default_btn.clicked.connect(self.set_default_model)
        
        action_layout.addWidget(self.refresh_btn)
        action_layout.addWidget(self.test_btn)
        action_layout.addWidget(self.set_default_btn)
        layout.addLayout(action_layout)
        
        # Display current default
        self.current_default_label = QLabel("<b>Current Default Model:</b> None")
        layout.addWidget(self.current_default_label)

        self.setLayout(layout)

    def load_models(self):
        """Fetch models from database via backend."""
        try:
            response = requests.get(f"{self.proxy_url}/models")
            if response.status_code == 200:
                models = response.json()
                self.model_table.setRowCount(len(models))
                for row, model_data in enumerate(models):
                    model_name = model_data.get("model_name", "Unknown")
                    target = model_data.get("litellm_params", {}).get("model", "Unknown")
                    self.model_table.setItem(row, 0, QTableWidgetItem(model_name))
                    self.model_table.setItem(row, 1, QTableWidgetItem(target))
            else:
                QMessageBox.warning(self, "Warning", f"Failed to load models: {response.text}")
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not connect to backend: {e}")

    def load_default_model(self):
        """Fetch DEFAULT_MODEL_NAME from SystemConfig."""
        try:
            response = requests.get(self.config_url)
            if response.status_code == 200:
                configs = response.json()
                default_model = configs.get("DEFAULT_MODEL_NAME", "Not Set")
                self.current_default_label.setText(f"<b>Current Default Model:</b> {default_model}")
        except Exception as e:
            print(f"Error loading config: {e}")

    def load_execution_mode(self):
        """Fetch ASYNC_MODEL_EXECUTION from SystemConfig."""
        try:
            response = requests.get(self.config_url)
            if response.status_code == 200:
                configs = response.json()
                is_async = configs.get("ASYNC_MODEL_EXECUTION", "false").lower() == "true"
                # Block signals to prevent triggering toggle_async_mode when loading
                self.async_checkbox.blockSignals(True)
                self.async_checkbox.setChecked(is_async)
                self.async_checkbox.blockSignals(False)
        except Exception as e:
            print(f"Error loading execution mode: {e}")

    def toggle_async_mode(self, checked):
        """Update the ASYNC_MODEL_EXECUTION in SystemConfig."""
        payload = {
            "configs": {
                "ASYNC_MODEL_EXECUTION": "true" if checked else "false"
            }
        }
        try:
            response = requests.post(self.config_url, json=payload)
            if response.status_code == 200:
                mode = "Async" if checked else "Sync"
                # QMessageBox.information(self, "Success", f"Execution mode set to {mode}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to update execution mode: {response.text}")
                # Revert checkbox state
                self.async_checkbox.blockSignals(True)
                self.async_checkbox.setChecked(not checked)
                self.async_checkbox.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
            self.async_checkbox.blockSignals(True)
            self.async_checkbox.setChecked(not checked)
            self.async_checkbox.blockSignals(False)

    def on_table_select(self):
        pass # Optional: populate form if needed, but usually we just select for actions

    def add_model_to_proxy(self):
        model_name = self.model_name_input.text().strip()
        litellm_model = self.litellm_model_input.text().strip()
        api_base = self.api_base_input.text().strip()
        api_key = self.api_key_input.text().strip()

        if not model_name or not litellm_model:
            QMessageBox.warning(self, "Input Error", "Model Alias and Target Model are required.")
            return

        payload = {
            "model_name": model_name,
            "litellm_params": {
                "model": litellm_model
            }
        }
        
        if api_base:
            payload["litellm_params"]["api_base"] = api_base
        if api_key:
            payload["litellm_params"]["api_key"] = api_key

        try:
            response = requests.post(f"{self.proxy_url}/models", json=payload)
            if response.status_code == 200:
                QMessageBox.information(self, "Success", f"Model '{model_name}' saved to database successfully!")
                self.load_models()
                # Clear form
                self.model_name_input.clear()
                self.litellm_model_input.clear()
                self.api_base_input.clear()
                self.api_key_input.clear()
            else:
                QMessageBox.critical(self, "Error", f"Failed to add model: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def test_selected_model(self):
        selected_items = self.model_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a model from the list to test.")
            return

        row = selected_items[0].row()
        model_name = self.model_table.item(row, 0).text()

        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing...")
        
        try:
            response = requests.post(f"{self.proxy_url}/test-model", json={"model_name": model_name})
            res_data = response.json()
            if res_data.get("status") == "success":
                mode = res_data.get("mode", "Unknown")
                time_ms = res_data.get("time_ms", 0)
                msg = f"Connected to '{model_name}'.\n\nReply: {res_data.get('reply')}\n\nExecution: {mode} ({time_ms} ms)"
                QMessageBox.information(self, "Test Success", msg)
            else:
                QMessageBox.warning(self, "Test Failed", f"Failed to connect to '{model_name}'.\nDetails: {res_data.get('message')}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during testing: {e}")
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("Test Connectivity")

    def set_default_model(self):
        selected_items = self.model_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a model from the list first.")
            return

        row = selected_items[0].row()
        model_name = self.model_table.item(row, 0).text()

        payload = {
            "configs": {
                "DEFAULT_MODEL_NAME": model_name
            }
        }

        try:
            response = requests.post(self.config_url, json=payload)
            if response.status_code == 200:
                QMessageBox.information(self, "Success", f"'{model_name}' set as Default Model successfully!")
                self.load_default_model()
            else:
                QMessageBox.critical(self, "Error", f"Failed to set default model: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
