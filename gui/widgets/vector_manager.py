from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QMessageBox, QListWidget, QLineEdit, QHBoxLayout)
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
        layout.addWidget(QLabel("<h2>Vector Database Manager</h2>"))
        
        # --- Section 2: Full Rebuild ---
        # Button to trigger full database rebuild
        self.rebuild_btn = QPushButton("Rebuild Public Vector DB (Full)")
        self.rebuild_btn.clicked.connect(self.rebuild_db)
        layout.addWidget(self.rebuild_btn)
        
        # --- Section 3: Single File Update ---
        layout.addWidget(QLabel("<h3>Single File Update</h3>"))
        file_layout = QHBoxLayout()
        
        # Input field for file path
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select file path...")
        file_layout.addWidget(self.file_path_input)
        
        # Browse button to open file dialog
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)
        
        # Update button to trigger single file update
        self.update_btn = QPushButton("Update File")
        self.update_btn.clicked.connect(self.update_single_file)
        file_layout.addWidget(self.update_btn)
        
        layout.addLayout(file_layout)
        
        # --- Section 4: Search Test ---
        layout.addWidget(QLabel("<h3>Search Test</h3>"))
        search_layout = QHBoxLayout()
        
        # Input field for search query
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter query...")
        search_layout.addWidget(self.search_input)
        
        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_law)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        # --- Section 5: Results Display ---
        # List widget to show search results or logs
        self.results_list = QListWidget()
        layout.addWidget(self.results_list)
        
        self.setLayout(layout)

    def rebuild_db(self):
        """
        Handler for Rebuild Button.
        Sends a request to the backend to rebuild the entire public vector database.
        """
        reply = QMessageBox.question(self, 'Confirm Rebuild', 
                                     "Rebuilding will delete all existing vectors and re-process all files. Are you sure?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # UI Feedback: Disable button and show loading state
                self.rebuild_btn.setEnabled(False)
                self.rebuild_btn.setText("Rebuilding... (Please wait)")
                self.repaint() # Force UI update
                
                # Call Backend API
                response = requests.post(f"{API_URL}/rebuild")
                
                if response.status_code == 200:
                    QMessageBox.information(self, "Success", f"Rebuild complete: {response.json()}")
                else:
                    QMessageBox.warning(self, "Error", f"Rebuild failed: {response.text}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Connection error: {e}")
            finally:
                # Restore button state
                self.rebuild_btn.setEnabled(True)
                self.rebuild_btn.setText("Rebuild Public Vector DB (Full)")

    def browse_file(self):
        """Open file dialog to select a document."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Law File", "", "Documents (*.docx *.pdf)")
        if file_name:
            self.file_path_input.setText(file_name)

    def update_single_file(self):
        """
        Handler for Update File Button.
        Sends a request to update a specific file in the vector database.
        """
        file_path = self.file_path_input.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a file first.")
            return

        try:
            # Call Backend API
            response = requests.post(f"{API_URL}/update_single", json={"file_path": file_path})
            
            if response.status_code == 200:
                QMessageBox.information(self, "Success", f"Update complete: {response.json()}")
            else:
                QMessageBox.warning(self, "Error", f"Update failed: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection error: {e}")

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
            response = requests.post(f"{API_URL}/search", json={"query": query, "n_results": 5})
            
            if response.status_code == 200:
                results = response.json()
                self.results_list.clear()
                
                # Parse ChromaDB results
                # Chroma returns {'ids': [[...]], 'documents': [[...]], 'metadatas': [[...]]}
                docs = results.get('documents', [[]])[0]
                metas = results.get('metadatas', [[]])[0]
                
                if not docs:
                    self.results_list.addItem("No results found.")
                    return

                for i, doc in enumerate(docs):
                    meta = metas[i] if i < len(metas) else {}
                    law_name = meta.get('law_name', 'Unknown')
                    # Display snippet: [Law Name] Content...
                    item_text = f"[{law_name}] {doc[:150]}..."
                    self.results_list.addItem(item_text)
            else:
                QMessageBox.warning(self, "Error", f"Search failed: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection error: {e}")
