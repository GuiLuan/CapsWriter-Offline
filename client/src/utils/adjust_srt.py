import uuid
from pathlib import Path

from . import srt_from_txt
from ..mtypes import console

__all__ = ["adjust_srt"]


def adjust_srt(file: Path):
    # 生成任务 id
    task_id = str(uuid.uuid1())
    console.print(f"\n任务标识：{task_id}")
    console.print(f"    处理文件：{file}")

    # 调整 srt
    srt_from_txt.one_task(file)
    console.print("    [green]srt 调整完成")
