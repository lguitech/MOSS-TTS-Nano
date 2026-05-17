"""
MOSS-TTS-Nano API Service
基于 ONNX Runtime CUDA 加速的 TTS API 服务
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
import logging
import time
import io
import os
from pathlib import Path
from typing import Optional

# 音频处理依赖
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("pydub not available, audio conversion will fail")

# MOSS-TTS-Nano 依赖
from onnx_tts_runtime import OnnxTtsRuntime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="MOSS-TTS-Nano API Service", version="1.0.0")

# 全局变量：TTS 运行时实例
tts_runtime: Optional[OnnxTtsRuntime] = None

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"


def get_reference_audio_path(voice: str) -> Path:
    """
    获取发音人参考音频路径
    
    Args:
        voice: 发音人ID，如 'zh_1'
    
    Returns:
        参考音频文件路径
    
    Raises:
        FileNotFoundError: 如果音频文件不存在
    """
    audio_path = ASSETS_AUDIO_DIR / f"{voice}.wav"
    
    # 如果指定文件不存在，使用默认 zh_1.wav
    if not audio_path.exists():
        logger.warning(f"Voice '{voice}' not found, using default 'zh_1'")
        audio_path = ASSETS_AUDIO_DIR / "zh_1.wav"
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Default reference audio not found: {audio_path}")
    
    return audio_path


def convert_wav_to_mp3(wav_bytes: bytes) -> bytes:
    """
    将 WAV 音频转换为 MP3 格式（24kHz, 单声道, 48kbps）
    
    Args:
        wav_bytes: WAV 格式的音频数据
    
    Returns:
        MP3 格式的音频数据
    
    Raises:
        RuntimeError: 如果转换失败
    """
    if not PYDUB_AVAILABLE:
        raise RuntimeError("pydub is required for audio conversion. Install with: pip install pydub")
    
    try:
        # 加载 WAV 数据
        audio = AudioSegment.from_wav(io.BytesIO(wav_bytes))
        
        # 转换为 24kHz 单声道
        audio = audio.set_frame_rate(24000).set_channels(1)
        
        # 导出为 MP3 (48kbps)
        mp3_buffer = io.BytesIO()
        audio.export(mp3_buffer, format="mp3", bitrate="48k")
        
        return mp3_buffer.getvalue()
    except Exception as e:
        logger.error(f"Audio conversion failed: {e}", exc_info=True)
        raise RuntimeError(f"Failed to convert audio to MP3: {e}")


@app.on_event("startup")
async def startup_event():
    """服务启动时加载模型"""
    global tts_runtime
    
    logger.info("=" * 60)
    logger.info("Starting MOSS-TTS-Nano API Service")
    logger.info("=" * 60)
    
    try:
        # 初始化 ONNX TTS Runtime (CUDA 加速)
        logger.info("Loading ONNX model with CUDA acceleration...")
        tts_runtime = OnnxTtsRuntime(
            model_dir=None,  # 使用默认模型目录
            thread_count=4,
            execution_provider="cuda",  # 固定使用 CUDA
        )
        logger.info("Model loaded successfully!")
        logger.info(f"Available providers: {tts_runtime.sessions.get('tts', None)}")
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}", exc_info=True)
        raise


@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "service": "MOSS-TTS-Nano API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """
    详细健康检查
    
    Returns:
        服务状态信息
    """
    global tts_runtime
    
    if tts_runtime is None:
        return {
            "status": "unhealthy",
            "model_loaded": False,
            "device": "unknown",
            "backend": "onnx"
        }
    
    return {
        "status": "healthy",
        "model_loaded": True,
        "device": "cuda:0",
        "backend": "onnx"
    }


@app.post("/tts")
async def synthesize(
    text: str = Query(..., description="要合成的文本"),
    voice: str = Query("zh_1", description="发音人ID，如 zh_1, en_1 等")
):
    """
    文本转语音接口
    
    Parameters:
    - text: 要转换的文本（URL 编码）
    - voice: 发音人ID，对应 assets/audio/{voice}.wav
    
    Returns:
    - MP3 音频数据（24kHz, 单声道, 48kbps）
    """
    global tts_runtime
    
    # 验证参数
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if tts_runtime is None:
        raise HTTPException(status_code=503, detail="Service not ready, model not loaded")
    
    start_time = time.time()
    
    try:
        logger.info(f"Synthesizing: text='{text[:50]}...', voice='{voice}'")
        
        # 获取参考音频路径
        reference_audio_path = get_reference_audio_path(voice)
        logger.info(f"Using reference audio: {reference_audio_path}")
        
        # 调用 ONNX TTS 推理
        result = tts_runtime.synthesize(
            text=text.strip(),
            voice=None,  # 不使用内置语音
            prompt_audio_path=str(reference_audio_path),  # 使用参考音频
            output_audio_path=None,  # 不保存到文件
            sample_mode="fixed",
            do_sample=True,
            streaming=False,
            max_new_frames=375,
            voice_clone_max_text_tokens=75,
            enable_wetext=True,
            enable_normalize_tts_text=True,
        )
        
        # 获取生成的波形数据
        waveform = result["waveform"]
        sample_rate = result["sample_rate"]
        
        # 将波形数据转换为 WAV 字节流
        wav_buffer = io.BytesIO()
        import wave
        import numpy as np
        
        # 确保数据类型为 int16
        audio_data = np.clip(waveform, -1.0, 1.0)
        if audio_data.ndim == 1:
            audio_data = audio_data.reshape(-1, 1)
        pcm16 = np.round(audio_data * 32767.0).astype(np.int16)
        
        # 写入 WAV 格式
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(int(pcm16.shape[1]))
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(int(sample_rate))
            wav_file.writeframes(pcm16.tobytes())
        
        wav_bytes = wav_buffer.getvalue()
        
        # 转换为 MP3 格式（24kHz, 单声道, 48kbps）
        mp3_bytes = convert_wav_to_mp3(wav_bytes)
        
        # 计算合成耗时
        synthesis_time = time.time() - start_time
        
        logger.info(
            f"Generated {len(mp3_bytes)} bytes MP3 in {synthesis_time:.2f}s"
        )
        
        # 返回 MP3 音频
        return Response(
            content=mp3_bytes,
            media_type="audio/mpeg",
            headers={
                "X-Synthesis-Time": f"{synthesis_time:.3f}",
                "X-Audio-Length": str(len(mp3_bytes))
            }
        )
        
    except FileNotFoundError as e:
        logger.error(f"Reference audio not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"TTS synthesis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("MOSS-TTS-Nano API Service")
    print("=" * 60)
    print("Starting server on http://0.0.0.0:8005")
    print("Health check: http://0.0.0.0:8005/health")
    print("TTS endpoint: POST http://0.0.0.0:8005/tts?text=xxx&voice=zh_1")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        log_level="info"
    )
