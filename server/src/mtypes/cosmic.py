import websockets
from multiprocessing import Queue
from typing import Dict
from multiprocessing.managers import ListProxy
from rich.console import Console

__all__ = ["Cosmic", "console"]

console = Console(highlight=False)


class Cosmic:
    sockets: Dict[str, websockets.WebSocketClientProtocol] = {}
    sockets_id: ListProxy
    queue_in = Queue()
    queue_out = Queue()
