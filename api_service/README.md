# MOSS-TTS-Nano API Service

## 快速启动

```bash
# 1. 安装依赖
pip install pydub requests
sudo apt install ffmpeg  # 音频转换需要

# 2. 启动服务（手动）
./api_service/start_api.sh

# 3. 测试服务
python api_service/test_api.py
```

## Systemd 部署（推荐）

```bash
# 安装为系统服务（开机自启）
sudo ./api_service/install_service.sh

# 查看服务状态
systemctl status moss-tts-nano-api

# 查看日志
journalctl -u moss-tts-nano-api -f
```

## API 接口

**POST** `http://localhost:8005/tts?text={文本}&voice={发音人}`

- **text**: URL 编码的文本内容
- **voice**: 发音人ID（如 zh_1），对应 `assets/audio/{voice}.wav`
- **返回**: MP3 音频（24kHz, 单声道, 48kbps）

## 示例

```bash
curl -X POST "http://localhost:8005/tts?text=你好世界&voice=zh_1" -o output.mp3
```

## Java 调用

参考 `api_service/examples/MossTtsClient.java`

## 健康检查

```bash
curl http://localhost:8005/health
```
