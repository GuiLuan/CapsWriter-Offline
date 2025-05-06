import asyncio
import sys
import time
import threading
import numpy as np

import sounddevice as sd

from ..mtypes import Cosmic, console

__all__ = ["stream_open", "stream_close"]


def record_callback(
    indata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags
) -> None:
    if not Cosmic.on:
        return
    loop = Cosmic.loop
    if loop is None:
        raise RuntimeError(
            "Event loop not initialized. Please initialize Cosmic.loop before launching tasks."
        )

    asyncio.run_coroutine_threadsafe(
        Cosmic.queue_in.put(
            {
                "type": "data",
                "time": time.time(),
                "data": indata.copy(),
            },
        ),
        loop,
    )


def stream_close(signum, frame):
    if Cosmic.stream is None:
        return
    Cosmic.stream.close()


def stream_reopen():
    if not threading.main_thread().is_alive():
        return
    print("重启音频流")

    # 关闭旧流
    if Cosmic.stream is not None:
        Cosmic.stream.close()

    # 重载 PortAudio，更新设备列表
    sd._terminate()
    sd._ffi.dlclose(sd._lib)
    if sd._libname is not None:
        sd._lib = sd._ffi.dlopen(sd._libname)
    sd._initialize()

    # 打开新流
    time.sleep(0.1)
    Cosmic.stream = stream_open()


def stream_open():
    # 显示录音所用的音频设备
    channels = 1
    try:
        device = sd.query_devices(kind="input")
        channels = min(2, getattr(device, "max_input_channels", 1))
        console.print(
            f"使用默认音频设备：[italic]{getattr(device, 'name', '未知设备')}，声道数：{channels}",
            end="\n\n",
        )
    except UnicodeDecodeError:
        console.print(
            "由于编码问题，暂时无法获得麦克风设备名字", end="\n\n", style="bright_red"
        )
    except sd.PortAudioError:
        console.print("没有找到麦克风设备", end="\n\n", style="bright_red")
        input("按回车键退出")
        sys.exit()

    stream = sd.InputStream(
        samplerate=48000,
        blocksize=int(0.05 * 48000),  # 0.05 seconds
        device=None,
        dtype="float32",
        channels=channels,
        callback=record_callback,
        finished_callback=stream_reopen,
    )
    stream.start()

    return stream
