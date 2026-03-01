#!/usr/bin/env python3

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="生成测试语音并调用 ASR 接口，支持纯转写或 ASR+workflow 联调。"
    )
    parser.add_argument(
        "--mode",
        choices=("transcribe", "workflow"),
        default="transcribe",
        help="transcribe: 只调用 /asr/transcribe；workflow: 调用 /asr/workflow",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="服务地址，如 http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--text",
        default="帮我明天下午三点提醒我开会",
        help="用于生成测试语音的文本",
    )
    parser.add_argument(
        "--voice",
        default="Tingting",
        help="macOS say 使用的声音",
    )
    parser.add_argument(
        "--audio-format",
        default="wav",
        help="上传给接口的 audio_format 字段，默认 wav",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="上传给接口的 sample_rate 字段，默认 16000",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="curl 请求超时时间（秒）",
    )
    parser.add_argument(
        "--save-audio",
        default="",
        help="可选，保存生成后的 wav 路径",
    )
    return parser.parse_args()


def check_binary(cmd: str) -> None:
    if shutil.which(cmd):
        return
    raise RuntimeError(f"缺少命令: {cmd}")


def run_cmd(cmd: list[str]) -> str:
    completed = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        details = stderr or stdout or "unknown error"
        raise RuntimeError(f"命令失败: {' '.join(cmd)}\n{details}")
    return completed.stdout


def generate_wav(text: str, voice: str, sample_rate: int, output_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        aiff_path = temp_path / "tts.aiff"
        run_cmd(["say", "-v", voice, "-o", str(aiff_path), text])
        run_cmd(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(aiff_path),
                "-ac",
                "1",
                "-ar",
                str(sample_rate),
                str(output_path),
            ]
        )


def call_api(
    mode: str,
    base_url: str,
    wav_path: Path,
    audio_format: str,
    sample_rate: int,
    timeout: int,
) -> dict:
    endpoint = "/api/v1/asr/transcribe" if mode == "transcribe" else "/api/v1/asr/workflow"
    url = f"{base_url.rstrip('/')}{endpoint}"
    cmd = [
        "curl",
        "-sS",
        "--max-time",
        str(timeout),
        "-X",
        "POST",
        url,
        "-F",
        f"audio_file=@{wav_path}",
        "-F",
        f"audio_format={audio_format}",
        "-F",
        f"sample_rate={sample_rate}",
    ]
    raw = run_cmd(cmd).strip()
    if not raw:
        raise RuntimeError("服务返回为空")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"返回非 JSON: {raw}") from exc


def main() -> int:
    args = parse_args()

    for binary in ("say", "ffmpeg", "curl"):
        check_binary(binary)

    target_wav = Path(args.save_audio).expanduser().resolve() if args.save_audio else None
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_wav = Path(temp_dir) / "tts_16k.wav"
        generate_wav(
            text=args.text,
            voice=args.voice,
            sample_rate=args.sample_rate,
            output_path=temp_wav,
        )
        if target_wav:
            target_wav.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(temp_wav, target_wav)
            wav_path = target_wav
        else:
            wav_path = temp_wav

        result = call_api(
            mode=args.mode,
            base_url=args.base_url,
            wav_path=wav_path,
            audio_format=args.audio_format,
            sample_rate=args.sample_rate,
            timeout=args.timeout,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if "asr_text" in result:
        print(f"\nASR_TEXT: {result['asr_text']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
