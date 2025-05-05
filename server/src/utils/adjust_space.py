import re
from string import digits

__all__ = ["adjust_space"]

en_in_zh = re.compile(r"""(?ix)    # i 表示忽略大小写，x 表示开启注释模式
    ([\u4e00-\u9fa5]|[a-z0-9]+\s)?      # 左侧是中文，或者英文加空格
    ([a-z0-9 ]+)                    # 中间是一个或多个「英文数字加空格」
    ([\u4e00-\u9fa5]|[a-z0-9]+)?       # 右是中文，或者英文加空格
""")


def replacer(original: re.Match) -> str:
    """
    格式化中英文混合文本的间距
    功能：
    1. 移除英文单词中间的多余空格
    2. 在中英文之间添加适当空格
    3. 正确处理数字边界情况

    参数:
        original: 正则匹配对象，应包含3个捕获组:
            group(1): 左侧文本
            group(2): 中间文本(主要处理部分)
            group(3): 右侧文本

    返回:
        格式化后的字符串
    """

    def _remove_inner_spaces(text: str) -> str:
        """移除英文单词中间的多余空格"""
        if not text:
            return text
        # 优化后的正则表达式，同时处理数字前缀情况
        return re.sub(r"((\d) )?(\b\w) ?(?!\w{2})", r"\2\3", text).strip()

    def _process_left_connection(left: str, center: str, original: re.Match) -> str:
        """处理文本左侧连接"""
        if not left:
            # 检查前一个字符是否是中文
            if original.start(2) > 0 and re.match(
                r"[\u4e00-\u9fa5]", original.string[original.start(2) - 1]
            ):
                return " " + center if center.lstrip(digits) == center else center
            return center

        # 左侧有文本时的处理
        result = left.rstrip()
        if (
            left.strip(digits) == left  # 左侧结尾不是数字
            and center.lstrip(digits) == center
        ):  # 中间开头不是数字
            result += " "
        return result + center

    def _process_right_connection(current: str, right: str) -> str:
        """处理文本右侧连接"""
        if not right:
            return current

        if current.rstrip(digits) == current:  # 当前文本结尾不是数字
            current += " "
        return current + right.lstrip()

    # 提取匹配组并去除两端空格
    left: str = original.group(1) or ""
    center: str = original.group(2) or ""
    right: str = original.group(3) or ""

    # 预处理：移除英文中间的多余空格
    processed_center = _remove_inner_spaces(center)

    # 处理左侧连接
    final = _process_left_connection(left, processed_center, original)

    # 处理右侧连接
    final = _process_right_connection(final, right)

    return final


def adjust_space(txt):
    return en_in_zh.sub(replacer, txt)
