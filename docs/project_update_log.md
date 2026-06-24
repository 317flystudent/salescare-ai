# 项目更新日志

本日志用于补充课程评分标准中的“项目管理与团队协作”证据，记录项目从需求分析到部署提交的主要迭代。

| 时间 | 阶段 | 更新内容 | 证据 |
| --- | --- | --- | --- |
| 第 1-2 周 | 市场调研与定位 | 明确销售/售后服务场景，选择“悦行智能电动车”作为虚构品牌，确定产品咨询、订单查询、退换货、故障排查、投诉安抚等核心功能 | 报告第 1 章 |
| 第 3 周 | 系统设计 | 确定前后端分离架构，设计前端、后端、数据库、AI 服务分层，规划五张核心业务表 | 报告第 2 章 |
| 第 4-5 周 | AI 核心实现 | 构建 12 条初始知识库，实现意图识别、订单号识别、情绪识别、Top-K 检索、提示词约束和 DeepSeek API 可选接入 | `backend/ai_service.py`, `backend/seed_data.py` |
| 第 6-7 周 | 全栈功能开发 | 完成买家聊天页、商家后台、知识库 CRUD、订单生成、订单查询、人工工单、会话与消息记录 | `frontend/`, `backend/` |
| 第 8 周 | 数据库与课堂演示 | 完成 SQLite/MySQL 双模式，补充 phpStudy、HeidiSQL 和 MySQL 课堂演示流程 | `database/mysql_init.sql`, `docs/classroom_demo.md` |
| 第 9 周 | 公有云部署 | 部署到腾讯云 Ubuntu 服务器，配置 MySQL、systemd 后端服务、Nginx 前端托管与 API 反向代理 | `docs/cloud_deploy_evidence.md` |
| 第 10 周 | 报告与提交 | 生成 Word 报告，补充部署截图、GitHub 仓库截图、README 地址截图，整理开源仓库 | `reports/outputs/`, GitHub 仓库 |

## Git 提交记录

```text
636e005 Initial course project submission
6e048a9 Add repository URL to deliverables
3dbe1a0 Add GitHub evidence screenshots to report
```

后续如继续修改报告或源码，可继续用 `git commit` 留下更新记录。
