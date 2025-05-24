import time
from platform import system
from multiprocessing import Queue

from . import load_model
from ..utils import console, load_config, empty_current_working_set, Task


def recognize_service(queue_in: Queue, queue_out: Queue, socket_id):
    config = load_config()
    recognizer_config = config["recognize_model"]
    punctuator_config = config["punc_model"]

    t1 = time.time()
    console.print("[yellow]语音模型载入中", end="\r")
    recognizer = load_model(recognizer_config["_type"], **recognizer_config)
    console.print("[green4]语音模型载入完成", end="\n\n")
    console.print(f"[green4]语音模型载入耗时：{time.time() - t1}", end="\n\n")

    t2 = time.time()
    punctuator = None
    if punctuator_config["_enable"] is True:

        def disable_jieba_debug():
            # 关闭 jieba 的 debug
            import jieba
            import logging

            jieba.setLogLevel(logging.INFO)

        disable_jieba_debug()

        console.print("[yellow]标点模型载入中", end="\r")
        punctuator = load_model(punctuator_config["_type"], **punctuator_config)
        console.print("[green4]标点模型载入完成", end="\n\n")
        console.print(f"[green4]标点模型载入耗时：{time.time() - t2}", end="\n\n")

    console.print(f"模型加载总耗时 {time.time() - t1:.2f}s", end="\n\n")

    if system() == "Windows":
        empty_current_working_set()

    queue_out.put(True)  # 通知主进程服务已准备就绪

    while True:
        try:
            task: Task = queue_in.get(timeout=1)
        except KeyboardInterrupt:
            return
        except Exception as _:
            continue

        if task.socket_id not in socket_id:
            continue

        result = recognizer(task)
        if punctuator is not None:
            result.text = punctuator(result.text).text

        queue_out.put(result)
