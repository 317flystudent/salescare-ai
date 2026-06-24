# phpStudy 课堂演示流程

这份流程用于课堂现场演示：程序负责聊天，phpStudy 的数据库工具负责给老师查看 MySQL 表和聊天记录。

## 课前确认

1. 打开 phpStudy，启动 `MySQL8.0.12`。
2. 在 phpStudy 的数据库工具中连接 MySQL。
   - 主机：`127.0.0.1`
   - 端口：`3306`
   - 用户：`root`
   - 密码：`root`
3. 选择数据库 `salescare_ai`。
4. 打开 `knowledge_base` 表，确认有 12 条知识库数据。

如果 phpStudy 打开的 MySQL-Front 报 `Internal Program Bug`、`not a valid date and time`，这是 MySQL-Front 5.3 和 MySQL 8 的兼容问题，不是项目数据库损坏。课堂上不要继续纠结这个窗口，直接用下面的查库脚本展示 MySQL：

```powershell
powershell -ExecutionPolicy Bypass -File E:\dsjhomework\scripts\show_demo_database.ps1
```

如果数据库工具支持执行 SQL，可以打开或复制：

```text
E:\dsjhomework\database\demo_check.sql
```

重点看五张表：

- `knowledge_base`：销售/售后知识库。
- `sessions`：每次聊天会话。
- `messages`：用户和机器人每一轮对话。
- `demo_orders`：课堂演示订单，包含商品、物流、售后状态。
- `handoff_tickets`：转人工客服工单，包含工单号、优先级、状态和处理小组。

## 启动程序

在 PowerShell 中运行：

```powershell
powershell -ExecutionPolicy Bypass -File E:\dsjhomework\scripts\start_demo_mysql.ps1
```

如果 PowerShell 不方便，也可以直接运行：

```text
E:\dsjhomework\scripts\start_demo_mysql.cmd
```

启动脚本会先尝试连接 MySQL；如果 phpStudy 的 MySQL 没有响应，会自动启动 `E:\xp\phpstudy_pro\Extensions\MySQL8.0.12\bin\mysqld.exe`，再启动网页程序。

看到下面地址后，保持这个窗口不要关闭：

```text
http://127.0.0.1:5173
```

浏览器打开这个地址，进入聊天页面。

## 现场演示顺序

1. 先在 phpStudy 数据库工具里展示 `salescare_ai`。
2. 打开 `knowledge_base`，说明已有 12 条业务知识。
3. 打开 `demo_orders`，说明系统准备了课堂演示订单。
4. 打开网页 `http://127.0.0.1:5173`。
5. 先展示买家页：欢迎词、聊天框和 1 到 6 个售后入口。这个页面就是普通买家看到的查询聊天页面。
6. 点击右上角“商家后台”，进入后台管理页。
7. 在后台“概览”里展示买家订单信息和订单信息汇总。
8. 切到后台“订单”，点击“生成演示订单”。
9. 返回买家页，发送订单号，机器人会返回付款、物流、售后状态。
10. 再输入示例问题：

```text
电池保修多久？
```

```text
我的车无法启动，应该怎么排查？
```

```text
我很生气，维修太慢了，怎么处理？
```

11. 点击“转人工”或输入“我要转人工”，展示机器人生成 `RG` 开头的人工工单。
12. 再进入“商家后台”，展示“工单”和“概览”已经刷新。
13. 回到 phpStudy 数据库工具，刷新 `demo_orders`、`handoff_tickets`、`sessions` 和 `messages`。
14. 执行或展示 `database/demo_check.sql`，说明订单、人工工单和现场聊天已经写入 MySQL。

## 给老师看的讲解口径

- 这个系统不是静态网页，前端聊天、后端 API、MySQL 数据库是连起来的。
- 买家页面模拟电商售后客服，进入后先显示欢迎词和自助入口，再由用户选择订单查询、退换货、故障排查等业务。
- 商家后台和买家页面分开，后台可以查看买家订单信息、订单汇总、知识库、会话和转人工工单。
- `knowledge_base` 保存业务知识，机器人回答会优先检索这些内容，减少胡编乱造。
- `demo_orders` 保存演示订单，机器人识别订单号后会返回当前订单状态、物流进度和售后状态。
- `handoff_tickets` 保存人工工单，机器人识别“转人工”后会生成工单号、排队状态、优先级和处理小组。
- `sessions` 保存会话，`messages` 保存每一条聊天消息。
- 现场对话后，`messages` 表会立即新增记录，说明系统具备数据持久化能力。
- 没有配置 DeepSeek API Key 时，系统会用本地检索兜底，课堂演示更稳定。
