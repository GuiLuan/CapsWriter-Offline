import sys
from pathlib import Path
from typing import List, TypeVar, Type
from dataclasses import dataclass

from ..types.cosmic import console
from ..config import ModelPaths

__all__ = ["check_model"]


def check_model() -> None:
    """检查所有模型文件是否存在

    检查ModelPaths类中定义的所有Path类型属性，
    如果发现缺失的文件，则打印错误信息并退出程序。
    """
    try:
        result = ModelCheckResult.check_paths(ModelPaths)

        if result.missing_paths:
            console.print(
                MISSING_MODEL_MSG.format(
                    missing_paths="\n".join(f"    - {p}" for p in result.missing_paths),
                    model_dir=ModelPaths.model_dir,
                ),
                style="bright_red",
            )
            input("按回车退出")
            raise ModelCheckError("缺少必要的模型文件")

    except ModelCheckError:
        sys.exit(1)


# 错误消息模板
MISSING_MODEL_MSG = """
未能找到模型文件

未找到：{missing_paths}

本服务端需要 paraformer-offline-zh 模型和 punc_ct-transformer_zh-cn 模型，
请下载模型并放置到： {model_dir}

下载地址在： https://github.com/HaujetZhao/CapsWriter-Offline/releases/tag/v0.3
"""


class ModelCheckError(Exception):
    """模型检查失败异常"""

    pass


T = TypeVar("T", bound="ModelCheckResult")


@dataclass
class ModelCheckResult:
    """模型检查结果"""

    missing_paths: List[Path]
    existing_paths: List[Path]

    @classmethod
    def check_paths(cls: Type[T], model_paths: object) -> T:
        """检查模型路径是否存在

        Args:
            model_paths: 包含模型路径属性的对象

        Returns:
            ModelCheckResult: 检查结果对象
        """
        missing = []
        existing = []

        for attr in dir(model_paths):
            if attr.startswith("_"):
                continue

            path = getattr(model_paths, attr)
            if isinstance(path, Path):
                if path.exists():
                    existing.append(path)
                else:
                    missing.append(path)

        return cls(missing, existing)
