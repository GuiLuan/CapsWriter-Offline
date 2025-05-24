import tomllib
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any

__all__ = ["load_config"]


@lru_cache(maxsize=1)  # 只保留最新一次调用的结果
def load_config(path: str | Path = "config.toml") -> Dict[str, Any]:
    """读 TOML 并把结果自动缓存到装饰器里。"""
    with open(path, "rb") as f:
        return tomllib.load(f)
