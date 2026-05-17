#!/usr/bin/env python3
"""
MOSS-TTS-Nano API 测试脚本
"""
import requests
import sys
from pathlib import Path

# 配置
API_BASE_URL = "http://localhost:8005"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "generated_audio"
OUTPUT_DIR.mkdir(exist_ok=True)


def test_health():
    """测试健康检查端点"""
    print("=" * 60)
    print("Testing health endpoint...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✓ Health check passed\n")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}\n")
        return False


def test_tts(text, voice="zh_1", output_filename="test_output.mp3"):
    """
    测试 TTS 接口
    
    Args:
        text: 要合成的文本
        voice: 发音人ID
        output_filename: 输出文件名
    """
    print("=" * 60)
    print(f"Testing TTS synthesis...")
    print(f"Text: {text}")
    print(f"Voice: {voice}")
    print("=" * 60)
    
    try:
        # 发送 POST 请求
        response = requests.post(
            f"{API_BASE_URL}/tts",
            params={"text": text, "voice": voice},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False
        
        # 保存 MP3 文件
        output_path = OUTPUT_DIR / output_filename
        output_path.write_bytes(response.content)
        
        # 显示响应头信息
        synthesis_time = response.headers.get("X-Synthesis-Time", "N/A")
        audio_length = response.headers.get("X-Audio-Length", "N/A")
        
        print(f"✓ Synthesis successful!")
        print(f"  Audio size: {len(response.content)} bytes")
        print(f"  Synthesis time: {synthesis_time}s")
        print(f"  Audio length header: {audio_length} bytes")
        print(f"  Output saved to: {output_path}")
        print(f"  Content-Type: {response.headers.get('Content-Type')}")
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ TTS synthesis failed: {e}\n")
        return False


def main():
    """主测试函数"""
    print("\nMOSS-TTS-Nano API Test Suite")
    print("=" * 60)
    
    # 测试 1: 健康检查
    if not test_health():
        print("Service is not ready. Please start the API service first.")
        print(f"Run: ./api_service/start_api.sh")
        sys.exit(1)
    
    # 测试 2: 中文合成
    test_tts(
        text="欢迎使用 MOSS-TTS-Nano API 服务。",
        voice="zh_1",
        output_filename="test_chinese.mp3"
    )
    
    # 测试 3: 英文合成
    test_tts(
        text="Hello, this is a test of the MOSS-TTS-Nano API service.",
        voice="zh_1",
        output_filename="test_english.mp3"
    )
    
    # 测试 4: 长文本合成
    test_tts(
        text="这是一个较长的测试文本，用于验证 API 服务在处理长文本时的表现。MOSS-TTS-Nano 是一个轻量级的语音合成模型，支持多种语言和声音克隆功能。",
        voice="zh_1",
        output_filename="test_long_text.mp3"
    )
    
    print("=" * 60)
    print("All tests completed!")
    print(f"Generated files are in: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
