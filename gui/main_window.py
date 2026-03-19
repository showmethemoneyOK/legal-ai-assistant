from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
                             QLabel, QStackedWidget)
from legal_ai.gui.widgets.vector_manager import VectorManager
from legal_ai.gui.widgets.agent_workflow import AgentWorkflow
from legal_ai.gui.widgets.model_config import ModelConfig

class MainWindow(QMainWindow):
    """
    The main application window that serves as the container for all feature modules.
    It uses a tabbed interface to switch between different functionalities.
    """
    def __init__(self, token, user_id):
        super().__init__()
        self.token = token # Store the auth token for API calls
        self.user_id = user_id
        self.setWindowTitle("Legal AI Assistant - Desktop Client")
        self.resize(1000, 700)
        
        self.init_ui()

    def init_ui(self):
        """Initialize the main window layout and tabs."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Tabs for different modules (Workbench, Vector DB, Document AI)
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # 1. Dashboard / Workbench (Placeholder)
        # In a real app, this would show recent docs, tasks, etc.
        dashboard = QWidget()
        dashboard_layout = QVBoxLayout()
        dashboard_layout.addWidget(QLabel("Welcome to your Legal AI Workbench!"))
        dashboard.setLayout(dashboard_layout)
        tabs.addTab(dashboard, "Workbench")
        
        # 2. Vector DB Manager
        # This is the core module for managing the legal knowledge base
        vector_manager = VectorManager(self.token)
        tabs.addTab(vector_manager, "Vector DB Manager")
        
        # 3. Agent Workflow
        # New LangGraph-powered multi-agent system
        agent_workflow = AgentWorkflow(self.token)
        tabs.addTab(agent_workflow, "Agent Workflow")

        # 4. Model Config
        model_config = ModelConfig(self.token)
        tabs.addTab(model_config, "Model Config")

        # 5. Document AI (Placeholder)
        # Future module for document generation and review
        doc_ai = QWidget()
        doc_ai_layout = QVBoxLayout()
        doc_ai_layout.addWidget(QLabel("Document Generation & Review (Coming Soon)"))
        doc_ai.setLayout(doc_ai_layout)
        tabs.addTab(doc_ai, "Document AI")
        
        # Status Bar
        self.statusBar().showMessage(f"Logged in as User ID: {self.user_id}")
