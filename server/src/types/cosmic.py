from multiprocessing import Queue
from typing import Dict
from multiprocessing.managers import ListProxy
import websockets
from rich.console import Console

console = Console(highlight=False)


class Cosmic:
    sockets: Dict[str, websockets.WebSocketClientProtocol] = {}
    sockets_id: ListProxy
    queue_in = Queue()
    queue_out = Queue()
