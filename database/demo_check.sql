USE salescare_ai;

SHOW TABLES;

SELECT COUNT(*) AS knowledge_count
FROM knowledge_base;

SELECT id, category, title
FROM knowledge_base
ORDER BY id;

SELECT id, channel, created_at, updated_at
FROM sessions
ORDER BY updated_at DESC
LIMIT 5;

SELECT
    id,
    session_id,
    role,
    intent,
    LEFT(content, 100) AS content_preview,
    created_at
FROM messages
ORDER BY id DESC
LIMIT 12;

SELECT
    order_no,
    product_name,
    status,
    logistics_status,
    aftersale_status,
    amount,
    city,
    updated_at
FROM demo_orders
ORDER BY updated_at DESC
LIMIT 10;

SELECT
    ticket_no,
    customer_name,
    priority,
    status,
    assigned_team,
    LEFT(reason, 100) AS reason_preview,
    expected_response,
    updated_at
FROM handoff_tickets
ORDER BY updated_at DESC
LIMIT 10;
