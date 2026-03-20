from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QMessageBox, QListWidget, QLineEdit, QHBoxLayout,
                             QListWidgetItem, QDialog, QTextBrowser)
from PyQt6.QtCore import Qt
import requests
import os

# API Endpoint Configuration
API_URL = "http://127.0.0.1:8000/api/vector"

class VectorManager(QWidget):
    """
    GUI Widget for managing the vector database.
    Provides functionalities to:
    1. Rebuild the entire public law vector database.
    2. Update a single file in the vector database.
    3. Perform test searches against the vector database.
    """
    def __init__(self, token):
        super().__init__()
        self.token = token # Auth token for API requests (if needed in future)
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface layout and widgets."""
        layout = QVBoxLayout()
        
        # --- Section 1: Title ---
        layout.addWidget(QLabel("<h2>🗄️ 向量数据库管理</h2>"))
        
        # --- Section 2: Full Rebuild ---
        # Button to trigger full database rebuild
        self.rebuild_btn = QPushButton("🔄 重建公开法律向量库（完整）")
        self.rebuild_btn.setStyleSheet("background-color: #FF5722; color: white; font-weight: bold; border-radius: 4px; padding: 8px;")
        self.rebuild_btn.clicked.connect(self.rebuild_db)
        layout.addWidget(self.rebuild_btn)
        
        # --- Section 3: Single File Update ---
        layout.addWidget(QLabel("<h3>📄 单文件更新</h3>"))
        file_layout = QHBoxLayout()
        
        # Input field for file path
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("选择文件路径...")
        file_layout.addWidget(self.file_path_input)
        
        # Browse button to open file dialog
        self.browse_btn = QPushButton("📂 浏览")
        self.browse_btn.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px; padding: 6px;")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)
        
        # Update button to trigger single file update
        self.update_btn = QPushButton("📤 更新文件")
        self.update_btn.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px; padding: 6px;")
        self.update_btn.clicked.connect(self.update_single_file)
        file_layout.addWidget(self.update_btn)
        
        layout.addLayout(file_layout)
        
        # --- Section 4: Search Test ---
        layout.addWidget(QLabel("<h3>🔍 法律条款搜索</h3>"))
        search_layout = QHBoxLayout()
        
        # Input field for search query
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入查询内容...")
        search_layout.addWidget(self.search_input)
        
        # Search button
        self.search_btn = QPushButton("🔎 搜索")
        self.search_btn.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px; padding: 6px;")
        self.search_btn.clicked.connect(self.search_law)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        # --- Section 5: Results Display ---
        # List widget to show search results or logs
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_law_details)
        layout.addWidget(self.results_list)
        
        self.setLayout(layout)

    def rebuild_db(self):
        """
        Handler for Rebuild Button.
        Sends a request to the backend to rebuild the entire public vector database.
        """
        reply = QMessageBox.question(self, '确认重建', 
                                     "重建将删除所有现有向量并重新处理所有文件。您确定吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # UI Feedback: Disable button and show loading state
                self.rebuild_btn.setEnabled(False)
                self.rebuild_btn.setText("重建中... (请稍候)")
                self.repaint() # Force UI update
                
                # Call Backend API
                response = requests.post(f"{API_URL}/rebuild")
                
                if response.status_code == 200:
                    QMessageBox.information(self, "成功", f"重建完成: {response.json()}")
                else:
                    QMessageBox.warning(self, "错误", f"重建失败: {response.text}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"连接错误: {e}")
            finally:
                # Restore button state
                self.rebuild_btn.setEnabled(True)
                self.rebuild_btn.setText("🔄 重建公开法律向量库（完整）")

    def browse_file(self):
        """Open file dialog to select a document."""
        file_name, _ = QFileDialog.getOpenFileName(self, "选择法律文件", "", "Documents (*.docx *.pdf)")
        if file_name:
            self.file_path_input.setText(file_name)

    def update_single_file(self):
        """
        Handler for Update File Button.
        Sends a request to update a specific file in the vector database.
        """
        file_path = self.file_path_input.text()
        if not file_path:
            QMessageBox.warning(self, "警告", "请先选择一个文件。")
            return

        try:
            # Call Backend API
            response = requests.post(f"{API_URL}/update_single", json={"file_path": file_path})
            
            if response.status_code == 200:
                QMessageBox.information(self, "成功", f"更新完成: {response.json()}")
            else:
                QMessageBox.warning(self, "错误", f"更新失败: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接错误: {e}")

    def search_law(self):
        """
        Handler for Search Button.
        Performs a semantic search against the vector database.
        """
        query = self.search_input.text()
        if not query:
            return

        try:
            # Call Backend API
            # Increased n_results to 50 as per user request to show "all relevant" concise provisions
            response = requests.post(f"{API_URL}/search", json={"query": query, "n_results": 50})
            
            if response.status_code == 200:
                results = response.json()
                self.results_list.clear()
                
                # Parse ChromaDB results
                # Chroma returns {'ids': [[...]], 'documents': [[...]], 'metadatas': [[...]]}
                docs = results.get('documents', [[]])[0]
                metas = results.get('metadatas', [[]])[0]
                
                if not docs:
                    self.results_list.addItem("未找到结果。")
                    return

                for i, doc in enumerate(docs):
                    meta = metas[i] if i < len(metas) else {}
                    law_name = meta.get('law_name', '未知法律')
                    
                    # Display snippet: [Law Name] Content...
                    # Truncate for display in list
                    display_text = f"[{law_name}] {doc[:100]}..."
                    
                    # Create List Item
                    item = QListWidgetItem(display_text)
                    
                    # Store full data in the item for detail view
                    item_data = {
                        "law_name": law_name,
                        "content": doc,
                        "metadata": meta
                    }
                    item.setData(Qt.ItemDataRole.UserRole, item_data)
                    
                    self.results_list.addItem(item)
            else:
                QMessageBox.warning(self, "错误", f"搜索失败: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接错误: {e}")

    def show_law_details(self, item):
        """
        Display full details of the selected law provision in a dialog.
        """
        data = item.data(Qt.ItemDataRole.UserRole)
        
        if not data:
            return # Should not happen for valid items
            
        law_name = data.get("law_name", "未知法律")
        content = data.get("content", "无可用内容。")
        
        # Create a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"详细信息: {law_name}")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        # Title Label
        title_label = QLabel(f"<h2>{law_name}</h2>")
        layout.addWidget(title_label)
        
        # Content Browser (Scrollable)
        text_browser = QTextBrowser()
        text_browser.setPlainText(content)
        layout.addWidget(text_browser)
        
        # Close Button
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
