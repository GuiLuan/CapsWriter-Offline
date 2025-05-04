import re
import time
import numpy as np

from ..types.task import Task, Result
from ..utils.chinese_itn import chinese_to_num
from ..utils.format_tools import adjust_space
from ..config import ServerConfig as Config

__all__ = ["recognize"]


RESULTS = {}


def recognize(recognizer, punc_model, task: Task) -> Result:
    """主识别函数，协调各子函数完成语音识别流程"""
    # 确保结果容器存在
    result = _ensure_result_container(task)

    # 记录识别时间
    result.time_start = task.time_start
    result.time_submit = task.time_submit

    # 处理音频片段
    samples, duration = _process_audio_segment(result, task)

    # 执行识别
    stream = _perform_recognition(recognizer, samples, task.samplerate)

    # 去重处理
    m, n = _deduplicate_timestamps(
        stream, result, duration, task.overlap, task.is_final
    )

    # 合并结果
    _merge_results(result, stream, m, n, task.offset)

    # 格式化文本
    result.text = _format_text(result.tokens)

    if not task.is_final:
        return result

    # 最终处理
    result.text = format_text(result.text, punc_model)
    result.time_complete = time.time()
    result.is_final = True
    result = RESULTS.pop(task.task_id)
    return result


def format_text(text, punc_model):
    if Config.format_spell:
        text = adjust_space(text)  # 调空格
    if Config.format_punc and punc_model and text:
        text = punc_model(text)[0]  # 加标点
    if Config.format_num:
        text = chinese_to_num(text)  # 转数字
    if Config.format_spell:
        text = adjust_space(text)  # 调空格
    return text


def _ensure_result_container(task: Task) -> Result:
    """确保结果容器存在并返回"""
    if task.task_id not in RESULTS:
        RESULTS[task.task_id] = Result(task.task_id, task.socket_id, task.source)
    return RESULTS[task.task_id]


def _process_audio_segment(result: Result, task: Task) -> tuple[np.ndarray, float]:
    """处理音频片段数据并返回样本和持续时间"""
    samples = np.frombuffer(task.data, dtype=np.float32)
    duration = len(samples) / task.samplerate
    result.duration += duration - task.overlap
    if task.is_final:
        result.duration += task.overlap
    return samples, duration


def _perform_recognition(recognizer, samples: np.ndarray, samplerate: int):
    """执行语音识别并返回识别流"""
    stream = recognizer.create_stream()
    stream.accept_waveform(samplerate, samples)
    recognizer.decode_stream(stream)
    return stream


def _deduplicate_timestamps(
    stream, result: Result, duration: float, overlap: float, is_final: bool
) -> tuple[int, int]:
    """处理时间戳去重并返回有效范围(m,n)"""
    m = n = len(stream.result.timestamps)

    # 粗去重：基于时间戳
    for i, timestamp in enumerate(stream.result.timestamps, start=0):
        if timestamp > overlap / 2:
            m = i
            break
    for i, timestamp in enumerate(stream.result.timestamps, start=1):
        n = i
        if timestamp > duration - overlap / 2:
            break

    if not result.timestamps:
        m = 0
    if is_final:
        n = len(stream.result.timestamps)

    # 细去重：基于重复token
    if result.tokens and result.tokens[-2:] == stream.result.tokens[m:n][:2]:
        m += 2
    elif result.tokens and result.tokens[-1:] == stream.result.tokens[m:n][:1]:
        m += 1

    return m, n


def _merge_results(result: Result, stream, m: int, n: int, offset: float):
    """合并识别结果到最终结果"""
    result.timestamps += [t + offset for t in stream.result.timestamps[m:n]]
    result.tokens += [token for token in stream.result.tokens[m:n]]


def _format_text(tokens: list[str]) -> str:
    """格式化token为文本"""
    text = " ".join(tokens).replace("@@ ", "")
    return re.sub("([^a-zA-Z0-9]) (?![a-zA-Z0-9])", r"\1", text)
