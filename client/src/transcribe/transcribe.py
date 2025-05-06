import re
import sys
import uuid
import time
import json
import base64
import subprocess
from pathlib import Path

from ..utils import srt_from_txt
from ..mtypes import Cosmic, console
from ..comm.ws_check import check_websocket
from ..config import ClientConfig as Config

__all__ = ["transcribe_check", "transcribe_send", "transcribe_recv"]


async def transcribe_check(file: Path):
    # 检查连接
    if not await check_websocket():
        console.print("无法连接到服务端")
        sys.exit()

    if not file.exists():
        console.print(f"文件不存在：{file}")
        return False


async def transcribe_send(file: Path) -> None:
    # 生成任务 id
    task_id = str(uuid.uuid1())
    console.print(f"\n任务标识：{task_id}")
    console.print(f"    处理文件：{file}")

    # 获取音频数据，ffmpeg 输出采样率 16000，单声道，float32 格式
    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        file,
        "-f",
        "f32le",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-",
    ]
    try:
        websocket = Cosmic.websocket
        if websocket is None:
            raise RuntimeError("websocket服务端连接失败")
        process = subprocess.Popen(
            ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        if process.stdout is None:
            raise RuntimeError("FFmpeg进程启动失败，无法获取输出流")

        console.print("    正在提取音频", end="\r")
        data = process.stdout.read()
        if not data:
            raise RuntimeError("从FFmpeg读取音频数据失败")

        audio_duration = len(data) / 4 / 16000
        console.print(f"    音频长度：{audio_duration:.2f}s")
    except Exception as e:
        console.print(f"    [red]错误: {str(e)}[/red]")
        raise

    # 构建分段消息，发送给服务端
    offset = 0
    while True:
        chunk_end = offset + 16000 * 4 * 60
        is_final = False if chunk_end < len(data) else True
        message = {
            "task_id": task_id,  # 任务 ID
            "seg_duration": Config.file_seg_duration,  # 分段长度
            "seg_overlap": Config.file_seg_overlap,  # 分段重叠
            "is_final": is_final,  # 是否结束
            "time_start": time.time(),  # 录音起始时间
            "time_frame": time.time(),  # 该帧时间
            "source": "file",  # 数据来源：从文件读的数据
            "data": base64.b64encode(data[offset:chunk_end]).decode("utf-8"),
        }
        offset = chunk_end
        progress = min(offset / 4 / 16000, audio_duration)
        await websocket.send(json.dumps(message))
        console.print(f"    发送进度：{progress:.2f}s", end="\r")
        if is_final:
            break


async def transcribe_recv(file: Path) -> None:
    # 获取连接
    websocket = Cosmic.websocket
    if websocket is None:
        raise RuntimeError("websocket服务端连接失败")

    # 初始化message
    message = None

    # 接收结果
    async for message in websocket:
        message = json.loads(message)
        console.print(f"    转录进度: {message['duration']:.2f}s", end="\r")
        if message["is_final"]:
            break

    # 检查是否收到有效消息
    if message is None:
        raise RuntimeError("未收到任何转录结果")

    # 解析结果
    text_merge = message["text"]
    text_split = re.sub("[，。？]", "\n", text_merge)
    timestamps = message["timestamps"]
    tokens = message["tokens"]

    # 得到文件名
    json_filename = Path(file).with_suffix(".json")
    txt_filename = Path(file).with_suffix(".txt")
    merge_filename = Path(file).with_suffix(".merge.txt")

    # 写入结果
    with open(merge_filename, "w", encoding="utf-8") as f:
        f.write(text_merge)
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(text_split)
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump({"timestamps": timestamps, "tokens": tokens}, f, ensure_ascii=False)
    srt_from_txt.one_task(txt_filename)

    process_duration = message["time_complete"] - message["time_start"]
    console.print(f"\033[K    处理耗时：{process_duration:.2f}s")
    console.print(f"    识别结果：\n[green]{message['text']}")
