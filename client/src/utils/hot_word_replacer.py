from . import hot_word_replacer_zh, hot_word_replacer_en, hot_word_replacer_rule
from ..config import ClientConfig as Config

__all__ = ["hot_sub"]


def hot_sub(text: str) -> str:
    # 热词替换
    if Config.hot_zh:
        text = hot_word_replacer_zh.热词替换(text)
    if Config.hot_en:
        text = hot_word_replacer_en.热词替换(text)
    if Config.hot_rule:
        text = hot_word_replacer_rule.热词替换(text)
    return text
