# 悦行销售/售后 AI 聊天机器人

这是《大数据机器学习》课程作业的全栈项目实现，面向“销售（售后）服务”场景。项目采用前后端分离结构：

- `frontend/`：响应式电商售后聊天界面、知识库管理和演示订单面板，原生 HTML/CSS/JavaScript 实现。
- `backend/`：Python 标准库 HTTP API、SQLite/MySQL 持久化、演示订单生成、知识库检索、意图识别、DeepSeek 大模型代理。
- `reports/`：项目报告生成脚本与最终 Word 报告。

## 项目地址

- Web 应用生产环境 URL：<http://1.14.184.75>
- 开源代码仓库地址：上传 GitHub/Gitee 后在这里补充。

## 本地运行

最省事的方式是一条命令同时启动前后端：

```powershell
& "C:\Users\31719\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/dev_server.py
```

浏览器访问：

```text
http://127.0.0.1:5173
```

也可以分开启动。

启动后端 API：

```powershell
& "C:\Users\31719\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" backend/server.py
```

另开一个终端启动前端静态服务：

```powershell
& "C:\Users\31719\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m http.server 5173 -d frontend
```

浏览器访问：

```text
http://127.0.0.1:5173
```

后端默认地址：

```text
http://127.0.0.1:8000
```

## 接入 DeepSeek

如果配置了 `DEEPSEEK_API_KEY`，机器人会把检索到的知识库片段、对话上下文和系统提示词一起发送给 DeepSeek。未配置时，会自动使用本地检索式回答，便于课堂演示。

PowerShell 示例：

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
$env:DEEPSEEK_MODEL="deepseek-chat"
& "C:\Users\31719\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" backend/server.py
```

可选环境变量：

```text
CHATBOT_HOST=127.0.0.1
CHATBOT_PORT=8000
CHATBOT_DB=data/salescare.db
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=15
```

## API 摘要

- `GET /api/health`：服务健康检查。
- `POST /api/chat`：发送用户消息并返回机器人回复。
- `GET /api/knowledge`：查看知识库。
- `POST /api/knowledge`：新增知识库条目。
- `PUT /api/knowledge/{id}`：更新知识库条目。
- `DELETE /api/knowledge/{id}`：删除知识库条目。
- `GET /api/demo-orders`：查看演示订单和可选商品。
- `POST /api/demo-orders/create`：随机生成课堂演示订单。
- `GET /api/handoff-tickets`：查看人工客服工单。
- `POST /api/handoff-tickets/create`：创建人工客服工单。
- `GET /api/sessions`：查看会话列表。
- `GET /api/sessions/{session_id}/messages`：查看指定会话历史。

## 后续需要你补充

- 开源代码仓库地址：上传 GitHub/Gitee 后，把仓库地址填入报告首页。
- 大模型 API Key：演示真实大模型回答时，需要你自行申请并在环境变量中配置。

## 公有云部署

如果需要填写“Web 应用生产环境 URL”，请按 [公有云服务器部署步骤](docs/cloud_deploy.md) 操作。部署完成后，生产环境 URL 通常是：

```text
http://你的服务器公网IP
```

本项目当前部署验收记录见：[公有云部署验收记录](docs/cloud_deploy_evidence.md)。

## MySQL 课堂演示

如果老师要查看 MySQL 表和现场对话写入记录，请按 [课堂演示流程](docs/classroom_demo.md) 操作。

课堂现场推荐直接运行：

```cmd
E:\dsjhomework\scripts\start_demo_mysql.cmd
```

这个脚本会先检查 phpStudy MySQL，未启动时会自动尝试拉起 `MySQL8.0.12`，再启动前后端服务。

然后访问：

```text
http://127.0.0.1:5173
```

如果 phpStudy 自带的 MySQL-Front 报兼容错误，可以用下面脚本直接展示 MySQL 中的五张核心表：

```powershell
powershell -ExecutionPolicy Bypass -File E:\dsjhomework\scripts\show_demo_database.ps1
```

核心步骤：

```powershell
mysql -u root -p --default-character-set=utf8mb4
```

进入 `mysql>` 后执行：

```sql
SOURCE E:/dsjhomework/database/mysql_init.sql;
USE salescare_ai;
SHOW TABLES;
SELECT COUNT(*) AS knowledge_count FROM knowledge_base;
```

五张核心表：

```text
knowledge_base：销售/售后知识库
demo_orders：课堂演示订单
handoff_tickets：人工客服工单
sessions：用户会话
messages：用户和机器人消息记录
```

如需手动用 MySQL 模式启动：

```powershell
& "C:\Users\31719\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install -r requirements-mysql.txt
$env:CHATBOT_DB_ENGINE="mysql"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="你的MySQL密码"
$env:MYSQL_DATABASE="salescare_ai"
& "C:\Users\31719\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/dev_server.py
```
