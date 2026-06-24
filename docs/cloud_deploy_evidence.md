# 公有云部署验收记录

## 1. 生产环境信息

项目名称：悦行销售/售后 AI 聊天机器人

生产环境 URL：

```text
http://1.14.184.75
```

后端健康检查 URL：

```text
http://1.14.184.75/api/health
```

服务器信息：

```text
云厂商：腾讯云
服务器类型：轻量应用服务器
系统：Ubuntu 22.04 LTS
配置：2 核 CPU / 2GB 内存 / 40GB 系统盘
带宽：3Mbps
公网 IP：1.14.184.75
部署日期：2026-06-24
```

## 2. 服务器软件环境

已安装组件：

```text
Python 3.10.12
Nginx 1.18.0
MySQL 8.0.46
PyMySQL 1.2.0
```

服务器项目目录：

```text
/opt/salescare-ai
```

后端 systemd 服务：

```text
salescare-ai.service
```

## 3. 数据库验收

数据库名称：

```text
salescare_ai
```

核心数据表：

```text
knowledge_base
demo_orders
handoff_tickets
sessions
messages
```

初始化验证结果：

```text
knowledge_base：12 条知识库数据
```

可在服务器执行以下命令复查：

```bash
mysql -u salescare -p --default-character-set=utf8mb4 -e "USE salescare_ai; SHOW TABLES; SELECT COUNT(*) AS knowledge_count FROM knowledge_base;"
```

## 4. 后端服务验收

服务器本机验证命令：

```bash
curl http://127.0.0.1:8000/api/health
```

公网验证命令：

```powershell
Invoke-RestMethod -Uri http://1.14.184.75/api/health
```

公网验证结果：

```json
{"ok":true,"service":"salescare-ai","version":"1.0"}
```

## 5. Nginx 访问验收

Nginx 将公网 80 端口映射为：

```text
/              -> 前端静态页面 /opt/salescare-ai/frontend
/api/          -> 后端服务 http://127.0.0.1:8000/api/
```

浏览器访问：

```text
http://1.14.184.75
```

可看到买家聊天页，右上角可进入商家后台。

## 6. 功能验收清单

建议课堂验收按以下顺序截图或现场演示：

1. 浏览器打开 `http://1.14.184.75`，显示买家聊天页面。
2. 输入产品咨询问题，例如“我预算 3000 以内，女生城市通勤，帮我推荐一辆电动车”。
3. 页面返回 AI 回复，回复标签显示 `DeepSeek`。
4. 点击“商家后台”，查看订单总数、演示成交额、待处理工单、会话数量。
5. 在后台“订单”页生成演示订单。
6. 回到买家页发送订单号，机器人返回付款、物流和售后状态。
7. 点击“转人工”，系统生成 `RG` 开头的人工工单。
8. 在后台“工单”页查看新工单。
9. 在 HeidiSQL 或服务器 MySQL 中查看 `messages`、`demo_orders`、`handoff_tickets` 表。

## 7. 老师检查时可以执行的命令

查看后端运行状态：

```bash
systemctl status salescare-ai --no-pager
```

查看后端日志：

```bash
journalctl -u salescare-ai -n 50 --no-pager
```

查看 Nginx 状态：

```bash
systemctl status nginx --no-pager
```

查看端口：

```bash
ss -lntp | grep -E ':80|:8000|:3306'
```

查看数据库表：

```bash
mysql -u salescare -p --default-character-set=utf8mb4 -e "USE salescare_ai; SHOW TABLES;"
```

## 8. 安全注意事项

以下内容不能放进报告、公开仓库或公开截图：

```text
DeepSeek API Key
数据库密码
服务器登录密码
```

部署时 DeepSeek Key 已保存在服务器环境变量文件：

```text
/etc/salescare-ai.env
```

该文件权限已设置为：

```text
600
```

如果截图中出现 `DEEPSEEK_API_KEY=sk-...`，提交前必须打码。

## 9. 报告填写内容

报告首页可填写：

```text
Web 应用生产环境 URL：http://1.14.184.75
项目开源代码仓库地址：https://github.com/317flystudent/salescare-ai
```
