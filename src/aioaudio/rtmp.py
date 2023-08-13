import asyncio
from time import time
from typing import Optional
import numpy as np

from .ffmpeg import F2N, ffmpeg_sink


from .base import AudioSink


class RTMPAudioSink(AudioSink):
    def __init__(
        self,
        sampling_rate: int,
        format: str,
        channels: int,
        url: str,
        keep_alive_interval: Optional[int] = None,
    ):
        self.sampling_rate = sampling_rate
        self.format = format
        self.channels = channels
        self.url = url
        self.keep_alive_interval = keep_alive_interval

    async def __aenter__(self) -> "RTMPAudioSink":
        self.ffmpeg, self.stdin = await ffmpeg_sink(
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
        )
        self.keep_alive_task = asyncio.create_task(self._keep_alive_loop())
        self.dtype = F2N[self.format]
        self.zeros = np.zeros((self.sampling_rate, self.channels), dtype=self.dtype)
        self.last_written_time = 0
        return self

    async def _keep_alive_loop(self) -> None:
        if not self.keep_alive_interval:
            return

        while self.ffmpeg.returncode is None:
            await asyncio.sleep(self.keep_alive_interval)
            if time() - self.last_written_time < self.keep_alive_interval:
                continue
            await self.write(self.zeros)

    async def __aexit__(self, *args, **kwargs) -> None:
        if self.stdin:
            self.stdin.close()
        else:
            self.ffmpeg.kill()
        await self.ffmpeg.wait()

    async def write(self, data: np.ndarray) -> None:
        assert self.stdin, "Pipe not open"
        self.stdin.write(data.tobytes())
        self.last_written_time = time()
        await self.stdin.drain()
