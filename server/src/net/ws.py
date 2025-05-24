import time
import json
import asyncio
from base64 import b64decode

import websockets

from ..utils import load_config, Cosmic, console, Status, Task, Result

__all__ = ["ws_send_service", "ws_recv_service"]


async def ws_send_service():
    queue_out = Cosmic.queue_out
    sockets = Cosmic.sockets

    while True:
        try:
            # 获取识别结果（从多进程队列）
            result: Result = await asyncio.to_thread(queue_out.get)

            # 得到退出的通知
            if result is None:
                print("收到None，退出循环")  # 调试信息
                return

            # 构建消息
            message = {
                "task_id": result.task_id,
                "duration": result.duration,
                "time_start": result.time_start,
                "time_submit": result.time_submit,
                "time_complete": result.time_complete,
                "tokens": result.tokens,
                "timestamps": result.timestamps,
                "text": result.text,
                "is_final": result.is_final,
            }

            # 获得 socket
            websocket = next(
                (ws for ws in sockets.values() if str(ws.id) == result.socket_id),
                None,
            )

            if not websocket:
                continue

            # 发送消息
            await websocket.send(json.dumps(message))

            if result.source == "mic":
                console.print(f"识别结果：\n    [green]{result.text}")
            elif result.source == "file":
                console.print(f"    转录进度：{result.duration:.2f}s", end="\r")
                if result.is_final:
                    console.print("\n    [green]转录完成")

        except asyncio.CancelledError:
            return

        except Exception as e:
            print(e)


async def ws_recv_service():
    cfg = load_config()["server"]
    server = await websockets.serve(
        _ws_recv,
        cfg["addr"],
        cfg["port"],
        subprotocols=[websockets.Subprotocol("binary")],
        max_size=None,
    )
    try:
        await server.wait_closed()
    except asyncio.CancelledError:
        pass
    finally:
        server.close()
        await asyncio.shield(server.wait_closed())


status_mic = Status("正在接收音频", spinner="point")


async def _ws_recv(websocket):
    global status_mic

    # 登记 socket 到字典，以 socket id 字符串为索引
    sockets = Cosmic.sockets
    sockets_id = Cosmic.sockets_id
    sockets[str(websocket.id)] = websocket
    sockets_id.append(str(websocket.id))
    console.print(f"接客了：{websocket}\n", style="yellow")

    # # 设定分段长度
    # seg_duration = 15
    # seg_overlap = 2
    # seg_threshold = seg_duration + seg_overlap * 2

    # 片段缓冲区、偏移时长
    cache = Cache()

    # 接收数据
    try:
        async for message in websocket:
            # json 解码字符串
            message = json.loads(message)

            # 处理数据
            await message_handler(websocket, message, cache)

        console.print(
            "ConnectionClosed...",
        )
    except websockets.ConnectionClosed:
        console.print(
            "ConnectionClosed...",
        )
    except websockets.InvalidState:
        console.print("InvalidState...")
    except Exception as e:
        console.print("Exception:", e)
    finally:
        status_mic.stop()
        status_mic.on = False
        sockets.pop(str(websocket.id))
        sockets_id.remove(str(websocket.id))


class Cache:
    # 定义一个可变对象，用于保存音频数据、偏移时间
    def __init__(self):
        self.chunks = b""
        self.offset = 0
        self.frame_num = 0


async def message_handler(websocket, message, cache: Cache):
    """处理得到的音频流数据"""

    queue_in = Cosmic.queue_in

    global status_mic
    source = message["source"]
    is_final = message["is_final"]
    is_start = not bool(cache.chunks)

    # 获取 id
    task_id = message["task_id"]
    socket_id = str(websocket.id)

    # 获取分段长度（以多长的音频进行识别）
    seg_duration = message["seg_duration"]
    seg_overlap = message["seg_overlap"]
    seg_threshold = seg_duration + seg_overlap * 2

    # base64 解码音频数据，再
    # 音频数据是 float32、单声道、16000采样率
    data = b64decode(message["data"])
    cache.chunks += data
    cache.frame_num += len(data)

    if not is_final:
        # 打印消息
        if source == "mic":
            status_mic.start()
        if source == "file" and is_start:
            console.print("正在接收音频文件...")

        # 若缓冲已达到分段长度，将片段作为任务提交
        while len(cache.chunks) / 4 / 16000 >= seg_threshold:
            data = cache.chunks[: 4 * 16000 * (seg_duration + seg_overlap)]
            cache.chunks = cache.chunks[4 * 16000 * seg_duration :]
            task = Task(
                source=message["source"],
                data=data,
                offset=cache.offset,
                task_id=task_id,
                socket_id=socket_id,
                overlap=seg_overlap,
                is_final=False,
                time_start=message["time_start"],
                time_submit=time.time(),
            )
            cache.offset += seg_duration
            queue_in.put(task)

    elif is_final:
        # 打印消息
        if source == "mic":
            status_mic.stop()
        elif source == "file":
            print(f"音频文件接收完毕，时长 {cache.frame_num / 16000 / 4:.2f}s")

        # 客户端说片段结束，将缓冲区音频识别
        task = Task(
            source=message["source"],
            data=cache.chunks[0:],
            offset=cache.offset,
            task_id=task_id,
            socket_id=socket_id,
            overlap=seg_overlap,
            is_final=True,
            time_start=message["time_start"],
            time_submit=time.time(),
        )
        queue_in.put(task)

        # 还原缓冲区、偏移时长
        cache.chunks = b""
        cache.offset = 0
        cache.frame_num = 0
