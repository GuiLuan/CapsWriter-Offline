import sys
from pathlib import Path
from typing import Any, Iterable, Generator, Set
from dataclasses import is_dataclass, fields as dataclass_fields  # 重命名避免冲突

from ..types.model import BaseModelArgs
from ..types.cosmic import console

__all__ = ["check_model"]

# 错误消息模板
MISSING_MODEL_MSG = """
[bold red]未能找到必要的模型文件[/]

[yellow]缺失的文件:[/yellow]
{missing_paths}

[cyan]提示:[/cyan]
本服务端需要 [green]paraformer-offline-zh[/] 模型和 [green]punc_ct-transformer_zh-cn[/] 模型。
请确保已下载这些模型并将其放置在正确的目录下（通常是 'models' 目录）。

模型下载地址: [link=https://github.com/HaujetZhao/CapsWriter-Offline/releases/tag/v0.3]https://github.com/HaujetZhao/CapsWriter-Offline/releases/tag/v0.3[/link]
"""


def _find_paths(obj: Any) -> Generator[Path, None, None]:
    """递归地查找对象及其嵌套成员中的所有 Path 对象。"""
    # 检查是否已访问过，防止无限递归（虽然在树状结构中不太可能，但以防万一）
    # 对于大型配置或循环引用，这可能需要更复杂的处理，但对于典型模型配置应该足够
    # 这里简单起见，不添加 visited 集合

    if isinstance(obj, Path):
        yield obj
        return

    # 忽略基本类型和 None
    if isinstance(obj, (str, bytes, int, float, bool, type(None), type)):
        return

    # 优先处理已知结构：Pydantic 模型, Dataclasses, 常见迭代器
    processed = False
    try:
        # 尝试 Pydantic v2+ 的 model_fields
        model_fields = getattr(obj, "model_fields", None)
        if model_fields:
            for field_name in model_fields:
                yield from _find_paths(getattr(obj, field_name))
            processed = True

        # 尝试 Pydantic v1 的 __fields__
        if not processed:
            fields_v1 = getattr(obj, "__fields__", None)
            if fields_v1:
                for field_name in fields_v1:
                    yield from _find_paths(getattr(obj, field_name))
                processed = True

        # 尝试标准库 dataclasses 的 fields
        if not processed and is_dataclass(obj):
            # is_dataclass(obj) 已经排除了 type
            for field in dataclass_fields(obj):
                yield from _find_paths(getattr(obj, field.name))
            processed = True

    except TypeError:
        # is_dataclass 或 getattr 可能对某些类型抛出 TypeError
        pass

    # 处理常见迭代器（列表、元组、集合），排除字符串和字节串
    if (
        not processed
        and isinstance(obj, Iterable)
        and not isinstance(obj, (str, bytes))
    ):
        for item in obj:
            yield from _find_paths(item)
        processed = True

    # 注意：这里没有包含对普通对象的属性遍历，因为我们假设配置
    # 主要由 Pydantic 模型、数据类和基本集合构成。
    # 如果需要支持任意嵌套的普通对象，可以添加 dir() 遍历，但需谨慎。


def check_model() -> None:
    """检查 ServerConfig 中定义的所有模型文件是否存在。

    递归查找 ServerConfig 对象中所有 BaseModelArgs 实例内部的 Path 类型属性，
    如果发现缺失的文件，则打印错误信息并退出程序。
    """
    try:
        # 延迟导入以避免潜在的循环依赖和加速启动
        from ..config import ServerConfig
    except ImportError as e:
        console.print(
            f"[bold red]错误：无法导入 ServerConfig，请检查配置模块。 ({e})[/]"
        )
        sys.exit(1)

    all_paths: Set[Path] = set()

    # 确定要检查的对象：ServerConfig 本身或其属性值
    objects_to_check = []
    if isinstance(ServerConfig, BaseModelArgs) or (
        is_dataclass(ServerConfig) and not isinstance(ServerConfig, type)
    ):
        # 如果 ServerConfig 本身就是目标类型
        objects_to_check.append(ServerConfig)
    else:
        # 否则，遍历其属性（假设它是一个模块或包含配置的类/实例）
        config_attrs = (
            vars(ServerConfig)
            if hasattr(ServerConfig, "__dict__")
            else {
                name: getattr(ServerConfig, name)
                for name in dir(ServerConfig)
                if not name.startswith("_")
            }
        )
        for attr_value in config_attrs.values():
            if isinstance(attr_value, BaseModelArgs):
                objects_to_check.append(attr_value)
            # 可以选择性地也检查其他数据类属性
            # elif is_dataclass(attr_value) and not isinstance(attr_value, type):
            #     objects_to_check.append(attr_value)

    # 从选定的对象中收集所有路径
    for obj in objects_to_check:
        for path in _find_paths(obj):
            all_paths.add(path)  # 使用 set 自动去重

    # 检查路径是否存在
    missing_paths = {p for p in all_paths if not p.exists()}

    if missing_paths:
        # 按路径字符串排序以获得一致的输出
        sorted_missing_paths = sorted(list(missing_paths), key=str)
        # 解析为绝对路径以提供更清晰的信息
        missing_paths_str = "\n".join(
            f"    - {p.resolve()}" for p in sorted_missing_paths
        )
        error_message = MISSING_MODEL_MSG.format(missing_paths=missing_paths_str)

        console.print(error_message, style="white")  # 使用默认样式，让标记生效

        # 在非交互式环境（如 CI/CD 或无 TTY 的 Docker）中，input() 会失败
        if sys.stdin.isatty():
            try:
                input("按回车键退出...")
            except EOFError:
                pass  # 忽略非交互式环境中的 EOFError
        else:
            console.print("[yellow]在非交互式环境中运行，将直接退出。[/]")

        sys.exit(1)
