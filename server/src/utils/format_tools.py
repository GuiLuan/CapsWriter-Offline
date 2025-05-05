from .adjust_space import adjust_space
from .chinese_itn import chinese_to_num
from ..config import ServerConfig as Config

__all__ = ["format_text"]


def format_text(text: str, punc_model=None) -> str:
    if Config.format_spell:
        text = adjust_space(text)
    if Config.format_punc and punc_model and text:
        text = punc_model(text)[0]
    if Config.format_num:
        text = chinese_to_num(text)
    if Config.format_spell:
        text = adjust_space(text)  # 防止前面的修改导致空格异常
    return text
