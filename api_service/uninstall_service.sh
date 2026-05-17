#!/bin/bash
# MOSS-TTS-Nano API Service - Systemd 卸载脚本

set -e

SERVICE_NAME="moss-tts-nano-api"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=========================================="
echo "Uninstalling $SERVICE_NAME service"
echo "=========================================="

# 检查是否有 root 权限
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

# 停止服务
echo "Stopping service..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true

# 禁用服务
echo "Disabling service..."
systemctl disable "$SERVICE_NAME" 2>/dev/null || true

# 删除服务文件
echo "Removing service file..."
rm -f "$SERVICE_FILE"

# 重新加载 systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "✓ Service uninstalled successfully"
