import websockets
import sounddevice as sd
from typing import List, Union
from asyncio import Queue, AbstractEventLoop

from rich.theme import Theme
from rich.console import Console

__all__ = ["Cosmic", "console"]

my_theme = Theme({"markdown.code": "cyan", "markdown.item.number": "yellow"})
console = Console(highlight=False, soft_wrap=False, theme=my_theme)


class Cosmic:
    """
    用一个 class 存储需要跨模块访问的变量值，命名为 Cosmic
    """

    on = False
    queue_in: Queue
    queue_out: Queue
    loop: Union[None, AbstractEventLoop] = None
    websocket: Union[None, websockets.WebSocketClientProtocol] = None
    audio_files = {}
    stream: Union[None, sd.InputStream] = None
    kwd_list: List[str] = []
