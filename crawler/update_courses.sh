#!/bin/bash

# Course data update script
# This script runs the crawler and redirects output to a log file
# for real-time monitoring via the web interface
# It also manages nginx configuration to show the smart static page during updates

# Configuration
LOG_FILE="/tmp/crawler_fetch.log"
CRAWLER_DIR="/home/deploy/xkB/crawler"
VENV_DIR="/home/deploy/xkB/venv"
NGINX_CONF_XK="/etc/nginx/sites-available/xk"
NGINX_CONF_TONGJI="/etc/nginx/sites-available/flask_vue_app"
NGINX_BACKUP_DIR="/tmp/nginx_backup_$(date +%s)"
STATIC_PAGE_DIR="/var/www/shared_pages"

# Function to restore original nginx configs on exit
restore_nginx() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    if [ -d "$NGINX_BACKUP_DIR" ]; then
        echo "[$timestamp] 恢复 nginx 配置..." >> "$LOG_FILE"
        sudo cp "$NGINX_BACKUP_DIR/xk" "$NGINX_CONF_XK"
        sudo cp "$NGINX_BACKUP_DIR/flask_vue_app" "$NGINX_CONF_TONGJI"
        sudo nginx -s reload
        rm -rf "$NGINX_BACKUP_DIR"
    fi
}

# Trap to ensure nginx is restored on script exit (even on error)
trap 'restore_nginx' EXIT

# Clear old log and start fresh
> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始数据更新任务" >> "$LOG_FILE"

# Create backup directory
mkdir -p "$NGINX_BACKUP_DIR"

# Backup original nginx configs
cp "$NGINX_CONF_XK" "$NGINX_BACKUP_DIR/xk"
cp "$NGINX_CONF_TONGJI" "$NGINX_BACKUP_DIR/flask_vue_app"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 切换到更新模式页面..." >> "$LOG_FILE"

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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误: nginx 配置测试失败，恢复原配置" >> "$LOG_FILE"
    restore_nginx
    exit 1
fi

# Reload nginx to apply update mode
sudo nginx -s reload
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 已切换到更新模式，用户将看到实时进度页面" >> "$LOG_FILE"

# Change to crawler directory
cd "$CRAWLER_DIR" || exit 1

# Run crawler using venv python directly with unbuffered output for real-time logging
if [ -f "$VENV_DIR/bin/python3" ]; then
    "$VENV_DIR/bin/python3" -u fetchCourseList.py >> "$LOG_FILE" 2>&1
elif [ -f "$VENV_DIR/bin/python" ]; then
    "$VENV_DIR/bin/python" -u fetchCourseList.py >> "$LOG_FILE" 2>&1
else
    # Fallback to system python3
    python3 -u fetchCourseList.py >> "$LOG_FILE" 2>&1
fi

CRAWLER_EXIT_CODE=$?

# Check exit status
if [ $CRAWLER_EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 数据更新完成" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 数据更新失败 (退出码: $CRAWLER_EXIT_CODE)" >> "$LOG_FILE"
fi

# Wait a moment so users can see the final status
sleep 5

# Restore original nginx configs (the trap will also call this, but we do it explicitly here)
restore_nginx

# Clean up trap since we've already restored
trap - EXIT

exit $CRAWLER_EXIT_CODE
