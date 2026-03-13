
本地部署法律文书AI助手——完整版开发文档
适用场景：Windows 本地私有化部署、律师/律所内部使用、数据不出本地
技术栈：Python 3.10+ + PyQt6（可视化GUI） + FastAPI（本地服务） + SQLite（权限/资产库） + Chroma（向量数据库） + python-docx/pdfplumber（文档解析） + 本地Embedding模型
核心特色：用户隔离 + 文件授权共享 + 通用法律向量库（自动按文件夹更新） + 单文件增量更新向量库 + AI文书生成/审查/检索
一、文档概述
1.1 文档目的
定义本地法律文书AI助手完整功能、架构、模块、接口、数据结构、向量库更新机制，确保开发、测试、部署可直接落地。
1.2 适用范围
• 本地Windows 10/11 运行
• 多用户、权限隔离、文件授权
• 通用法律库（法条）自动构建、增量更新
• 支持个人私有文书向量检索
• 可视化操作，无命令行
1.3 核心新增要求（你指定）
1. 通用法律向量库：自动读取指定目录下的法条DOC/DOCX/PDF
2. 全自动更新：放入新文件 → 一键重建/增量更新通用库
3. 单文件粒度更新：如《民法典》更新，只更新民法典对应向量
4. 不影响其他文件、不重建全库
5. 本地永久存储，不上云
二、系统总体架构
2.1 架构分层
1. 可视化GUI层（PyQt6） —— 用户操作界面
2. 本地接口层（FastAPI） —— 内部功能调用
3. 业务逻辑层 —— 权限、文书、审查、共享、向量管理
4. 数据持久层
◦ SQLite：用户、权限、文书、版本、日志
◦ Chroma：向量数据库（通用法律库 + 用户私有库）
5. 工具链：文档解析、Embedding生成、Word/PDF导出
2.2 向量库架构（最重要部分）
• 公共向量库（通用法律库）
路径：./vector_db/public/
来源：./data/public_law/ 下的法条文件（民法典、刑法、劳动合同法、司法解释等）
• 用户私有向量库
路径：./vector_db/user_{user_id}/
来源：个人上传的文书、证据、案例
2.3 向量库更新机制设计
1. 全量重建：替换/新增多个法条 → 重建整个公共库
2. 增量单文件更新：只更新《民法典》或某一部法律
3. 文件唯一标识：通过文件名+文件哈希唯一绑定向量块
4. 删除即清理：删除某法条文件 → 可清理对应向量
三、功能模块完整设计（全部可开发）
模块1：用户与权限系统（多用户、数据隔离）
1.1 功能
• 注册、登录、密码加密（bcrypt）
• 每个用户只能看到自己的文书/向量库/文件
• 文件级授权：查看 / 可编辑
• 授权可撤销、可变更权限
• 操作日志（查看、编辑、共享、导出、向量更新）
1.2 权限规则
• 文档创建者 = 所有者（最高权限）
• 授权用户：只读 → 可看不可改
• 授权用户：可写 → 可修改、可保存版本
• 向量库：公共库所有人可读，不可写
• 私有向量库：仅本人可见、可管理
1.3 接口
• POST /api/user/register
• POST /api/user/login

• GET /api/user/info

• GET /api/user/logs
模块2：可视化桌面GUI（Windows本地界面）

2.1 主界面布局

左侧导航：

• 工作台

• 文书AI生成

• 文书AI审查

• 我的文书库

• 向量库管理（公共+私有）

• 文件共享与协作

• 用户中心

2.2 核心页面

1. 工作台

◦ 最近文书、待审查、共享给我的文件

2. 向量库管理页面（最关键）

◦ 显示公共法律库状态

◦ 显示“法条目录路径”

◦ 按钮：重新构建公共向量库

◦ 按钮：单文件更新（选择一个法律文件更新）

◦ 显示：文件数、块数、向量数、更新时间

3. 文件授权页面

◦ 选择文档 → 授权用户 → 设置权限

4. 文书编辑/预览/导出
模块3：法律文书AI核心功能

3.1 文书生成

• 模板选择 → 表单填写 → AI生成 → 保存 → 导出

3.2 文书审查

• 上传/粘贴 → AI审查 → 风险点（高/中/低） → 修改建议

3.3 基于向量库的智能引用

• 生成/审查时自动匹配：相关法条、相似案例、风险条款
模块4：向量数据库系统（核心开发点）

4.1 公共法律向量库（全自动）

4.1.1 目录规则
./data/public_law/
   民法典.docx
   刑法.docx
   劳动合同法.docx
   民事诉讼法.docx
   司法解释/
      民间借贷司法解释.docx
      劳动争议司法解释.docx
4.1.2 向量库构建逻辑

1. 递归读取 ./data/public_law/ 下所有 .doc/.docx/.pdf

2. 提取文本 → 分块（128~256字/块）

3. 生成Embedding

4. 存入Chroma：public_law 集合

5. 记录每个文件的：

◦ file_path

◦ file_hash

◦ law_name（法律名称）

◦ chunk_ids（对应的向量块ID）

4.1.3 支持两种更新模式

模式A：全量重建（适合批量更新法条）

触发条件：

• 新增/删除/替换多部法律
操作：

1. 删除公共向量库集合

2. 重新扫描全部法条文件

3. 全部重新向量化

4. 更新完成记录时间

界面按钮：【重建公共法律向量库】

模式B：单文件增量更新（只更新某一部法律）

触发条件：

• 仅《民法典》更新

• 仅《劳动合同法》更新
操作：

1. 用户选择目标文件（如民法典.docx）

2. 系统根据文件路径/哈希查找旧向量块

3. 删除旧向量（仅该文件相关）

4. 解析新文件 → 分块 → 生成新向量

5. 插入到公共库

6. 完成增量更新

界面按钮：【单文件更新法条向量】

4.2 用户私有向量库

• 每个用户独立隔离

• 可上传个人文书/案例/证据材料

• 支持单文件上传、单文件删除、单文件更新向量

• 检索仅返回自己的内容

4.3 向量检索功能

• 语义检索：输入问题 → 匹配最相关法条/文书

• 文书生成时自动引用法条

• 审查时自动匹配风险依据
模块5：文件资产与协作系统

5.1 功能

• 我的文书列表

• 版本管理（每次修改自动保存）

• 共享给我（他人授权的文件）

• 我共享的（我授权给他人的文件）

• 权限：只读/可编辑

• 导出Word/PDF

5.2 共享逻辑

• 所有者可随时撤销权限

• 编辑者修改会产生新版本

• 所有操作写入日志
模块6：系统设置与本地管理

• 法条目录路径配置

• 向量库存储路径

• 导出默认目录

• 数据备份/恢复

• 模型参数（Embedding/LLM）

• 日志查看
四、数据库设计（SQLite）

1. sys_user（用户）

user_id, username, password, create_time

2. legal_doc（文书）

doc_id, user_id, title, content, doc_type, create_time, update_time

3. doc_version（版本）

version_id, doc_id, content, operator_id, create_time

4. doc_permission（文件授权）

id, doc_id, owner_id, to_user_id, permission(1=read 2=write), create_time

5. public_law_files（公共法律文件索引）

id, file_name, file_path, file_hash, law_name, status, chunk_count, update_time

6. vector_log（向量库操作日志）

id, operate_type(rebuild/update/delete), file_path, operator, create_time

7. operation_log（用户操作日志）

id, user_id, action, target_type, target_id, create_time
五、向量库元数据设计（Chroma）

每个向量块带以下元数据，用于精准删除、更新、检索
metadata = {
    "library": "public",
    "file_path": "./data/public_law/民法典.docx",
    "law_name": "民法典",
    "file_hash": "xxxx",
    "chunk_index": 3
}
单文件更新依靠：file_path + law_name 定位删除
六、核心接口设计（完整）

用户

• /api/user/register

• /api/user/login

文书

• /api/doc/list

• /api/doc/detail

• /api/doc/save

• /api/doc/version/list

授权
• /api/permission/share
• /api/permission/revoke
• /api/permission/shared_to_me

向量库（最关键）

• /api/vector/public/info

• /api/vector/public/rebuild

• /api/vector/public/update_single

• /api/vector/public/delete_file

• /api/vector/search

• /api/vector/private/upload

文书AI

• /api/ai/generate

• /api/ai/review

导出

• /api/export/word

• /api/export/pdf
七、向量库更新流程（开发标准流程）

7.1 全量重建公共库

1. 界面点击【重建公共向量库】

2. 后端清空 Chroma 的 public_law 集合

3. 遍历 ./data/public_law/ 所有法律文件

4. 解析文本 → 分块 → 生成Embedding

5. 插入向量与元数据

6. 更新 public_law_files 表

7. 返回成功

7.2 单文件增量更新（你重点要求）

1. 界面选择一个法律文件（如民法典.docx）

2. 后端根据 file_path 查询元数据

3. 根据 metadata 删除该文件所有旧向量

4. 读取最新文件内容

5. 分块、向量化、插入

6. 更新 public_law_files 记录

7. 完成（仅更新该法律，不影响其他法条）
八、部署与打包（Windows本地）

8.1 目录结构
legal_ai/
├── main.py                # 启动器(GUI+FastAPI)
├── gui/                   # PyQt6界面
├── api/                   # 接口服务
├── core/                  # 配置/LLM/Embedding
├── service/
│   ├── doc_service.py
│   ├── vector_service.py  # 向量核心
│   └── law_service.py     # 法条解析
├── data/
│   └── public_law/        # 法条自动读取目录
├── vector_db/
│   ├── public/            # 公共向量库
│   └── user_xxx/          # 用户私有向量库
├── db/
│   └── app.db             # SQLite
└── requirements.txt
8.2 打包

使用 PyInstaller 打包为单文件夹 EXE，双击运行，无依赖。

按照如下顺序进行开发
1. 基础环境 + GUI框架
2. 用户系统 + 权限隔离
3. 文书生成/审查/保存/版本/导出
4. 公共法律向量库 + 单文件增量更新
5. 私有向量库 + 检索
6. 文件共享与授权
7. 日志、备份、设置
8. 打包Windows版本


