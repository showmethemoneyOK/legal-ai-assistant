from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QLabel, QStackedWidget, QPushButton, QFrame, QGridLayout)
from PyQt6.QtCore import Qt
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
        self.setWindowTitle("法律AI助手 - 桌面客户端")
        self.resize(1200, 800)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                color: #333;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #d5d5d5;
            }
        """)
        
        self.init_ui()

    def init_ui(self):
        """Initialize the main window layout and tabs."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        central_widget.setLayout(main_layout)
        
        # Tabs for different modules
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # 1. Dashboard / Workbench
        dashboard = self.create_workbench()
        tabs.addTab(dashboard, "📊 工作台")
        
        # 2. Vector DB Manager
        vector_manager = VectorManager(self.token)
        tabs.addTab(vector_manager, "🗄️ 向量库管理")
        
        # 3. Agent Workflow
        agent_workflow = AgentWorkflow(self.token)
        tabs.addTab(agent_workflow, "🤖 智能分析")

        # 4. Model Config
        model_config = ModelConfig(self.token)
        tabs.addTab(model_config, "⚙️ 模型配置")
        
        # Status Bar
        self.statusBar().showMessage(f"已登录 | 用户ID: {self.user_id}")
        self.statusBar().setStyleSheet("background-color: #e0e0e0; color: #333;")

    def create_workbench(self):
        """Create an optimized dashboard/workbench UI."""
        dashboard = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Welcome Header
        header = QLabel("欢迎来到您的法律AI工作台")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #333;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        subtitle = QLabel("在这里，您可以管理法律知识库、执行智能分析并配置AI模型。")
        subtitle.setStyleSheet("font-size: 16px; color: #666;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Quick Actions Grid
        grid = QGridLayout()
        grid.setSpacing(20)
        
        def create_card(title, desc, color):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 2px solid {color};
                    border-radius: 8px;
                    padding: 20px;
                }}
            """)
            card_layout = QVBoxLayout()
            
            t_label = QLabel(title)
            t_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color}; border: none;")
            t_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            d_label = QLabel(desc)
            d_label.setStyleSheet("font-size: 14px; color: #555; border: none;")
            d_label.setWordWrap(True)
            d_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            card_layout.addWidget(t_label)
            card_layout.addWidget(d_label)
            card.setLayout(card_layout)
            return card
            
        grid.addWidget(create_card("🗄️ 向量库管理", "上传并向量化法律文档，构建专属的法律知识库供AI检索。", "#2196F3"), 0, 0)
        grid.addWidget(create_card("🤖 智能分析", "使用多智能体工作流，针对复杂的法律问题进行深度剖析和建议。", "#4CAF50"), 0, 1)
        grid.addWidget(create_card("⚙️ 模型配置", "管理本地和在线的大语言模型，动态切换以获取最佳性能。", "#FF9800"), 1, 0)
        grid.addWidget(create_card("🛡️ 隐私与安全", "所有本地模型分析和向量检索均在您的设备上进行，确保数据安全。", "#9C27B0"), 1, 1)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        dashboard.setLayout(layout)
        return dashboard
