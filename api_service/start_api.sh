#!/bin/bash
# MOSS-TTS-Nano API Service 启动脚本

set -e

# 配置变量
SERVICE_NAME="moss-tts-nano-api"
WORK_DIR="/home/brookli/MOSS-TTS-Nano"
CONDA_ENV="moss-tts-nano"
HOST="0.0.0.0"
PORT="8005"

echo "=========================================="
echo "Starting $SERVICE_NAME"
echo "=========================================="
echo "Working Directory: $WORK_DIR"
echo "Conda Environment: $CONDA_ENV"
echo "Host: $HOST"
echo "Port: $PORT"
echo "=========================================="

# 检查 conda 环境是否存在
if ! conda env list | grep -q "$CONDA_ENV"; then
    echo "Error: Conda environment '$CONDA_ENV' not found!"
    echo "Please create it first: conda create -n $CONDA_ENV python=3.12"
    exit 1
fi

# 激活 conda 环境并启动服务
eval "$(conda shell.bash hook)"
conda activate $CONDA_ENV

# 检查 pydub 是否安装
if ! python -c "import pydub" 2>/dev/null; then
    echo "Installing pydub..."
    pip install pydub
fi

# 检查 ffmpeg 是否安装
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg not found. Please install it:"
    echo "  sudo apt install ffmpeg"
    echo ""
fi

# 进入工作目录
cd $WORK_DIR

# 启动服务
echo "Starting FastAPI server..."
python api_service/moss_tts_api.py
