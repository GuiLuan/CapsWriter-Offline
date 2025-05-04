from dataclasses import dataclass
from typing import Union
from pathlib import Path


class BaseModelArgs: ...


@dataclass
class ParaformerModelArgs(BaseModelArgs):
    paraformer: Path
    tokens: Path
    num_threads: int
    sample_rate: int
    feature_dim: int
    decoding_method: str
    debug: bool


@dataclass
class CTTransformer(BaseModelArgs):
    model_dir: Union[str, Path]
    batch_size: int
    device_id: Union[str, int]
    quantize: bool
    intra_op_num_threads: int
