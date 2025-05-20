import time
import signal
from multiprocessing import Queue
from platform import system
from typing import Union

from funasr_onnx import CT_Transformer

from . import recognize, load_model
from ..mtypes import console
from ..utils import empty_current_working_set
from ..config import ServerConfig as Config


def disable_jieba_debug():
    # 关闭 jieba 的 debug
    import jieba
    import logging

    jieba.setLogLevel(logging.INFO)


def recognizer_service(queue_in: Queue, queue_out: Queue, sockets_id):
    # Ctrl-C 退出
    signal.signal(signal.SIGINT, lambda signum, frame: exit())

    disable_jieba_debug()

    # 载入语音模型
    t1 = time.time()
    console.print("[yellow]语音模型载入中", end="\r")
    recognizer = load_model(Config.recognize_model_args)
    console.print("[green4]语音模型载入完成", end="\n\n")
    console.print(f"[green4]语音模型载入耗时：{time.time() - t1}", end="\n\n")

    # 载入标点模型
    t2 = time.time()
    punc_model: Union[None, CT_Transformer] = None
    if Config.punc_model_args is not None:
        console.print("[yellow]标点模型载入中", end="\r")
        punc_model = load_model(Config.punc_model_args)  # type: ignore
        console.print("[green4]标点模型载入完成", end="\n\n")
        console.print(f"[green4]标点模型载入耗时：{time.time() - t2}", end="\n\n")
    console.print(f"模型加载总耗时 {time.time() - t1:.2f}s", end="\n\n")

    # 清空物理内存工作集
    if system() == "Windows":
        empty_current_working_set()

    queue_out.put(True)  # 通知主进程加载完了

    while True:
        # 从队列中获取任务消息
        # 阻塞最多1秒，便于中断退出
        try:
            task = queue_in.get(timeout=1)
        except Exception as _:
            continue

        if task.socket_id not in sockets_id:  # 检查任务所属的连接是否存活
            continue

        result = recognize(recognizer, task)
        if punc_model is not None:
            result.text = punc_model(result.text)[0]
        queue_out.put(result)
