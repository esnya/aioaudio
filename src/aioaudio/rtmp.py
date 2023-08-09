from asyncio import StreamWriter, subprocess

import numpy as np

from . import AudioSink


class RTMPAudioSink(AudioSink):
    def __init__(self, sampling_rate: int, format: str, channels: int, url: str):
        self.sampling_rate = sampling_rate
        self.format = format
        self.channels = channels
        self.url = url

    async def __aenter__(self) -> StreamWriter:
        self.ffmpeg = await subprocess.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-re",
            "-f",
            self.format,
            "-ar",
            str(self.sampling_rate),
            "-ac",
            str(self.channels),
            "-i",
            "-",
            "-acodec",
            "aac",
            "-strict",
            "experimental",
            "-f",
            "flv",
            self.url,
            stdin=subprocess.PIPE,
        )
        self.stdin = self.ffmpeg.stdin
        assert self.stdin, "Failed to open pipe"

        return self.stdin

    async def __aexit__(self, *args, **kwargs) -> None:
        if self.stdin:
            self.stdin.close()
        else:
            self.ffmpeg.kill()
        await self.ffmpeg.wait()

    async def write(self, data: np.ndarray) -> None:
        assert self.stdin, "Pipe not open"
        self.stdin.write(data.tobytes())
        await self.stdin.drain()
