import time
from pathlib import Path
from os import makedirs

from .hot_word_kwd import kwd_list

__all__ = ["create_markdown_file", "write_markdown_file"]

header_md = r"""```txt
正则表达式 Tip

匹配到音频文件链接：\[(.+)\]\((.{10,})\)[\s]*
替换为 HTML 控件：<audio controls><source src="$2" type="audio/mpeg">$1</audio>\n\n

匹配 HTML 控件：<audio controls><source src="(.+)" type="audio/mpeg">(.+)</audio>\n\n
替换为文件链接：[$2]($1) 
```


"""


def create_markdown_file(file_md):
    with open(file_md, "w", encoding="utf-8") as f:
        f.write(header_md)


def write_markdown_file(text: str, time_start: float, file_audio: Path):
    time_year = time.strftime("%Y", time.localtime(time_start))
    time_month = time.strftime("%m", time.localtime(time_start))
    time_day = time.strftime("%d", time.localtime(time_start))
    time_hms = time.strftime("%H:%M:%S", time.localtime(time_start))
    folder_path = Path() / time_year / time_month
    makedirs(folder_path, exist_ok=True)

    # 列表内的元素是元组，元组内包含了：关键词、md路径
    md_list = [
        (kwd, folder_path / f"{kwd + '-' if kwd else ''}{time_day}.md")
        for kwd in kwd_list
        if text.startswith(kwd)
    ]

    # 为 md 文件写入识别记录
    for kwd, file_md in md_list:
        # 确保 md 文件存在
        if not file_md.exists():
            create_markdown_file(file_md)

        # 写入 md
        with open(file_md, "a", encoding="utf-8") as f:
            path_ = (
                file_audio.relative_to(file_md.parent).as_posix().replace(" ", "%20")
            )
            text_ = text[len(kwd) :].lstrip("，。,.")
            f.write(f"[{time_hms}]({path_}) {text_}\n\n")
