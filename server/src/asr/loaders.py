import re
import time
from abc import ABC, abstractmethod
from typing import Literal, Dict

import numpy as np
import sherpa_onnx
import funasr_onnx

from ..utils import Task, Result


__all__ = ["load_model"]


RESULTS = {}


class BaseLoader(ABC):
    @abstractmethod
    def load(self, **kwargs):
        return self

    @abstractmethod
    def __call__(self, *args, **kwargs) -> Result: ...


class ParaformerLoader(BaseLoader):
    def load(self, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}
        self._model = sherpa_onnx.OfflineRecognizer.from_paraformer(**kwargs)
        return self

    def __call__(self, task: Task, *args, **kwargs):
        return self._sherpa_recognize(self._model, task, *args, **kwargs)

    def _sherpa_recognize(
        self, recognizer: sherpa_onnx.OfflineRecognizer, task: Task
    ) -> Result:
        # 确保结果容器存在
        result = self._ensure_result_container(task)

        # 记录识别时间
        result.time_start = task.time_start
        result.time_submit = task.time_submit

        # 处理音频片段
        samples, duration = self._process_audio_segment(result, task)

        # 执行识别
        stream = self._perform_recognition(recognizer, samples, task.samplerate)

        # 去重处理
        m, n = self._deduplicate_timestamps(
            stream, result, duration, task.overlap, task.is_final
        )

        # 合并结果
        self._merge_results(result, stream, m, n, task.offset)

        # 格式化文本
        result.text = self._format_text(result.tokens)

        if not task.is_final:
            return result

        # 最终处理
        result.time_complete = time.time()
        result.is_final = True
        result = RESULTS.pop(task.task_id)
        return result

    def _ensure_result_container(self, task: Task) -> Result:
        """确保结果容器存在并返回"""
        if task.task_id not in RESULTS:
            RESULTS[task.task_id] = Result(task.task_id, task.socket_id, task.source)
        return RESULTS[task.task_id]

    def _process_audio_segment(
        self, result: Result, task: Task
    ) -> tuple[np.ndarray, float]:
        """处理音频片段数据并返回样本和持续时间"""
        samples = np.frombuffer(task.data, dtype=np.float32)
        duration = len(samples) / task.samplerate
        result.duration += duration - task.overlap
        if task.is_final:
            result.duration += task.overlap
        return samples, duration

    def _perform_recognition(self, recognizer, samples: np.ndarray, samplerate: int):
        """执行语音识别并返回识别流"""
        stream = recognizer.create_stream()
        stream.accept_waveform(samplerate, samples)
        recognizer.decode_stream(stream)
        return stream

    def _deduplicate_timestamps(
        self, stream, result: Result, duration: float, overlap: float, is_final: bool
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

    def _merge_results(self, result: Result, stream, m: int, n: int, offset: float):
        """合并识别结果到最终结果"""
        result.timestamps += [t + offset for t in stream.result.timestamps[m:n]]
        result.tokens += [token for token in stream.result.tokens[m:n]]

    def _format_text(self, tokens: list[str]) -> str:
        """格式化token为文本"""
        text = " ".join(tokens).replace("@@ ", "")
        return re.sub("([^a-zA-Z0-9]) (?![a-zA-Z0-9])", r"\1", text)


class SensevoiceLoader(ParaformerLoader):
    def load(self, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}
        self._model = sherpa_onnx.OfflineRecognizer.from_sense_voice(**kwargs)
        return self


class CttransformerLoader(BaseLoader):
    def load(self, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}
        self._model = funasr_onnx.CT_Transformer(**kwargs)
        return self

    def __call__(self, *args, **kwargs) -> Result:
        # fake result
        result = Result(task_id=-1, socket_id=-1, source=-1)
        result.text = self._model(*args, **kwargs)[0]
        return result


LoaderName = Literal["paraformer", "sensevoice", "cttransformer"]

LOADERS: Dict[LoaderName, type[BaseLoader]] = {
    "paraformer": ParaformerLoader,
    "sensevoice": SensevoiceLoader,
    "cttransformer": CttransformerLoader,
}


def load_model(loader_name: LoaderName, *args, **kwargs):
    try:
        loader_cls = LOADERS[loader_name]
    except KeyError:
        raise ValueError(f"Unsupported loader_name: {loader_name!r}")

    return loader_cls().load(*args, **kwargs)
