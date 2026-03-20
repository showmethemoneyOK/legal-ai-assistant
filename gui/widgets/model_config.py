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

        layout.addWidget(QLabel("<h2>🖥️ 本地和在线模型管理</h2>"))
        layout.addWidget(QLabel("添加模型以直接连接（例如，DeepSeek API，本地Ollama），并设置您的默认模型。"))

        # Execution Mode Toggle
        mode_layout = QHBoxLayout()
        self.async_checkbox = QCheckBox("启用异步执行模式")
        self.async_checkbox.setToolTip("如果选中，系统将在调用LLM时使用异步请求以加快处理速度。")
        self.async_checkbox.toggled.connect(self.toggle_async_mode)
        mode_layout.addWidget(self.async_checkbox)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # Top section: Add New Model Form
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("<h3>添加新模型配置</h3>"))

        # Model Name (Frontend ID)
        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("例如: my-qwen, online-deepseek")
        form_layout.addWidget(QLabel("模型别名（唯一名称）:"))
        form_layout.addWidget(self.model_name_input)

        # Target Model
        self.litellm_model_input = QLineEdit()
        self.litellm_model_input.setPlaceholderText("例如: qwen2.5:7b, deepseek-chat, gpt-4o")
        form_layout.addWidget(QLabel("实际目标模型名称:"))
        form_layout.addWidget(self.litellm_model_input)

        # API Base
        self.api_base_input = QLineEdit()
        self.api_base_input.setPlaceholderText("例如: http://127.0.0.1:11434/v1 或 https://api.deepseek.com/v1")
        form_layout.addWidget(QLabel("API基础URL (Ollama和DeepSeek必填):"))
        form_layout.addWidget(self.api_base_input)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("API密钥 (在线模型如DeepSeek必填)")
        form_layout.addWidget(QLabel("API密钥 (本地模型可选):"))
        form_layout.addWidget(self.api_key_input)

        layout.addLayout(form_layout)

        # Buttons Layout for Form
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("💾 保存模型配置")
        self.add_btn.clicked.connect(self.add_model_to_proxy)
        btn_layout.addWidget(self.add_btn)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("<hr>"))
        layout.addWidget(QLabel("<h3>数据库中的可用模型</h3>"))

        # Table to show all current models
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(2)
        self.model_table.setHorizontalHeaderLabels(["模型别名", "目标模型"])
        self.model_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.model_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.model_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.model_table.itemSelectionChanged.connect(self.on_table_select)
        layout.addWidget(self.model_table)

        # Buttons for Table actions
        action_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 刷新列表")
        self.refresh_btn.clicked.connect(self.load_models)
        self.test_btn = QPushButton("🧪 测试连接")
        self.test_btn.clicked.connect(self.test_selected_model)
        self.set_default_btn = QPushButton("⭐ 设为默认模型")
        self.set_default_btn.clicked.connect(self.set_default_model)
        
        action_layout.addWidget(self.refresh_btn)
        action_layout.addWidget(self.test_btn)
        action_layout.addWidget(self.set_default_btn)
        layout.addLayout(action_layout)
        
        # Display current default
        self.current_default_label = QLabel("<b>当前默认模型:</b> 无")
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
                QMessageBox.warning(self, "警告", f"加载模型失败: {response.text}")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法连接到后端: {e}")

    def load_default_model(self):
        """Fetch DEFAULT_MODEL_NAME from SystemConfig."""
        try:
            response = requests.get(self.config_url)
            if response.status_code == 200:
                configs = response.json()
                default_model = configs.get("DEFAULT_MODEL_NAME", "未设置")
                self.current_default_label.setText(f"<b>当前默认模型:</b> {default_model}")
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
                mode = "异步" if checked else "同步"
                # QMessageBox.information(self, "成功", f"执行模式已设置为 {mode}")
            else:
                QMessageBox.critical(self, "错误", f"更新执行模式失败: {response.text}")
                # Revert checkbox state
                self.async_checkbox.blockSignals(True)
                self.async_checkbox.setChecked(not checked)
                self.async_checkbox.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误: {e}")
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
            QMessageBox.warning(self, "输入错误", "模型别名和目标模型是必填项。")
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
                QMessageBox.information(self, "成功", f"模型 '{model_name}' 已成功保存到数据库！")
                self.load_models()
                # Clear form
                self.model_name_input.clear()
                self.litellm_model_input.clear()
                self.api_base_input.clear()
                self.api_key_input.clear()
            else:
                QMessageBox.critical(self, "错误", f"添加模型失败: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误: {e}")

    def test_selected_model(self):
        selected_items = self.model_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先从列表中选择一个模型进行测试。")
            return

        row = selected_items[0].row()
        model_name = self.model_table.item(row, 0).text()

        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")
        
        try:
            response = requests.post(f"{self.proxy_url}/test-model", json={"model_name": model_name})
            res_data = response.json()
            if res_data.get("status") == "success":
                mode = res_data.get("mode", "未知")
                time_ms = res_data.get("time_ms", 0)
                msg = f"成功连接到 '{model_name}'。\n\n回复: {res_data.get('reply')}\n\n执行模式: {mode} ({time_ms} ms)"
                QMessageBox.information(self, "测试成功", msg)
            else:
                QMessageBox.warning(self, "测试失败", f"无法连接到 '{model_name}'。\n详细信息: {res_data.get('message')}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试期间发生错误: {e}")
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("🧪 测试连接")

    def set_default_model(self):
        selected_items = self.model_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先从列表中选择一个模型。")
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
                QMessageBox.information(self, "成功", f"'{model_name}' 已成功设为默认模型！")
                self.load_default_model()
            else:
                QMessageBox.critical(self, "错误", f"设置默认模型失败: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误: {e}")
