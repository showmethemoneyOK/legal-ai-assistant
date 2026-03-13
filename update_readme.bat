@echo off
echo Updating README.md with Git instructions...
cd /d "%~dp0"

REM Add verify_git.bat to Git
git add verify_git.bat

REM Update README.md
echo # Legal AI Assistant (本地法律文书AI助手) > README_new.md
echo. >> README_new.md
echo ![GitHub](https://img.shields.io/badge/version-1.0.0-blue) >> README_new.md
echo ![Python](https://img.shields.io/badge/python-3.10%2B-green) >> README_new.md
echo ![License](https://img.shields.io/badge/license-MIT-yellow) >> README_new.md
echo. >> README_new.md
echo 这是一个基于 Python 的本地化法律文书 AI 助手，专为律师和律所设计。它集成了本地向量数据库（ChromaDB）、SQLite 数据库、FastAPI 后端服务和 PyQt6 桌面客户端，实现了法律文书的智能检索、生成和管理功能。 >> README_new.md
echo. >> README_new.md
echo ## 🚀 快速开始 >> README_new.md
echo. >> README_new.md
echo ### 1. 克隆仓库 >> README_new.md
echo ```bash >> README_new.md
echo git clone https://github.com/yourusername/legal-ai-assistant.git >> README_new.md
echo cd legal-ai-assistant >> README_new.md
echo ``` >> README_new.md
echo. >> README_new.md
echo ### 2. 安装依赖 >> README_new.md
echo ```bash >> README_new.md
echo pip install -r requirements.txt >> README_new.md
echo ``` >> README_new.md
echo. >> README_new.md
echo ### 3. 运行程序 >> README_new.md
echo ```bash >> README_new.md
echo python main.py >> README_new.md
echo ``` >> README_new.md
echo. >> README_new.md
echo ## 📦 项目状态 >> README_new.md
echo. >> README_new.md
echo - ✅ **基础架构完成**: 完整的多层架构 >> README_new.md
echo - ✅ **数据库设计**: SQLite + ChromaDB 集成 >> README_new.md
echo - ✅ **核心服务**: 向量库管理、用户认证、文档服务 >> README_new.md
echo - ✅ **GUI界面**: PyQt6 桌面应用 >> README_new.md
echo - ✅ **API接口**: FastAPI 后端服务 >> README_new.md
echo - ⚠️ **待完善**: AI功能实现、打包部署 >> README_new.md
echo. >> README_new.md
echo ## 🔧 技术栈 >> README_new.md
echo. >> README_new.md
echo - **语言**: Python 3.10+ >> README_new.md
echo - **GUI框架**: PyQt6 >> README_new.md
echo - **后端框架**: FastAPI >> README_new.md
echo - **数据库**: SQLite (关系型数据), ChromaDB (向量数据) >> README_new.md
echo - **文档解析**: python-docx, pdfplumber >> README_new.md
echo - **ORM**: SQLAlchemy >> README_new.md
echo. >> README_new.md
echo ## 📁 项目结构 >> README_new.md
echo. >> README_new.md
echo ``` >> README_new.md
echo legal_ai/ >> README_new.md
echo ├── api/                 # FastAPI 接口层 >> README_new.md
echo │   ├── routes/          # 路由定义 (auth, doc, vector) >> README_new.md
echo │   └── server.py        # 服务启动入口 >> README_new.md
echo ├── core/                # 核心配置 >> README_new.md
echo │   ├── config.py        # 路径与环境配置 >> README_new.md
echo │   └── database.py      # 数据库连接会话 >> README_new.md
echo ├── data/                # 数据存储目录 >> README_new.md
echo │   └── public_law/      # 公共法律法规文件 (.docx, .pdf) >> README_new.md
echo ├── db/                  # 数据库模型与存储 >> README_new.md
echo │   ├── models.py        # SQLAlchemy 模型定义 >> README_new.md
echo │   └── app.db           # SQLite 数据库文件 (自动生成) >> README_new.md
echo ├── gui/                 # PyQt6 界面层 >> README_new.md
echo │   ├── widgets/         # 自定义组件 (如向量库管理) >> README_new.md
echo │   ├── login_window.py  # 登录窗口 >> README_new.md
echo │   └── main_window.py   # 主窗口 >> README_new.md
echo ├── service/             # 业务逻辑层 >> README_new.md
echo │   ├── auth_service.py  # 用户认证服务 >> README_new.md
echo │   ├── doc_service.py   # 文档管理服务 >> README_new.md
echo │   ├── law_service.py   # 法条解析与分块服务 >> README_new.md
echo │   └── vector_service.py # 向量库核心服务 (重建/更新/检索) >> README_new.md
echo ├── vector_db/           # 向量数据库存储目录 >> README_new.md
echo │   └── chroma_db/       # ChromaDB 持久化文件 >> README_new.md
echo ├── main.py              # 项目启动入口 >> README_new.md
echo └── requirements.txt     # 项目依赖 >> README_new.md
echo ``` >> README_new.md
echo. >> README_new.md
echo ## 🤝 贡献 >> README_new.md
echo. >> README_new.md
echo 欢迎提交 Issue 和 Pull Request 来改进本项目。 >> README_new.md
echo. >> README_new.md
echo ## 📄 许可证 >> README_new.md
echo. >> README_new.md
echo MIT License >> README_new.md
echo. >> README_new.md
echo --- >> README_new.md
echo. >> README_new.md
echo *项目创建时间: 2026-03-13* >> README_new.md
echo *最后更新: 2026-03-13* >> README_new.md

REM Replace README.md
move /y README_new.md README.md

REM Add updated README.md to Git
git add README.md

REM Commit changes
git commit -m "Update README.md with GitHub instructions and project status"

echo.
echo README.md updated successfully!
echo.
echo Next steps:
echo 1. Create a new repository on GitHub
echo 2. Run: git remote add origin https://github.com/yourusername/legal-ai-assistant.git
echo 3. Run: git push -u origin main
echo.
pause