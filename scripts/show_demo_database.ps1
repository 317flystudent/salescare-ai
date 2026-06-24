param(
    [string]$MysqlPassword = "root",
    [string]$MysqlUser = "root",
    [string]$MysqlExe = "E:\xp\phpstudy_pro\Extensions\MySQL8.0.12\bin\mysql.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $MysqlExe)) {
    throw "MySQL client was not found: $MysqlExe"
}

$env:MYSQL_PWD = $MysqlPassword

Write-Host ""
Write-Host "=== Databases and Tables ==="
& $MysqlExe -u $MysqlUser --default-character-set=utf8mb4 -e "USE salescare_ai; SHOW TABLES;"

Write-Host ""
Write-Host "=== Knowledge Base Count ==="
& $MysqlExe -u $MysqlUser --default-character-set=utf8mb4 -e "USE salescare_ai; SELECT COUNT(*) AS knowledge_count FROM knowledge_base;"

Write-Host ""
Write-Host "=== Knowledge Base Items ==="
& $MysqlExe -u $MysqlUser --default-character-set=utf8mb4 -e "USE salescare_ai; SELECT id, category, title FROM knowledge_base ORDER BY id;"

Write-Host ""
Write-Host "=== Demo Orders ==="
& $MysqlExe -u $MysqlUser --default-character-set=utf8mb4 -e "USE salescare_ai; SELECT order_no, product_name, status, logistics_status, aftersale_status, amount, city, updated_at FROM demo_orders ORDER BY updated_at DESC LIMIT 10;"

Write-Host ""
Write-Host "=== Human Handoff Tickets ==="
& $MysqlExe -u $MysqlUser --default-character-set=utf8mb4 -e "USE salescare_ai; SELECT ticket_no, customer_name, priority, status, assigned_team, LEFT(reason, 100) AS reason_preview, expected_response, updated_at FROM handoff_tickets ORDER BY updated_at DESC LIMIT 10;"

Write-Host ""
Write-Host "=== Recent Chat Messages ==="
& $MysqlExe -u $MysqlUser --default-character-set=utf8mb4 -e "USE salescare_ai; SELECT id, session_id, role, intent, LEFT(content, 100) AS content_preview, created_at FROM messages ORDER BY id DESC LIMIT 12;"

Write-Host ""
Write-Host "Refresh this window after a classroom chat by running the same command again."
