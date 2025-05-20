import re
from typing import Final

__all__ = ["adjust_space"]

# 基本汉字区；如需扩展区，把码段自行追加
_CN: Final[str] = r"\u4e00-\u9fff"

# ——— ① 插空格用（“贴着” → “带空格”） ——— #
_INS_PAT = {
    "cn_en": (
        rf"([{_CN}])([A-Za-z])",
        rf"([A-Za-z])([{_CN}])",
    ),
    "cn_digit": (
        rf"([{_CN}])(\d)",
        rf"(\d)([{_CN}])",
    ),
    "en_digit": (
        r"([A-Za-z])(\d)",
        r"(\d)([A-Za-z])",
    ),
}

# ——— ② 删空格用（“带空格” → “贴着”） ——— #
_RM_PAT = {
    k: tuple(
        pat.replace(")", r")\s+") for pat in pats
    )  # 在第一个捕获组和第二个之间插 \s+
    for k, pats in _INS_PAT.items()
}

# 永远要删的：汉字 + 空格 + 汉字
_RM_CN_SPACE = rf"([{_CN}])\s+([{_CN}])"


def adjust_space(
    text: str,
    cn_en: bool = False,
    cn_digit: bool = False,
    en_digit: bool = False,
) -> str:
    """
    根据三个开关在【中文↔英文】【中文↔数字】【英文↔数字】之间插/删空格；
    无论如何都会“压缩空白”，并始终删除汉字之间的空格。

    Parameters
    ----------
    text : str
        待处理文本
    cn_en : bool, default False
        True  → 中文↔英文之间留 1 个空格
        False → 删掉两者之间已有的空格
    cn_digit : bool, default False
        True  → 中文↔数字之间留 1 个空格
        False → 删掉两者之间已有的空格
    en_digit : bool, default False
        True  → 英文↔数字之间留 1 个空格
        False → 删掉两者之间已有的空格

    Returns
    -------
    str
        处理后的文本
    """
    # 0) 把所有空白字符先压成单空格，方便后面统一处理
    s = re.sub(r"\s+", " ", text)

    # 1) 永远删掉汉字之间的空格
    s = re.sub(_RM_CN_SPACE, r"\1\2", s)

    # 2) 根据开关删掉“该删的空格”
    for flag, key in zip(
        (cn_en, cn_digit, en_digit),
        ("cn_en", "cn_digit", "en_digit"),
    ):
        if not flag:  # 开关 = False ➜ 删空格
            for pat in _RM_PAT[key]:
                s = re.sub(pat, r"\1\2", s)

    # 3) 再压一次，防止出现“双空格”
    s = re.sub(r"\s+", " ", s)

    # 4) 根据开关补上“该补的空格”
    for flag, key in zip(
        (cn_en, cn_digit, en_digit),
        ("cn_en", "cn_digit", "en_digit"),
    ):
        if flag:  # 开关 = True ➜ 插空格
            for pat in _INS_PAT[key]:
                s = re.sub(pat, r"\1 \2", s)

    # 5) 最终收尾：压缩 & 去首尾空白
    return re.sub(r"\s+", " ", s).strip()
