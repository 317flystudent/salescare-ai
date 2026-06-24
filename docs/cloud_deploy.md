# 公有云服务器部署步骤

这份文档用于把项目部署到一台 Ubuntu 云服务器，最终得到可填写到报告中的生产环境 URL。

## 1. 购买云服务器

推荐配置：

```text
类型：轻量应用服务器
系统：Ubuntu 22.04 LTS
配置：2 核 2G
硬盘：40G 左右
带宽：3M 或 5M
购买时长：1 个月
```

安全组/防火墙放行：

```text
22    SSH 登录
80    Web 访问
443   HTTPS 备用
```

暂时不要开放 `3306`、`8000`、`5173`。

## 2. 登录服务器

在本机 PowerShell 执行：

```powershell
ssh root@你的服务器公网IP
```

第一次连接输入：

```text
yes
```

然后输入云服务器密码。

## 3. 安装运行环境

登录服务器后执行：

```bash
apt update
apt install -y python3 python3-venv python3-pip nginx mysql-server git unzip
systemctl enable nginx
systemctl enable mysql
```

## 4. 上传项目代码

在本机 PowerShell 中执行，把项目上传到服务器：

```powershell
scp -r E:\dsjhomework root@你的服务器公网IP:/opt/salescare-ai
```

如果上传后目录变成 `/opt/salescare-ai/dsjhomework`，可以在服务器执行：

```bash
mv /opt/salescare-ai/dsjhomework/* /opt/salescare-ai/
```

## 5. 创建 Python 虚拟环境

在服务器执行：

```bash
cd /opt/salescare-ai
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-mysql.txt
```

## 6. 初始化 MySQL

在服务器执行：

```bash
mysql
```

进入 `mysql>` 后执行，注意把密码换成你自己的强密码：

```sql
CREATE DATABASE IF NOT EXISTS salescare_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'salescare'@'localhost' IDENTIFIED BY '换成你的数据库密码';
GRANT ALL PRIVILEGES ON salescare_ai.* TO 'salescare'@'localhost';
FLUSH PRIVILEGES;
SOURCE /opt/salescare-ai/database/mysql_init.sql;
EXIT;
```

## 7. 配置后端环境变量

在服务器执行：

```bash
cat > /etc/salescare-ai.env <<'EOF'
CHATBOT_HOST=127.0.0.1
CHATBOT_PORT=8000
CHATBOT_DB_ENGINE=mysql
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=salescare
MYSQL_PASSWORD=换成你的数据库密码
MYSQL_DATABASE=salescare_ai
DEEPSEEK_API_KEY=换成你的DeepSeekKey
DEEPSEEK_MODEL=deepseek-chat
EOF
chmod 600 /etc/salescare-ai.env
```

不要把 DeepSeek Key 写进代码仓库。

## 8. 配置 systemd 后台服务

在服务器执行：

```bash
cat > /etc/systemd/system/salescare-ai.service <<'EOF'
[Unit]
Description=SalesCare AI backend
After=network.target mysql.service

[Service]
WorkingDirectory=/opt/salescare-ai
EnvironmentFile=/etc/salescare-ai.env
ExecStart=/opt/salescare-ai/.venv/bin/python /opt/salescare-ai/backend/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable salescare-ai
systemctl restart salescare-ai
systemctl status salescare-ai --no-pager
```

看到 `active (running)` 就说明后端启动成功。

## 9. 配置 Nginx

在服务器执行：

```bash
cat > /etc/nginx/sites-available/salescare-ai <<'EOF'
server {
    listen 80;
    server_name _;

    root /opt/salescare-ai/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/salescare-ai /etc/nginx/sites-enabled/salescare-ai
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

## 10. 验证公网 URL

在浏览器打开：

```text
http://你的服务器公网IP
```

再测试接口：

```text
http://你的服务器公网IP/api/health
```

如果页面能打开，`/api/health` 返回 `ok: true`，报告里的生产环境 URL 就填写：

```text
http://你的服务器公网IP
```

## 11. 常用维护命令

查看后端状态：

```bash
systemctl status salescare-ai --no-pager
```

查看后端日志：

```bash
journalctl -u salescare-ai -n 100 --no-pager
```

重启后端：

```bash
systemctl restart salescare-ai
```

重新导入数据库：

```bash
mysql -u salescare -p --default-character-set=utf8mb4 salescare_ai < /opt/salescare-ai/database/mysql_init.sql
```

## 12. 如果无法访问

优先检查：

```bash
systemctl status nginx --no-pager
systemctl status salescare-ai --no-pager
ss -lntp | grep -E ':80|:8000|:3306'
```

同时确认云控制台安全组已经放行 `80` 端口。
