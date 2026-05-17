#!/bin/bash
# MOSS-TTS-Nano API Service - Systemd 安装脚本

set -e

SERVICE_NAME="moss-tts-nano-api"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_DIR="/home/brookli/MOSS-TTS-Nano"
API_SERVICE_FILE="${PROJECT_DIR}/api_service/moss-tts-nano-api.service"

echo "=========================================="
echo "Installing $SERVICE_NAME as systemd service"
echo "=========================================="

# 检查是否有 root 权限
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

# 复制服务文件
echo "Copying service file..."
cp "$API_SERVICE_FILE" "$SERVICE_FILE"

# 重新加载 systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# 启用服务（开机自启）
echo "Enabling service..."
systemctl enable "$SERVICE_NAME"

# 启动服务
echo "Starting service..."
systemctl start "$SERVICE_NAME"

# 等待服务启动
sleep 3

# 检查服务状态
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo ""
    echo "=========================================="
    echo "✓ Service installed and started successfully!"
    echo "=========================================="
    echo "Service name: $SERVICE_NAME"
    echo "Status: $(systemctl is-active $SERVICE_NAME)"
    echo "API URL: http://localhost:8005"
    echo ""
    echo "Useful commands:"
    echo "  Check status:   systemctl status $SERVICE_NAME"
    echo "  View logs:      journalctl -u $SERVICE_NAME -f"
    echo "  Stop service:   systemctl stop $SERVICE_NAME"
    echo "  Restart:        systemctl restart $SERVICE_NAME"
    echo "  Disable:        systemctl disable $SERVICE_NAME"
    echo "=========================================="
else
    echo ""
    echo "✗ Service failed to start"
    echo "Check logs: journalctl -u $SERVICE_NAME -n 50"
    exit 1
fi
