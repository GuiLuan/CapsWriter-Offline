from pathlib import Path


class ServerConfig:
    addr = "0.0.0.0"
    port = 6016

    format_num = True  # 输出时是否将中文数字转为阿拉伯数字
    format_punc = True  # 输出时是否启用标点符号引擎
    format_spell = True  # 输出时是否调整中英之间的空格


class ModelPaths:
    _BASE_DIR = Path(__file__).parents[1]
    model_dir = _BASE_DIR / "models"
    paraformer_path = _BASE_DIR / "models" / "paraformer-offline-zh" / "model.int8.onnx"
    tokens_path = _BASE_DIR / "models" / "paraformer-offline-zh" / "tokens.txt"
    punc_model_dir = _BASE_DIR / "models" / "punc_ct-transformer_cn-en"


class ParaformerArgs:
    paraformer = f"{ModelPaths.paraformer_path}"
    tokens = f"{ModelPaths.tokens_path}"
    num_threads = 6
    sample_rate = 16000
    feature_dim = 80
    decoding_method = "greedy_search"
    debug = False
