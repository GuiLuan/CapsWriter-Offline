from ..config import ClientConfig as Config

__all__ = ["strip_punc"]


def strip_punc(text: str) -> str:
    return text.strip(Config.trash_punc)
