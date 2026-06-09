#!/bin/bash

# Course data update script
# This script runs the crawler and redirects output to a log file
# for real-time monitoring via the web interface
# It also manages nginx configuration to show the smart static page during updates

# Configuration
CRAWLER_DIR="/home/deploy/xkB/crawler"
VENV_DIR="/home/deploy/xkB/venv"
NGINX_CONF_XK="/etc/nginx/sites-available/xk"
NGINX_CONF_TONGJI="/etc/nginx/sites-available/flask_vue_app"
NGINX_BACKUP_DIR="/tmp/nginx_backup_$(date +%s)"
STATIC_PAGE_DIR="/var/www/shared_pages"

# Function to push log line to Redis Stream
report_log() {
    echo "$1"
    redis-cli -p 6380 XADD crawler:log MAXLEN '~' 5000 '*' msg "$1" > /dev/null 2>&1 || true
}

# Function to write status atomically via Redis SET
write_status() {
    local status="$1"
    local message="${2:-}"
    local start_time="${3:-}"
    local end_time="${4:-}"
    printf '{"status":"%s","message":"%s","startTime":"%s","endTime":"%s"}' \
        "$status" "$message" "$start_time" "$end_time" \
        | redis-cli -p 6380 -x SET crawler:status > /dev/null 2>&1 || true
}

# Function to restore original nginx configs on exit
restore_nginx() {
    if [ -d "$NGINX_BACKUP_DIR" ]; then
        report_log "[$(date '+%Y-%m-%d %H:%M:%S')] 恢复 nginx 配置..."
        sudo cp "$NGINX_BACKUP_DIR/xk" "$NGINX_CONF_XK"
        sudo cp "$NGINX_BACKUP_DIR/flask_vue_app" "$NGINX_CONF_TONGJI"
        sudo nginx -s reload
        rm -rf "$NGINX_BACKUP_DIR"
    fi
}

# Trap to ensure nginx is restored on script exit (even on error)
trap 'restore_nginx' EXIT

# Start fresh — clear old Redis stream data
redis-cli -p 6380 DEL crawler:log crawler:status > /dev/null 2>&1 || true
START_TIME=$(date '+%Y-%m-%dT%H:%M:%S')
report_log "[$(date '+%Y-%m-%d %H:%M:%S')] 开始数据更新任务"

# Write initial status
write_status "running" "正在更新数据..." "$START_TIME" ""

# Create backup directory
mkdir -p "$NGINX_BACKUP_DIR"

# Backup original nginx configs
cp "$NGINX_CONF_XK" "$NGINX_BACKUP_DIR/xk"
cp "$NGINX_CONF_TONGJI" "$NGINX_BACKUP_DIR/flask_vue_app"

report_log "[$(date '+%Y-%m-%d %H:%M:%S')] 切换到更新模式页面..."

# Create update mode nginx config for xk.xialing.icu
cat > /tmp/nginx_xk_update.conf << 'EOF'
server {
    listen 80;
    server_name xk.xialing.icu;

    # Force redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name xk.xialing.icu;

    ssl_certificate /etc/letsencrypt/live/www.xialing.icu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.xialing.icu/privkey.pem;

    root /var/www/shared_pages;
    index index.html;

    # Proxy /api/ to xk backend so the smart page can fetch logs
    location /api/ {
        proxy_pass http://127.0.0.1:1239;
        proxy_buffering off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Serve static files (including our smart update page)
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

# Create update mode nginx config for tongji.xialing.icu
cat > /tmp/nginx_tongji_update.conf << 'EOF'
server {
    listen 80;
    server_name tongji.xialing.icu;

    # redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 80;
    server_name 43.134.174.70;
    return 444;
}

server {
    listen 443 ssl;
    server_name tongji.xialing.icu;

    ssl_certificate /etc/letsencrypt/live/www.xialing.icu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.xialing.icu/privkey.pem;

    # Serve the shared static page during update
    root /var/www/shared_pages;
    index index.html;

    # Proxy /api/ to xk backend (port 1239) since that's where getFetchLog is implemented
    location /api/ {
        proxy_pass http://127.0.0.1:1239;
        proxy_buffering off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Serve static files
    location / {
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 443 ssl;
    server_name 43.134.174.70;
    return 444;
}

server {
    listen 80;
    listen 443 ssl default_server;
    server_name _;
    ssl_certificate /etc/nginx/dummy.crt;
    ssl_certificate_key /etc/nginx/dummy.key;
    return 444;
}
EOF

# Apply update mode configs
sudo cp /tmp/nginx_xk_update.conf "$NGINX_CONF_XK"
sudo cp /tmp/nginx_tongji_update.conf "$NGINX_CONF_TONGJI"

# Test nginx config before reloading
if ! sudo nginx -t 2>/dev/null; then
    report_log "[$(date '+%Y-%m-%d %H:%M:%S')] 错误: nginx 配置测试失败，恢复原配置"
    restore_nginx
    exit 1
fi

# Reload nginx to apply update mode
sudo nginx -s reload
report_log "[$(date '+%Y-%m-%d %H:%M:%S')] 已切换到更新模式，用户将看到实时进度页面"

# Change to crawler directory
cd "$CRAWLER_DIR" || exit 1

# Sync venv with latest requirements
if [ -f "$VENV_DIR/bin/pip" ]; then
    "$VENV_DIR/bin/pip" install -r requirements.txt --quiet
fi

# Run crawler — all output (stdout + stderr) piped to log stream
# Strip \r because SSE protocol treats it as a line separator
if [ -f "$VENV_DIR/bin/python3" ]; then
    "$VENV_DIR/bin/python3" -u fetchCourseList.py 2>&1 | while IFS= read -r line; do
        line="${line//$'\r'/}"
        report_log "$line"
    done
elif [ -f "$VENV_DIR/bin/python" ]; then
    "$VENV_DIR/bin/python" -u fetchCourseList.py 2>&1 | while IFS= read -r line; do
        line="${line//$'\r'/}"
        report_log "$line"
    done
else
    python3 -u fetchCourseList.py 2>&1 | while IFS= read -r line; do
        line="${line//$'\r'/}"
        report_log "$line"
    done
fi

CRAWLER_EXIT_CODE=${PIPESTATUS[0]}

# Check exit status
END_TIME=$(date '+%Y-%m-%dT%H:%M:%S')
if [ $CRAWLER_EXIT_CODE -eq 0 ]; then
    report_log "[$(date '+%Y-%m-%d %H:%M:%S')] 数据更新完成"
else
    report_log "[$(date '+%Y-%m-%d %H:%M:%S')] 数据更新失败 (退出码: $CRAWLER_EXIT_CODE)"
fi

# Mark as completed first so frontend gets the status before nginx is restored
if [ $CRAWLER_EXIT_CODE -eq 0 ]; then
    write_status "completed" "数据更新完成" "$START_TIME" "$END_TIME"
else
    write_status "failed" "数据更新失败 (退出码: $CRAWLER_EXIT_CODE)" "$START_TIME" "$END_TIME"
fi

# Restore original nginx configs immediately — SSE connection is persistent,
# nginx reload preserves existing connections, and frontend es.close() prevents
# reconnection after the completed/failed event.
restore_nginx

# Clean up trap since we've already restored
trap - EXIT

exit $CRAWLER_EXIT_CODE
