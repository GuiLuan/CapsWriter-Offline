import os
import sys
import asyncio
import websockets
from websockets.typing import Subprotocol
from multiprocessing import Process, Manager
from platform import system

from .config import ServerConfig as Config
from .types.cosmic import Cosmic, console
from .recognize.check_model import check_model
from .comm.ws_recv import ws_recv
from .comm.ws_send import ws_send
from .recognize.recognizer import recognizer_service
from .utils.empty_working_set import empty_current_working_set

BASE_DIR = os.path.dirname(__file__)
os.chdir(BASE_DIR)  # 确保 os.getcwd() 位置正确，用相对路径加载模型

__all__ = ["start_server"]


def start_server():
    try:
        asyncio.run(run_all_service())
    except KeyboardInterrupt:
        # Ctrl+C退出
        console.print("\n再见！")
    except OSError as e:
        # 端口占用
        console.print(f"出错了：{e}", style="bright_red")
        console.input("...")
    except Exception as e:
        print(e)
    finally:
        stop_all_service()
        sys.exit(0)


async def run_all_service():
    """主服务入口"""
    # 检查模型文件
    check_model()
    # 打印服务器基本信息
    print_server_info()

    # 初始化共享资源
    await initialize_shared_resources()

    # 启动识别子进程
    await start_recognizer_service()

    console.rule("[green3]开始服务")
    console.line()

    # 系统优化
    await optimize_system()

    # 启动WebSocket服务
    await start_websocket_service()


def stop_all_service():
    Cosmic.queue_out.put(None)


def print_server_info():
    """打印服务器基本信息"""
    console.line(2)
    console.rule("[bold #d55252]CapsWriter Offline Server")
    console.line()
    console.print(
        "项目地址：[cyan underline]https://github.com/HaujetZhao/CapsWriter-Offline",
        end="\n\n",
    )
    console.print(f"当前基文件夹：[cyan underline]{BASE_DIR}", end="\n\n")
    console.print(
        f"绑定的服务地址：[cyan underline]{Config.addr}:{Config.port}", end="\n\n"
    )


async def start_websocket_service():
    """启动WebSocket服务"""
    # 负责接收客户端数据的 coroutine
    recv = websockets.serve(
        ws_recv,
        Config.addr,
        Config.port,
        subprotocols=[Subprotocol("binary")],
        max_size=None,
    )

    # 负责发送结果的 coroutine
    send = ws_send()
    # 加入都执行列表
    await asyncio.gather(recv, send)


async def start_recognizer_service():
    """启动并等待识别子进程初始化完成"""
    recognize_process = Process(
        target=recognizer_service,
        args=(Cosmic.queue_in, Cosmic.queue_out, Cosmic.sockets_id),
        daemon=True,
    )
    recognize_process.start()
    # 等待子进程初始化完成
    Cosmic.queue_out.get()


async def initialize_shared_resources():
    """初始化跨进程共享资源"""
    Cosmic.sockets_id = Manager().list()


async def optimize_system():
    """执行系统优化操作"""
    if system() == "Windows":
        empty_current_working_set()


if __name__ == "__main__":
    start_server()
