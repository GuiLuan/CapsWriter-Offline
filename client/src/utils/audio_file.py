import os
import re
import uuid
import time
import json
import shutil
import base64
import asyncio
from pathlib import Path
from typing import Union, Tuple
from subprocess import Popen, PIPE, DEVNULL

import wave
import tempfile
import websockets
import numpy as np

from ..mtypes import Cosmic, console
from ..config import ClientConfig as Config

__all__ = [
    "create_audio_file",
    "write_audio_file",
    "finish_audio_file",
    "rename_audio_file",
    "send_audio",
]


def create_audio_file(
    channels: int, time_start: float
) -> Tuple[Path, Union[Popen, wave.Wave_write]]:
    time_year = time.strftime("%Y", time.localtime(time_start))
    time_month = time.strftime("%m", time.localtime(time_start))
    time_ymdhms = time.strftime("%Y%m%d-%H%M%S", time.localtime(time_start))

    folder_path = Path() / time_year / time_month / "assets"
    os.makedirs(folder_path, exist_ok=True)
    file_path = tempfile.mktemp(prefix=f"({time_ymdhms})", dir=folder_path)
    file_path = Path(file_path)

    if shutil.which("ffmpeg"):
        # 用户已安装 ffmpeg，则输出到 mp3 文件
        file_path = file_path.with_suffix(".mp3")
        # 构造ffmpeg命令行
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-f",
            "f32le",
            "-ar",
            "48000",
            "-ac",
            f"{channels}",
            "-i",
            "-",
            "-b:a",
            "192k",
            file_path,
        ]
        # 执行ffmpeg命令行，得到 Popen
        file = Popen(ffmpeg_command, stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
    else:  # 用户未安装 ffmpeg，则输出为 wav 格式
        file_path = file_path.with_suffix(".wav")
        file = wave.open(str(file_path), "w")
        file.setnchannels(channels)
        file.setsampwidth(2)
        file.setframerate(48000)
    return file_path, file


def rename_audio_file(task_id, text, time_start) -> Union[Path, None]:
    # 获取旧文件名
    file_path = Path(Cosmic.audio_files.pop(task_id))

    # 确保旧文件存在
    if not file_path.exists():
        console.print(f"    文件不存在：{file_path}")
        return

    # 构建新文件名
    # time_year = time.strftime("%Y", time.localtime(time_start))
    # time_month = time.strftime("%m", time.localtime(time_start))
    time_ymdhms = time.strftime("%Y%m%d-%H%M%S", time.localtime(time_start))
    file_stem = f"({time_ymdhms}){text[: Config.audio_name_len]}"
    file_stem = re.sub(r'[\\/:"*?<>|]', " ", file_stem)

    # 重命名
    file_path_new = file_path.with_name(file_stem + file_path.suffix)
    file_path.rename(file_path_new)

    # 返回新的录音文件路径
    return file_path_new


def write_audio_file(file: Union[Popen, wave.Wave_write], data: np.ndarray):
    if isinstance(file, Popen) and file.stdin:
        file.stdin.write(data.tobytes())
        file.stdin.flush()
    elif isinstance(file, wave.Wave_write):
        int16_data = (data * (2**15 - 1)).astype(np.int16)
        file.writeframes(int16_data.tobytes())


def finish_audio_file(file: Union[Popen, wave.Wave_write]):
    if isinstance(file, Popen) and file.stdin:
        file.stdin.close()  # 停止输入，ffmpeg 会自动关闭

    elif isinstance(file, wave.Wave_write):
        file.close()


async def send_message(message):
    # 发送数据
    if Cosmic.websocket is None or Cosmic.websocket.closed:
        if message["is_final"]:
            Cosmic.audio_files.pop(message["task_id"])
            console.print("    服务端未连接，无法发送\n")
    else:
        try:
            await Cosmic.websocket.send(json.dumps(message))
        except websockets.ConnectionClosedError as _:
            if message["is_final"]:
                console.print("[red]连接中断了")
        except Exception as e:
            print("出错了")
            print(e)


async def send_audio():
    try:
        # 生成唯一任务 ID
        task_id = str(uuid.uuid1())

        # 任务起始时间
        time_start = 0

        # 音频数据临时存放处
        cache = []
        duration = 0

        # 保存音频文件
        file_path, file = "", None

        # 开始取数据
        # task: {'type', 'time', 'data'}
        while task := await Cosmic.queue_in.get():
            Cosmic.queue_in.task_done()
            if task["type"] == "begin":
                time_start = task["time"]
            elif task["type"] == "data":
                # 在阈值之前积攒音频数据
                if task["time"] - time_start < Config.threshold:
                    cache.append(task["data"])
                    continue

                # 创建音频文件
                if Config.save_audio and not file_path:
                    file_path, file = create_audio_file(
                        task["data"].shape[1], time_start
                    )
                    Cosmic.audio_files[task_id] = file_path

                # 获取音频数据
                if cache:
                    data = np.concatenate(cache)
                    cache.clear()
                else:
                    data = task["data"]

                # 保存音频至本地文件
                duration += len(data) / 48000
                if Config.save_audio and file:
                    write_audio_file(file, data)

                # 发送音频数据用于识别
                message = {
                    "task_id": task_id,  # 任务 ID
                    "seg_duration": Config.mic_seg_duration,  # 分段长度
                    "seg_overlap": Config.mic_seg_overlap,  # 分段重叠
                    "is_final": False,  # 是否结束
                    "time_start": time_start,  # 录音起始时间
                    "time_frame": task["time"],  # 该帧时间
                    "source": "mic",  # 数据来源：从麦克风收到的数据
                    "data": base64.b64encode(  # 数据
                        np.mean(data[::3], axis=1).tobytes()
                    ).decode("utf-8"),
                }
                task = asyncio.create_task(send_message(message))
            elif task["type"] == "finish":
                # 完成写入本地文件
                if Config.save_audio and file:
                    finish_audio_file(file)

                console.print(f"任务标识：{task_id}")
                console.print(f"    录音时长：{duration:.2f}s")

                # 告诉服务端音频片段结束了
                message = {
                    "task_id": task_id,
                    "seg_duration": 15,
                    "seg_overlap": 2,
                    "is_final": True,
                    "time_start": time_start,
                    "time_frame": task["time"],
                    "source": "mic",
                    "data": "",
                }
                task = asyncio.create_task(send_message(message))
                break
    except Exception as e:
        print(e)
