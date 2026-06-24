@echo off
setlocal

set CHATBOT_DB_ENGINE=mysql
set MYSQL_HOST=127.0.0.1
set MYSQL_PORT=3306
set MYSQL_USER=root
set MYSQL_PASSWORD=root
set MYSQL_DATABASE=salescare_ai
set MYSQL_EXE=E:\xp\phpstudy_pro\Extensions\MySQL8.0.12\bin\mysql.exe
set MYSQLD_EXE=E:\xp\phpstudy_pro\Extensions\MySQL8.0.12\bin\mysqld.exe
set MYSQLD_INI=E:\xp\phpstudy_pro\Extensions\MySQL8.0.12\my.ini
set MYSQL_PWD=%MYSQL_PASSWORD%

cd /d E:\dsjhomework

if exist "%MYSQL_EXE%" (
  "%MYSQL_EXE%" -u %MYSQL_USER% --default-character-set=utf8mb4 -e "SELECT 1" >nul 2>nul
  if errorlevel 1 (
    echo MySQL is not responding. Starting phpStudy MySQL...
    if exist "%MYSQLD_EXE%" (
      start "" /min "%MYSQLD_EXE%" --defaults-file="%MYSQLD_INI%"
      timeout /t 5 /nobreak >nul
    )
  )
)

echo Starting SalesCare AI demo with MySQL database: %MYSQL_DATABASE%
echo Frontend: http://127.0.0.1:5173
echo Backend:  http://127.0.0.1:8000
echo Keep this window open during the classroom demo. Press Ctrl+C to stop.

"C:\Users\31719\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "E:\dsjhomework\scripts\dev_server.py"
