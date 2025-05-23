import asyncio
import platform

import pyclip
import keyboard

from ..config import ClientConfig as Config

__all__ = ["type_result"]


async def type_result(text):
    # 模拟粘贴
    if Config.paste:
        # 保存剪切板
        try:
            temp = pyclip.paste()
            if isinstance(temp, bytes):
                temp = temp.decode("utf-8")
        except Exception as _:
            temp = ""

        # 复制结果
        pyclip.copy(text)

        # 粘贴结果
        if platform.system() == "Darwin":
            keyboard.press(55)
            keyboard.press(9)
            keyboard.release(55)
            keyboard.release(9)
        else:
            keyboard.send("ctrl + v")

        # 还原剪贴板
        if Config.restore_clip:
            await asyncio.sleep(0.1)
            pyclip.copy(temp)

    # 模拟打印
    else:
        keyboard.write(text)
