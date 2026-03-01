import json
import time
from threading import Event
from typing import Any

from app.config import require_env

try:
    import nls
except ImportError:  # pragma: no cover - runtime dependency
    nls = None


def _try_parse_json(data: Any) -> Any:
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data
    return data


def _extract_text(message: Any) -> str:
    parsed = _try_parse_json(message)

    if isinstance(parsed, str):
        return parsed
    if not isinstance(parsed, dict):
        return ""

    payload = parsed.get("payload")
    if isinstance(payload, dict):
        result = payload.get("result")
        result = _try_parse_json(result)
        if isinstance(result, dict):
            for key in ("text", "result", "sentence"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value
        elif isinstance(result, str) and result.strip():
            return result

    for key in ("text", "result", "sentence"):
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            return value

    return ""


class _SingleRecognizer:
    def __init__(self, url: str, token: str, appkey: str):
        if nls is None:
            raise RuntimeError("缺少nls依赖，请先按阿里云文档安装Python SDK")
        self._text = ""
        self._error = ""
        self._done = Event()
        self._recognizer = nls.NlsSpeechRecognizer(
            url=url,
            token=token,
            appkey=appkey,
            on_start=self._on_start,
            on_result_changed=self._on_result_changed,
            on_completed=self._on_completed,
            on_error=self._on_error,
            on_close=self._on_close,
            callback_args=[],
        )

    def _on_start(self, message, *args):
        return None

    def _on_result_changed(self, message, *args):
        text = _extract_text(message)
        if text:
            self._text = text

    def _on_completed(self, message, *args):
        text = _extract_text(message)
        if text:
            self._text = text
        self._done.set()

    def _on_error(self, message, *args):
        self._error = _extract_text(message) or str(message)
        self._done.set()

    def _on_close(self, *args):
        return None

    def run(
        self,
        audio_bytes: bytes,
        audio_format: str,
        sample_rate: int,
        chunk_size: int = 640,
        send_interval_seconds: float = 0.01,
        timeout_seconds: float = 30.0,
    ) -> str:
        if not audio_bytes:
            raise ValueError("audio_bytes is empty")

        start_ret = self._recognizer.start(
            aformat=audio_format,
            sample_rate=sample_rate,
            enable_intermediate_result=True,
            enable_punctuation_prediction=True,
            enable_inverse_text_normalization=True,
        )
        if not start_ret:
            raise RuntimeError("ASR session start failed")

        for offset in range(0, len(audio_bytes), chunk_size):
            self._recognizer.send_audio(audio_bytes[offset : offset + chunk_size])
            time.sleep(send_interval_seconds)

        self._recognizer.stop()
        self._done.wait(timeout=timeout_seconds)

        if self._error:
            raise RuntimeError(f"ASR error: {self._error}")
        if not self._text.strip():
            raise RuntimeError("ASR did not return recognized text")
        return self._text.strip()


def single_recognize(
    audio_bytes: bytes,
    url: str = "",
    audio_format: str = "pcm",
    sample_rate: int = 16000,
) -> str:
    asr_url = url or require_env("DEFAULT_ASR_URL")
    token = require_env("TOKEN")
    appkey = require_env("APPKEY")
    recognizer = _SingleRecognizer(url=asr_url, token=token, appkey=appkey)
    return recognizer.run(
        audio_bytes=audio_bytes,
        audio_format=audio_format,
        sample_rate=sample_rate,
    )
