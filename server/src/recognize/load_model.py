import sherpa_onnx
import funasr_onnx
from pathlib import Path

from ..types.model import BaseModelArgs, ParaformerModelArgs, CTTransformer

__all__ = ["load_model"]


class ModelNotSupportedError(Exception):
    """当传入的模型参数类型不被支持时抛出"""


def load_model(args: BaseModelArgs):
    match args:
        case ParaformerModelArgs():
            return load_paraformer_model(args)
        case CTTransformer():
            return load_cttransformer_model(args)
        case _:
            raise ModelNotSupportedError(
                f"Model type {type(args).__name__} is not supported"
            )


def load_paraformer_model(args: ParaformerModelArgs):
    params = {}
    for key, value in args.__dict__.items():
        if key.startswith("_"):
            continue
        if isinstance(value, Path):
            params[key] = str(value)
        else:
            params[key] = value
    return sherpa_onnx.OfflineRecognizer.from_paraformer(**params)


def load_cttransformer_model(args: CTTransformer):
    return funasr_onnx.CT_Transformer(
        **{
            key: value
            for key, value in args.__dict__.items()
            if not key.startswith("_")
        }
    )
