import json

import websockets

from .ws_check import check_websocket
from ..config import ClientConfig as Config
from ..mtypes import Cosmic, console
from ..utils import (
    hot_sub,
    rename_audio_file,
    strip_punc,
    write_markdown_file,
    type_result,
)


async def ws_recv():
    if not await check_websocket():
        return
    console.print("[green]连接成功\n")
    try:
        while True and Cosmic.websocket is not None:
            # 接收消息
            message = await Cosmic.websocket.recv()
            message = json.loads(message)
            text = message["text"]
            delay = message["time_complete"] - message["time_submit"]

            # 如果非最终结果，继续等待
            if not message["is_final"]:
                continue

            # 消除末尾标点
            text = strip_punc(text)

            # 热词替换
            text = hot_sub(text)

            # 打字
            await type_result(text)

            if Config.save_audio:
                # 重命名录音文件
                file_audio = rename_audio_file(
                    message["task_id"], text, message["time_start"]
                )

                if file_audio is not None:
                    # 记录写入 md 文件
                    write_markdown_file(text, message["time_start"], file_audio)

            # 控制台输出
            console.print(f"    转录时延：{delay:.2f}s")
            console.print(f"    识别结果：[green]{text}")
            console.line()

    except websockets.ConnectionClosedError:
        console.print("[red]连接断开\n")
    except websockets.ConnectionClosedOK:
        console.print("[red]连接断开\n")
    except Exception as e:
        print(e)
    finally:
        return
