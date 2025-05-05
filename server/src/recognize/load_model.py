import sherpa_onnx
import funasr_onnx
from pathlib import Path

from ..mtypes import (
    BaseModelArgs,
    ParaformerModelArgs,
    CTTransformerArgs,
    SenseVoiceArgs,
)

__all__ = ["load_model"]


class ModelNotSupportedError(Exception):
    """当传入的模型参数类型不被支持时抛出"""


def load_model(args: BaseModelArgs):
    match args:
        case ParaformerModelArgs():
            return load_paraformer_model(args)
        case CTTransformerArgs():
            return load_cttransformer_model(args)
        case SenseVoiceArgs():
            return load_sensevoice_model(args)
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


def load_cttransformer_model(args: CTTransformerArgs):
    return funasr_onnx.CT_Transformer(
        **{
            key: value
            for key, value in args.__dict__.items()
            if not key.startswith("_")
        }
    )


def load_sensevoice_model(args: SenseVoiceArgs):
    params = {}
    for key, value in args.__dict__.items():
        if key.startswith("_"):
            continue
        if isinstance(value, Path):
            params[key] = str(value)
        else:
            params[key] = value
    return sherpa_onnx.OfflineRecognizer.from_sense_voice(**params)
