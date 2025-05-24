from typing import Dict
from multiprocessing import Queue
from multiprocessing.managers import ListProxy

import websockets
from rich.style import StyleType
from rich.console import Console
from rich.status import Status as St
from rich.console import RenderableType

__all__ = ["Status", "Cosmic", "console", "Task", "Result"]


class Status(St):
    """
    重写 rich 的 Status，让它知道自己是否正在播放
    """

    def __init__(
        self,
        status: RenderableType,
        *,
        spinner: str = "dots",
        spinner_style: StyleType = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ):
        super().__init__(
            status,
            console=None,
            spinner=spinner,
            spinner_style=spinner_style,
            speed=speed,
            refresh_per_second=refresh_per_second,
        )
        self.started = False
        self.on = True

    def start(self) -> None:
        """开始播放"""
        if not self.started:
            self.started = True
            super().start()

    def stop(self) -> None:
        """停止播放"""
        if self.started:
            self.started = False
            super().stop()


console = Console(highlight=False)


class Cosmic:
    sockets: Dict[str, websockets.WebSocketClientProtocol] = {}
    sockets_id: ListProxy
    queue_in = Queue()
    queue_out = Queue()


class Task:
    def __init__(
        self,
        source: str,
        data,
        offset: float,
        overlap: float,
        task_id: str,
        socket_id: str,
        is_final: bool,
        time_start: float,
        time_submit: float,
    ) -> None:
        self.source = source
        self.data = data
        self.offset = offset
        self.overlap = overlap
        self.task_id = task_id
        self.socket_id = socket_id
        self.is_final = is_final
        self.time_start = time_start
        self.time_submit = time_submit
        self.samplerate = 16000


class Result:
    def __init__(self, task_id, socket_id, source) -> None:
        self.task_id = task_id  # 任务 id
        self.socket_id = socket_id  # socket id
        self.source = source  # 是从 'file' 还是 'mic' 的音频流得到的结果

        self.duration: float = 0.0  # 全部音频时长 (float)
        self.time_start: float = 0.0  # 录音开始的时刻 (float)
        self.time_submit: float = 0.0  # 片段提交时间 (float)
        self.time_complete: float = 0.0  # 识别完成时间 (float)

        self.tokens = []  # 字级 token
        self.timestamps = []  # 字级 token 的时间戳
        self.text = ""  # 合并的文字
        self.is_final = False  # 是否已完成所有片段识别
