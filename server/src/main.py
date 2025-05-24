import os
import sys
import asyncio
from multiprocessing import Process, Manager
from platform import system

from .asr import recognize_service
from .net import ws_recv_service, ws_send_service
from .utils import console, Cosmic, load_config, empty_current_working_set

__all__ = ["start"]


def start():
    """主进程"""
    try:
        asyncio.run(start_all_service())
    except KeyboardInterrupt:
        # Ctrl+C退出
        console.print("\n再见！")
    except OSError as e:
        # 端口占用
        console.print(f"出错了：{e}", style="bright_red")
        console.input("...")
    except Exception as e:
        console.print(e, style="bright_red")
    finally:
        stop_all_service()
        sys.exit(0)


async def start_all_service():
    print_server_info()
    await initialize_shared_resources()
    await start_recognizer_service()
    console.rule("[green3]开始服务")
    console.line()
    optimize_system()
    await start_websocket_service()


def stop_all_service():
    Cosmic.queue_out.put(None)


def print_server_info():
    """打印服务器基本信息"""
    server_config = load_config()["server"]
    addr, port = server_config["addr"], server_config["port"]
    console.line(2)
    console.rule("[bold #d55252]CapsWriter Offline Server")
    console.line()
    console.print(
        "项目地址：[cyan underline]https://github.com/GuiLuan/CapsWriter-Offline",
        end="\n\n",
    )
    console.print(f"当前基文件夹：[cyan underline]{os.getcwd()}", end="\n\n")
    console.print(f"绑定的服务地址：[cyan underline]{addr}:{port}", end="\n\n")


async def start_websocket_service():
    """启动WebSocket服务"""
    recv = ws_recv_service()
    send = ws_send_service()
    await asyncio.gather(recv, send)


async def start_recognizer_service():
    """启动并等待识别子进程初始化完成"""
    recognize_process = Process(
        target=recognize_service,
        args=(Cosmic.queue_in, Cosmic.queue_out, Cosmic.sockets_id),
        daemon=True,
    )
    recognize_process.start()
    # 等待子进程初始化完成
    Cosmic.queue_out.get()


async def initialize_shared_resources():
    """初始化跨进程共享资源"""
    Cosmic.sockets_id = Manager().list()


def optimize_system():
    """执行系统优化操作"""
    if system() == "Windows":
        empty_current_working_set()


if __name__ == "__main__":
    start()
