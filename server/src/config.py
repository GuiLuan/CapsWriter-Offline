from pathlib import Path
from .types.model import ParaformerModelArgs, SenseVoiceArgs, CTTransformerArgs

__all__ = ["ServerConfig"]

_BASE_DIR = Path(__file__).parents[1]

# Paraformer
paraformer_model = ParaformerModelArgs(
    paraformer=_BASE_DIR / "models" / "paraformer-offline-zh" / "model.int8.onnx",
    tokens=_BASE_DIR / "models" / "paraformer-offline-zh" / "tokens.txt",
    num_threads=6,
    sample_rate=16000,
    feature_dim=80,
    decoding_method="greedy_search",
    debug=False,
)

# sense-voice
# 识别结果自带标点，不需要像paraformer一样需要额外的标点模型
sensevoice_model = SenseVoiceArgs(
    model=_BASE_DIR
    / "models"
    / "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
    / "model.int8.onnx",
    tokens=_BASE_DIR
    / "models"
    / "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
    / "tokens.txt",
    num_threads=6,
    sample_rate=16000,
    feature_dim=80,
    decoding_method="greedy_search",
    use_itn=True,
    debug=False,
)

cttransformer_model = CTTransformerArgs(
    model_dir=_BASE_DIR / "models" / "punc_ct-transformer_cn-en",
    batch_size=1,
    device_id="-1",
    quantize=True,
    intra_op_num_threads=6,
)


class ServerConfig:
    addr = "0.0.0.0"
    port = 6016

    # 中文数字 -> 阿拉伯数字
    format_num = False
    # 启用 punc_model 与否
    format_punc = False
    # 调整中英空格
    format_spell = True

    # 语音识别模型
    recognize_model = sensevoice_model
    # 标点断句模型
    punc_model = cttransformer_model
