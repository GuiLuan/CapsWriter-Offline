from pathlib import Path
from .types.model import ParaformerModelArgs, CTTransformer

_BASE_DIR = Path(__file__).parents[1]


class ServerConfig:
    addr = "0.0.0.0"
    port = 6016

    # 中文数字 -> 阿拉伯数字
    format_num = True
    # 启用 punc_model 与否
    format_punc = True
    # 调整中英空格
    format_spell = True

    # 语音识别模型
    recognize_model = ParaformerModelArgs(
        paraformer=_BASE_DIR / "models" / "paraformer-offline-zh" / "model.int8.onnx",
        tokens=_BASE_DIR / "models" / "paraformer-offline-zh" / "tokens.txt",
        num_threads=6,
        sample_rate=16000,
        feature_dim=80,
        decoding_method="greedy_search",
        debug=False,
    )
    # 标点断句模型
    punc_model = CTTransformer(
        model_dir=_BASE_DIR / "models" / "punc_ct-transformer_cn-en",
        batch_size=1,
        device_id="-1",
        quantize=True,
        intra_op_num_threads=6,
    )
