import ctypes
import tomllib
from pathlib import Path
from typing import Union
from functools import lru_cache

from .types import Status, Cosmic, console, Task, Result


__all__ = [
    "empty_working_set",
    "empty_current_working_set",
    "load_config",
    "Status",
    "Cosmic",
    "console",
    "Task",
    "Result",
]


@lru_cache(maxsize=1)
def load_config(
    config_path: Union[str, Path] = "./config.toml",
):
    """读取项目配置，默认在根目录寻找"""
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def empty_working_set(pid: int):
    """清空 pid 对应进程的残留内存"""
    handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, pid)
    ctypes.windll.psapi.EmptyWorkingSet(handle)
    ctypes.windll.kernel32.CloseHandle(handle)


def empty_current_working_set():
    pid = ctypes.windll.kernel32.GetCurrentProcessId()
    empty_working_set(pid)
