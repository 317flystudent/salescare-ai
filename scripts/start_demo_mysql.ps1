param(
    [string]$MysqlPassword = "root",
    [string]$MysqlUser = "root",
    [string]$MysqlDatabase = "salescare_ai"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PythonExe = "C:\Users\31719\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$MysqlExe = "E:\xp\phpstudy_pro\Extensions\MySQL8.0.12\bin\mysql.exe"
$MysqldExe = "E:\xp\phpstudy_pro\Extensions\MySQL8.0.12\bin\mysqld.exe"
$MysqldIni = "E:\xp\phpstudy_pro\Extensions\MySQL8.0.12\my.ini"

if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$env:CHATBOT_DB_ENGINE = "mysql"
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = $MysqlUser
$env:MYSQL_PASSWORD = $MysqlPassword
$env:MYSQL_DATABASE = $MysqlDatabase
$env:MYSQL_PWD = $MysqlPassword

if (Test-Path $MysqlExe) {
    & $MysqlExe -u $MysqlUser --default-character-set=utf8mb4 -e "SELECT 1" *> $null
    if ($LASTEXITCODE -ne 0 -and (Test-Path $MysqldExe)) {
        Write-Host "MySQL is not responding. Starting phpStudy MySQL..."
        Start-Process -FilePath $MysqldExe -ArgumentList @("--defaults-file=$MysqldIni") -WorkingDirectory (Split-Path -Parent $MysqldExe) -WindowStyle Hidden
        Start-Sleep -Seconds 5
    }
}

Write-Host "Starting SalesCare AI demo with MySQL database: $MysqlDatabase"
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Keep this window open during the classroom demo. Press Ctrl+C to stop."

Set-Location $ProjectRoot
& $PythonExe "$ProjectRoot\scripts\dev_server.py"
