import json
import random
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import (
    CHATBOT_DB,
    CHATBOT_DB_ENGINE,
    MYSQL_CHARSET,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)
from seed_data import SEED_KNOWLEDGE


DEMO_PRODUCTS = [
    "悦行 S1 城市通勤版",
    "悦行 Pro 家庭长续航版",
    "悦行 Air 轻便版",
]

DEMO_ORDER_STATES = [
    {
        "status": "已付款，仓库拣货中",
        "logistics_status": "预计 24 小时内出库",
        "aftersale_status": "暂未发起售后",
    },
    {
        "status": "已出库，运输中",
        "logistics_status": "已到达华东转运中心，预计明天到达城市网点",
        "aftersale_status": "暂未发起售后",
    },
    {
        "status": "城市网点派送中",
        "logistics_status": "配送员正在联系收货人，预计今天 18:00 前送达",
        "aftersale_status": "暂未发起售后",
    },
    {
        "status": "门店待自提",
        "logistics_status": "车辆已到店，提车码将在核验手机号后发送",
        "aftersale_status": "暂未发起售后",
    },
    {
        "status": "已签收",
        "logistics_status": "订单已完成签收，可在 7 天内按规则申请退换",
        "aftersale_status": "可申请售后",
    },
    {
        "status": "售后处理中",
        "logistics_status": "订单已签收，当前进入售后工单流程",
        "aftersale_status": "门店已受理，预计 2 小时内回访",
    },
]

HANDOFF_TEAMS = {
    "投诉": "投诉关怀组",
    "质量": "质量检测组",
    "安全": "质量检测组",
    "故障": "售后技术组",
    "维修": "售后技术组",
    "订单": "订单与物流组",
    "物流": "订单与物流组",
    "发货": "订单与物流组",
}

SEED_DEMO_ORDERS = [
    {
        "order_no": "YX202606090001",
        "customer_name": "演示客户A",
        "product_name": "悦行 S1 城市通勤版",
        "status": "已出库，运输中",
        "logistics_status": "已到达华东转运中心，预计明天到达城市网点",
        "payment_status": "已支付",
        "aftersale_status": "暂未发起售后",
        "amount": 2699.00,
        "city": "杭州",
    },
    {
        "order_no": "YX202606090002",
        "customer_name": "演示客户B",
        "product_name": "悦行 Pro 家庭长续航版",
        "status": "门店待自提",
        "logistics_status": "车辆已到店，提车码将在核验手机号后发送",
        "payment_status": "已支付",
        "aftersale_status": "暂未发起售后",
        "amount": 3699.00,
        "city": "上海",
    },
    {
        "order_no": "YX202606090003",
        "customer_name": "演示客户C",
        "product_name": "悦行 S1 城市通勤版",
        "status": "售后处理中",
        "logistics_status": "订单已签收，当前进入售后工单流程",
        "payment_status": "已支付",
        "aftersale_status": "门店已受理，预计 2 小时内回访",
        "amount": 2699.00,
        "city": "南京",
    },
]


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def use_mysql():
    return CHATBOT_DB_ENGINE.lower() == "mysql"


def mysql_identifier(name):
    return "`" + name.replace("`", "``") + "`"


def get_pymysql():
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError(
            "MySQL mode requires PyMySQL. Install it with: "
            "python -m pip install pymysql"
        ) from exc
    return pymysql


def get_connection(database=True):
    if use_mysql():
        pymysql = get_pymysql()
        kwargs = {
            "host": MYSQL_HOST,
            "port": MYSQL_PORT,
            "user": MYSQL_USER,
            "password": MYSQL_PASSWORD,
            "charset": MYSQL_CHARSET,
            "autocommit": True,
            "cursorclass": pymysql.cursors.DictCursor,
        }
        if database:
            kwargs["database"] = MYSQL_DATABASE
        return pymysql.connect(**kwargs)

    Path(CHATBOT_DB).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CHATBOT_DB)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return dict(row)
    return {key: row[key] for key in row.keys()}


def init_db():
    if use_mysql():
        init_mysql_db()
    else:
        init_sqlite_db()


def init_sqlite_db():
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                keywords TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                channel TEXT NOT NULL DEFAULT 'web',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                intent TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, created_at);

            CREATE TABLE IF NOT EXISTS demo_orders (
                order_no TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                product_name TEXT NOT NULL,
                status TEXT NOT NULL,
                logistics_status TEXT NOT NULL,
                payment_status TEXT NOT NULL,
                aftersale_status TEXT NOT NULL,
                amount REAL NOT NULL,
                city TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS handoff_tickets (
                ticket_no TEXT PRIMARY KEY,
                session_id TEXT,
                customer_name TEXT NOT NULL,
                reason TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_team TEXT NOT NULL,
                expected_response TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_handoff_tickets_session
                ON handoff_tickets(session_id, updated_at);
            """
        )
        existing = conn.execute("SELECT COUNT(*) AS n FROM knowledge_base").fetchone()["n"]
        if existing == 0:
            now = utc_now()
            conn.executemany(
                """
                INSERT INTO knowledge_base
                    (category, title, question, answer, keywords, updated_at)
                VALUES
                    (:category, :title, :question, :answer, :keywords, :updated_at)
                """,
                [dict(item, updated_at=now) for item in SEED_KNOWLEDGE],
            )
        seed_demo_orders_sqlite(conn)
        conn.commit()
    finally:
        conn.close()


def init_mysql_db():
    db_name = mysql_identifier(MYSQL_DATABASE)
    server_conn = get_connection(database=False)
    try:
        with server_conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS {db_name} "
                f"CHARACTER SET {MYSQL_CHARSET} COLLATE {MYSQL_CHARSET}_unicode_ci"
            )
    finally:
        server_conn.close()

    conn = get_connection(database=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    category VARCHAR(100) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    keywords VARCHAR(500) NOT NULL DEFAULT '',
                    updated_at VARCHAR(40) NOT NULL,
                    UNIQUE KEY uq_knowledge_title (title)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id VARCHAR(64) PRIMARY KEY,
                    channel VARCHAR(40) NOT NULL DEFAULT 'web',
                    created_at VARCHAR(40) NOT NULL,
                    updated_at VARCHAR(40) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    session_id VARCHAR(64) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content LONGTEXT NOT NULL,
                    intent VARCHAR(100),
                    metadata_json LONGTEXT NOT NULL,
                    created_at VARCHAR(40) NOT NULL,
                    INDEX idx_messages_session (session_id, created_at),
                    CONSTRAINT fk_messages_session
                        FOREIGN KEY (session_id) REFERENCES sessions(id)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS demo_orders (
                    order_no VARCHAR(32) PRIMARY KEY,
                    customer_name VARCHAR(80) NOT NULL,
                    product_name VARCHAR(120) NOT NULL,
                    status VARCHAR(80) NOT NULL,
                    logistics_status VARCHAR(255) NOT NULL,
                    payment_status VARCHAR(40) NOT NULL,
                    aftersale_status VARCHAR(120) NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    city VARCHAR(80) NOT NULL,
                    created_at VARCHAR(40) NOT NULL,
                    updated_at VARCHAR(40) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS handoff_tickets (
                    ticket_no VARCHAR(32) PRIMARY KEY,
                    session_id VARCHAR(64),
                    customer_name VARCHAR(80) NOT NULL,
                    reason TEXT NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    status VARCHAR(40) NOT NULL,
                    assigned_team VARCHAR(80) NOT NULL,
                    expected_response VARCHAR(120) NOT NULL,
                    created_at VARCHAR(40) NOT NULL,
                    updated_at VARCHAR(40) NOT NULL,
                    INDEX idx_handoff_tickets_session (session_id, updated_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.execute("SELECT COUNT(*) AS n FROM knowledge_base")
            existing = cur.fetchone()["n"]
            if existing == 0:
                now = utc_now()
                cur.executemany(
                    """
                    INSERT INTO knowledge_base
                        (category, title, question, answer, keywords, updated_at)
                    VALUES
                        (%s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            item["category"],
                            item["title"],
                            item["question"],
                            item["answer"],
                            item["keywords"],
                            now,
                        )
                        for item in SEED_KNOWLEDGE
                    ],
                )
            seed_demo_orders_mysql(cur)
    finally:
        conn.close()


def seed_demo_orders_sqlite(conn):
    now = utc_now()
    for order in SEED_DEMO_ORDERS:
        payload = {**order, "created_at": now, "updated_at": now}
        conn.execute(
            """
            INSERT OR IGNORE INTO demo_orders
                (order_no, customer_name, product_name, status, logistics_status,
                 payment_status, aftersale_status, amount, city, created_at, updated_at)
            VALUES
                (:order_no, :customer_name, :product_name, :status, :logistics_status,
                 :payment_status, :aftersale_status, :amount, :city, :created_at, :updated_at)
            """,
            payload,
        )


def seed_demo_orders_mysql(cur):
    now = utc_now()
    cur.executemany(
        """
        INSERT INTO demo_orders
            (order_no, customer_name, product_name, status, logistics_status,
             payment_status, aftersale_status, amount, city, created_at, updated_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            product_name = VALUES(product_name),
            status = VALUES(status),
            logistics_status = VALUES(logistics_status),
            payment_status = VALUES(payment_status),
            aftersale_status = VALUES(aftersale_status),
            amount = VALUES(amount),
            city = VALUES(city),
            updated_at = VALUES(updated_at)
        """,
        [
            (
                order["order_no"],
                order["customer_name"],
                order["product_name"],
                order["status"],
                order["logistics_status"],
                order["payment_status"],
                order["aftersale_status"],
                order["amount"],
                order["city"],
                now,
                now,
            )
            for order in SEED_DEMO_ORDERS
        ],
    )


def list_demo_products():
    return list(DEMO_PRODUCTS)


def make_demo_order_no():
    today = datetime.now().strftime("%Y%m%d")
    return "YX" + today + str(random.randint(1000, 9999))


def make_handoff_ticket_no():
    today = datetime.now().strftime("%Y%m%d")
    return "RG" + today + str(random.randint(1000, 9999))


def normalize_order_payload(order):
    order = row_to_dict(order)
    if order and "amount" in order:
        order["amount"] = float(order["amount"])
    return order


def normalize_ticket_payload(ticket):
    return row_to_dict(ticket)


def infer_handoff_priority(reason):
    text = reason or ""
    if any(word in text for word in ("投诉", "差评", "生气", "安全", "质量", "多次维修")):
        return "高"
    if any(word in text for word in ("故障", "无法启动", "退款", "退货", "维修")):
        return "中"
    return "普通"


def infer_handoff_team(reason):
    text = reason or ""
    for keyword, team in HANDOFF_TEAMS.items():
        if keyword in text:
            return team
    return "售后升级组"


def get_demo_order(order_no):
    conn = get_connection()
    try:
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT order_no, customer_name, product_name, status,
                           logistics_status, payment_status, aftersale_status,
                           amount, city, created_at, updated_at
                    FROM demo_orders
                    WHERE order_no = %s
                    """,
                    (order_no,),
                )
                return normalize_order_payload(cur.fetchone())
        row = conn.execute(
            """
            SELECT order_no, customer_name, product_name, status,
                   logistics_status, payment_status, aftersale_status,
                   amount, city, created_at, updated_at
            FROM demo_orders
            WHERE order_no = ?
            """,
            (order_no,),
        ).fetchone()
        return normalize_order_payload(row)
    finally:
        conn.close()


def list_demo_orders(limit=10):
    conn = get_connection()
    try:
        sql = """
            SELECT order_no, customer_name, product_name, status,
                   logistics_status, payment_status, aftersale_status,
                   amount, city, created_at, updated_at
            FROM demo_orders
            ORDER BY updated_at DESC
            LIMIT {placeholder}
        """
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(sql.format(placeholder="%s"), (limit,))
                return [normalize_order_payload(row) for row in cur.fetchall()]
        rows = conn.execute(sql.format(placeholder="?"), (limit,)).fetchall()
        return [normalize_order_payload(row) for row in rows]
    finally:
        conn.close()


def create_demo_order(product_name=None):
    product = product_name if product_name in DEMO_PRODUCTS else random.choice(DEMO_PRODUCTS)
    state = random.choice(DEMO_ORDER_STATES)
    city = random.choice(["杭州", "上海", "南京", "苏州", "宁波", "合肥"])
    amount_by_product = {
        "悦行 S1 城市通勤版": 2699.00,
        "悦行 Pro 家庭长续航版": 3699.00,
        "悦行 Air 轻便版": 2199.00,
    }
    now = utc_now()

    conn = get_connection()
    try:
        for _ in range(20):
            order_no = make_demo_order_no()
            if get_demo_order(order_no) is None:
                break
        else:
            order_no = "YX" + datetime.now().strftime("%Y%m%d%H%M%S")

        order = {
            "order_no": order_no,
            "customer_name": "课堂演示客户",
            "product_name": product,
            "status": state["status"],
            "logistics_status": state["logistics_status"],
            "payment_status": "已支付",
            "aftersale_status": state["aftersale_status"],
            "amount": amount_by_product.get(product, 2699.00),
            "city": city,
            "created_at": now,
            "updated_at": now,
        }
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO demo_orders
                        (order_no, customer_name, product_name, status, logistics_status,
                         payment_status, aftersale_status, amount, city, created_at, updated_at)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        order["order_no"],
                        order["customer_name"],
                        order["product_name"],
                        order["status"],
                        order["logistics_status"],
                        order["payment_status"],
                        order["aftersale_status"],
                        order["amount"],
                        order["city"],
                        order["created_at"],
                        order["updated_at"],
                    ),
                )
            return order

        conn.execute(
            """
            INSERT INTO demo_orders
                (order_no, customer_name, product_name, status, logistics_status,
                 payment_status, aftersale_status, amount, city, created_at, updated_at)
            VALUES
                (:order_no, :customer_name, :product_name, :status, :logistics_status,
                 :payment_status, :aftersale_status, :amount, :city, :created_at, :updated_at)
            """,
            order,
        )
        conn.commit()
        return order
    finally:
        conn.close()


def create_handoff_ticket(session_id=None, reason=None, customer_name=None, priority=None):
    now = utc_now()
    reason_text = (reason or "用户请求转人工客服").strip() or "用户请求转人工客服"
    if session_id:
        ensure_session(session_id)
    ticket = {
        "ticket_no": make_handoff_ticket_no(),
        "session_id": session_id or "",
        "customer_name": (customer_name or "课堂演示客户").strip() or "课堂演示客户",
        "reason": reason_text,
        "priority": priority or infer_handoff_priority(reason_text),
        "status": "排队中",
        "assigned_team": infer_handoff_team(reason_text),
        "expected_response": "15 分钟内接入，2 小时内回访处理进度",
        "created_at": now,
        "updated_at": now,
    }

    conn = get_connection()
    try:
        for _ in range(20):
            if use_mysql():
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT ticket_no FROM handoff_tickets WHERE ticket_no = %s",
                        (ticket["ticket_no"],),
                    )
                    exists = cur.fetchone() is not None
            else:
                exists = (
                    conn.execute(
                        "SELECT ticket_no FROM handoff_tickets WHERE ticket_no = ?",
                        (ticket["ticket_no"],),
                    ).fetchone()
                    is not None
                )
            if not exists:
                break
            ticket["ticket_no"] = make_handoff_ticket_no()
        else:
            ticket["ticket_no"] = "RG" + datetime.now().strftime("%Y%m%d%H%M%S")

        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO handoff_tickets
                        (ticket_no, session_id, customer_name, reason, priority, status,
                         assigned_team, expected_response, created_at, updated_at)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        ticket["ticket_no"],
                        ticket["session_id"],
                        ticket["customer_name"],
                        ticket["reason"],
                        ticket["priority"],
                        ticket["status"],
                        ticket["assigned_team"],
                        ticket["expected_response"],
                        ticket["created_at"],
                        ticket["updated_at"],
                    ),
                )
            return ticket

        conn.execute(
            """
            INSERT INTO handoff_tickets
                (ticket_no, session_id, customer_name, reason, priority, status,
                 assigned_team, expected_response, created_at, updated_at)
            VALUES
                (:ticket_no, :session_id, :customer_name, :reason, :priority, :status,
                 :assigned_team, :expected_response, :created_at, :updated_at)
            """,
            ticket,
        )
        conn.commit()
        return ticket
    finally:
        conn.close()


def list_handoff_tickets(limit=20):
    conn = get_connection()
    try:
        sql = """
            SELECT ticket_no, session_id, customer_name, reason, priority, status,
                   assigned_team, expected_response, created_at, updated_at
            FROM handoff_tickets
            ORDER BY updated_at DESC
            LIMIT {placeholder}
        """
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(sql.format(placeholder="%s"), (limit,))
                return [normalize_ticket_payload(row) for row in cur.fetchall()]
        rows = conn.execute(sql.format(placeholder="?"), (limit,)).fetchall()
        return [normalize_ticket_payload(row) for row in rows]
    finally:
        conn.close()


def list_knowledge():
    conn = get_connection()
    try:
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, category, title, question, answer, keywords, updated_at
                    FROM knowledge_base
                    ORDER BY category, id
                    """
                )
                return [row_to_dict(row) for row in cur.fetchall()]
        rows = conn.execute(
            """
            SELECT id, category, title, question, answer, keywords, updated_at
            FROM knowledge_base
            ORDER BY category, id
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()


def create_knowledge(payload):
    now = utc_now()
    item = {
        "category": payload.get("category", "未分类").strip() or "未分类",
        "title": payload.get("title", "").strip(),
        "question": payload.get("question", "").strip(),
        "answer": payload.get("answer", "").strip(),
        "keywords": payload.get("keywords", "").strip(),
        "updated_at": now,
    }
    if not item["title"] or not item["question"] or not item["answer"]:
        raise ValueError("title, question and answer are required")

    conn = get_connection()
    try:
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO knowledge_base
                        (category, title, question, answer, keywords, updated_at)
                    VALUES
                        (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        item["category"],
                        item["title"],
                        item["question"],
                        item["answer"],
                        item["keywords"],
                        item["updated_at"],
                    ),
                )
                item["id"] = cur.lastrowid
            return item

        cur = conn.execute(
            """
            INSERT INTO knowledge_base
                (category, title, question, answer, keywords, updated_at)
            VALUES
                (:category, :title, :question, :answer, :keywords, :updated_at)
            """,
            item,
        )
        conn.commit()
        item["id"] = cur.lastrowid
        return item
    finally:
        conn.close()


def update_knowledge(item_id, payload):
    current = get_knowledge(item_id)
    if current is None:
        return None
    merged = {**current, **payload, "updated_at": utc_now()}
    for key in ("category", "title", "question", "answer", "keywords"):
        merged[key] = str(merged.get(key, "")).strip()
    if not merged["title"] or not merged["question"] or not merged["answer"]:
        raise ValueError("title, question and answer are required")

    conn = get_connection()
    try:
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE knowledge_base
                    SET category = %s,
                        title = %s,
                        question = %s,
                        answer = %s,
                        keywords = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (
                        merged["category"],
                        merged["title"],
                        merged["question"],
                        merged["answer"],
                        merged["keywords"],
                        merged["updated_at"],
                        item_id,
                    ),
                )
        else:
            conn.execute(
                """
                UPDATE knowledge_base
                SET category = :category,
                    title = :title,
                    question = :question,
                    answer = :answer,
                    keywords = :keywords,
                    updated_at = :updated_at
                WHERE id = :id
                """,
                merged,
            )
            conn.commit()
    finally:
        conn.close()
    return get_knowledge(item_id)


def get_knowledge(item_id):
    conn = get_connection()
    try:
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, category, title, question, answer, keywords, updated_at
                    FROM knowledge_base
                    WHERE id = %s
                    """,
                    (item_id,),
                )
                return row_to_dict(cur.fetchone())
        row = conn.execute(
            """
            SELECT id, category, title, question, answer, keywords, updated_at
            FROM knowledge_base
            WHERE id = ?
            """,
            (item_id,),
        ).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def delete_knowledge(item_id):
    conn = get_connection()
    try:
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute("DELETE FROM knowledge_base WHERE id = %s", (item_id,))
                return cur.rowcount > 0
        cur = conn.execute("DELETE FROM knowledge_base WHERE id = ?", (item_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def ensure_session(session_id=None):
    candidate = session_id or str(uuid.uuid4())
    now = utc_now()
    conn = get_connection()
    try:
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM sessions WHERE id = %s", (candidate,))
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        """
                        INSERT INTO sessions (id, channel, created_at, updated_at)
                        VALUES (%s, 'web', %s, %s)
                        """,
                        (candidate, now, now),
                    )
                else:
                    cur.execute(
                        "UPDATE sessions SET updated_at = %s WHERE id = %s",
                        (now, candidate),
                    )
            return candidate

        row = conn.execute("SELECT id FROM sessions WHERE id = ?", (candidate,)).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO sessions (id, channel, created_at, updated_at)
                VALUES (?, 'web', ?, ?)
                """,
                (candidate, now, now),
            )
        else:
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, candidate),
            )
        conn.commit()
        return candidate
    finally:
        conn.close()


def save_message(session_id, role, content, intent=None, metadata=None):
    now = utc_now()
    ensure_session(session_id)
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
    conn = get_connection()
    try:
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages
                        (session_id, role, content, intent, metadata_json, created_at)
                    VALUES
                        (%s, %s, %s, %s, %s, %s)
                    """,
                    (session_id, role, content, intent, metadata_json, now),
                )
                cur.execute(
                    "UPDATE sessions SET updated_at = %s WHERE id = %s",
                    (now, session_id),
                )
                return cur.lastrowid

        cur = conn.execute(
            """
            INSERT INTO messages
                (session_id, role, content, intent, metadata_json, created_at)
            VALUES
                (?, ?, ?, ?, ?, ?)
            """,
            (session_id, role, content, intent, metadata_json, now),
        )
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_sessions(limit=20):
    conn = get_connection()
    try:
        sql = """
            SELECT
                s.id,
                s.channel,
                s.created_at,
                s.updated_at,
                COUNT(m.id) AS message_count,
                MAX(CASE WHEN m.role = 'user' THEN m.content END) AS last_user_message
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            GROUP BY s.id, s.channel, s.created_at, s.updated_at
            ORDER BY s.updated_at DESC
            LIMIT {placeholder}
        """
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(sql.format(placeholder="%s"), (limit,))
                return [row_to_dict(row) for row in cur.fetchall()]
        rows = conn.execute(sql.format(placeholder="?"), (limit,)).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()


def list_messages(session_id, limit=100):
    conn = get_connection()
    try:
        sql = """
            SELECT id, session_id, role, content, intent, metadata_json, created_at
            FROM messages
            WHERE session_id = {session_placeholder}
            ORDER BY id ASC
            LIMIT {limit_placeholder}
        """
        if use_mysql():
            with conn.cursor() as cur:
                cur.execute(
                    sql.format(session_placeholder="%s", limit_placeholder="%s"),
                    (session_id, limit),
                )
                rows = cur.fetchall()
        else:
            rows = conn.execute(
                sql.format(session_placeholder="?", limit_placeholder="?"),
                (session_id, limit),
            ).fetchall()

        messages = []
        for row in rows:
            item = row_to_dict(row)
            item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
            messages.append(item)
        return messages
    finally:
        conn.close()


def recent_messages(session_id, limit=8):
    messages = list_messages(session_id, limit=200)
    return messages[-limit:]
