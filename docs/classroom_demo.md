# 课堂演示流程

## 课前准备

优先推荐课堂使用 phpStudy 的数据库工具查看 MySQL，具体步骤见：

```text
E:\dsjhomework\docs\phpstudy_demo.md
```

1. 打开 MySQL，导入数据库脚本。

PowerShell 不支持 `mysql -u root -p < file.sql` 这种写法。推荐进入 MySQL 后用 `SOURCE` 导入：

```powershell
mysql -u root -p --default-character-set=utf8mb4
```

输入密码后，在 `mysql>` 提示符里执行：

```sql
SOURCE E:/dsjhomework/database/mysql_init.sql;
USE salescare_ai;
SHOW TABLES;
SELECT COUNT(*) AS knowledge_count FROM knowledge_base;
```

也可以用 CMD 的重定向语法导入：

```powershell
cmd /c "mysql -u root -p --default-character-set=utf8mb4 < E:\dsjhomework\database\mysql_init.sql"
```

如果 `mysql` 命令不可用，可以在 MySQL Workbench 中打开 `E:\dsjhomework\database\mysql_init.sql`，点击执行。

2. 安装 MySQL Python 驱动。

```powershell
& "C:\Users\31719\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install -r requirements-mysql.txt
```

3. 用 MySQL 模式启动项目。

```powershell
$env:CHATBOT_DB_ENGINE="mysql"
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="你的MySQL密码"
$env:MYSQL_DATABASE="salescare_ai"
& "C:\Users\31719\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/dev_server.py
```

4. 打开浏览器访问：

```text
http://127.0.0.1:5173
```

## 老师查看 MySQL 时怎么讲

建议先展示五张核心表：

```sql
USE salescare_ai;
SHOW TABLES;
SELECT COUNT(*) AS knowledge_count FROM knowledge_base;
SELECT id, category, title FROM knowledge_base ORDER BY id;
SELECT order_no, product_name, status, logistics_status, aftersale_status
FROM demo_orders
ORDER BY updated_at DESC
LIMIT 10;
SELECT ticket_no, priority, status, assigned_team, LEFT(reason, 80) AS reason_preview, updated_at
FROM handoff_tickets
ORDER BY updated_at DESC
LIMIT 10;
SELECT id, channel, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT 5;
SELECT id, session_id, role, intent, LEFT(content, 80) AS content_preview, created_at
FROM messages
ORDER BY id DESC
LIMIT 10;
```

讲解口径：

- `knowledge_base` 是销售/售后知识库，包含分类、标题、标准问题、标准答案和关键词。
- `demo_orders` 保存课堂演示订单，机器人识别订单号后返回商品、付款、物流和售后状态。
- `handoff_tickets` 保存转人工工单，包含工单号、优先级、状态、处理小组和预计响应时间。
- `sessions` 保存每次用户会话，便于追踪一次完整客服过程。
- `messages` 保存用户和机器人消息，机器人回答还会记录识别出的意图和知识库来源。

## 现场对话演示脚本

演示顺序建议控制在 5 到 8 分钟。

先说明页面分成两个角色：

- 买家页：默认进入，只有正常的查询聊天、自助入口和转人工。
- 商家后台：点击右上角“商家后台”进入，可查看订单汇总、买家订单信息、知识库、会话和工单。

1. 产品咨询

用户输入：

```text
悦行 S1 和 Pro 有什么区别？
```

讲解重点：机器人能回答车型差异、续航和适用人群，体现销售咨询场景。

2. 售后保修

用户输入：

```text
电池保修多久？
```

讲解重点：机器人识别为“保修政策”，回答引用知识库中的电池、电机、控制器保修周期。

3. 故障排查

用户输入：

```text
我的车无法启动，应该怎么排查？
```

讲解重点：机器人不是简单聊天，而是给出步骤化排查：电量、空气开关、刹车把、NFC、仪表提示。

4. 情绪安抚

用户输入：

```text
我很生气，维修太慢了，怎么处理？
```

讲解重点：机器人识别负面情绪，先安抚，再建议转人工和保留凭证。

5. 转人工工单

用户输入：

```text
我要转人工，维修太慢了，想找人工客服
```

讲解重点：机器人会生成 `RG` 开头的人工工单号，右侧“工单”页签会显示排队状态、优先级、处理小组和预计响应时间。

6. 商家后台查看订单汇总

点击右上角“商家后台”，打开“概览”页。

讲解重点：后台与买家页分开，商家可以看到订单总数、演示成交额、售后相关订单、待处理工单、会话数量，以及买家订单明细表。

7. 现场查看数据库变化

在 MySQL 执行：

```sql
SELECT order_no, product_name, status, logistics_status, aftersale_status
FROM demo_orders
ORDER BY updated_at DESC
LIMIT 10;

SELECT id, session_id, role, intent, LEFT(content, 100) AS content_preview, created_at
FROM messages
ORDER BY id DESC
LIMIT 12;

SELECT ticket_no, customer_name, priority, status, assigned_team, LEFT(reason, 100) AS reason_preview, updated_at
FROM handoff_tickets
ORDER BY updated_at DESC
LIMIT 10;
```

讲解重点：现场对话、订单状态和人工工单已经持久化到 MySQL，说明系统不是静态页面，而是完整的前端、后端、数据库闭环。

## 答辩时的高分说法

- 本项目采用前后端分离架构，前端负责交互，后端负责会话、知识库、AI 代理和数据库持久化。
- AI 核心不是简单调用接口，而是先做意图识别和知识库 Top-K 检索，再把检索片段放入提示词，降低大模型幻觉。
- 如果没有 DeepSeek API Key，系统会使用本地检索兜底，保证课堂现场稳定演示。
- 如果配置 `DEEPSEEK_API_KEY`，系统会切换为真实大模型回答，并保留相同的知识库约束和边界意识。
- MySQL 中的 `messages` 表可以证明每轮对话都有持久化，`metadata_json` 中保留了来源和模型模式，方便后续分析客服质量。

## 常见老师提问与回答

问：为什么要做知识库，不直接问大模型？

答：销售和售后政策必须准确，不能让模型自由编造。知识库可以提供稳定依据，大模型负责组织语言和改善表达。

问：用户问到系统不知道的问题怎么办？

答：提示词要求机器人说明不确定，并引导用户补充车型、订单号、城市或故障图片；涉及安全、质量争议或强烈不满时升级人工客服。

问：数据库如何体现项目完整性？

答：`knowledge_base` 体现知识管理，`demo_orders` 体现订单业务数据，`handoff_tickets` 体现转人工工单，`sessions` 体现会话管理，`messages` 体现对话历史和 AI 识别结果，五类数据共同构成客服系统的数据闭环。

问：如果 DeepSeek API 不可用怎么办？

答：系统有本地检索兜底策略，仍可根据知识库返回标准客服答案，保证演示和基础业务可用。
