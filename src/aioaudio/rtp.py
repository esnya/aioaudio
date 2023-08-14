import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import AsyncContextManager, AsyncIterator

import numpy as np

from .base import AudioSink, AudioSource
from .ffmpeg import F2N, ffmpeg_sink, ffmpeg_source


class RTPAudioSource(AudioSource):
    def __init__(
        self,
        sdp: str,
        format: str = "f32le",
        frames_per_buffer: int = 1024,
    ):
        self.format = format
        self.sdp = sdp
        self.frames_per_buffer = frames_per_buffer
        self.dtype = F2N[format]
        self.bytes_per_buffer = self.frames_per_buffer * self.dtype.itemsize

    async def __aenter__(self):
        with TemporaryDirectory() as dir:
            sdp_path = Path(dir) / "sdp"
            sdp_path.write_text(self.sdp)

            self.ffmpeg, self.stdout = await ffmpeg_source(
                "-y",
                "-protocol_whiltelist",
                "file,rtp,udp",
                "-i",
                str(sdp_path),
                "-f",
                self.format,
                "-",
            )
        return self

    async def __aexit__(self, *args, **kwargs):
        self.ffmpeg.kill()
        await self.ffmpeg.wait()

    async def __aiter__(self) -> AsyncIterator[np.ndarray]:
        while self.is_active():
            data = await self.stdout.read(self.bytes_per_buffer)
            yield np.frombuffer(data, dtype=self.dtype)

    def is_active(self) -> bool:
        return self.ffmpeg.returncode is None


class RTPAudioSink(AudioSink):
    def __init__(
        self,
        sampling_rate: int,
        format: str = "f32le",
        channels: int = 1,
        url: str = "rtp://localhost:1234",
    ):
        self.sampling_rate = sampling_rate
        self.format = format
        self.channels = channels
        self.url = url

    async def __aenter__(self):
        self.ffmpeg, self.pipe = await ffmpeg_sink(
            "-y",
            "-i",
            "pipe:0",
            "-acodec",
            "copy",
            "-ar",
            str(self.sampling_rate),
            "-ac",
            str(self.channels),
            "-f",
            "rtp",
            self.url,
        )
        return self

    async def __aexit__(self, *args, **kwargs):
        self.pipe.close()
        await self.ffmpeg.wait()

    async def write(self, audio: np.ndarray):
        self.pipe.write(audio.tobytes())
        await self.pipe.drain()


class LocalAudioToRTP(AsyncContextManager):
    def __init__(
        self,
        sampling_rate: int,
        audio_device_name: str,
        url: str = "rtp://localhost:1234",
    ):
        self.sampling_rate = sampling_rate
        self.url = url
        self.audio_device_name = audio_device_name

    async def __aenter__(self):
        with TemporaryDirectory() as dir:
            dir_path = Path(dir)
            sdp_path = dir_path / "sdp"
            self.ffmpeg = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-f",
                "dshow",
                "-i",
                f"audio={self.audio_device_name}",
                "-acodec",
                "pcm_s16le",
                "-ar",
                str(self.sampling_rate),
                "-ac",
                str(1),
                "-f",
                "rtp",
                self.url,
                "-sdp_file",
                sdp_path,
            )
            while True:
                await asyncio.sleep(0.1)

                if not sdp_path.exists():
                    continue

                sdp = sdp_path.read_text()
                if not sdp:
                    continue
                self.sdp = sdp

                break
        return self

    async def __aexit__(self, *args, **kwargs):
        self.ffmpeg.kill()
        await self.ffmpeg.wait()


class RTPToLocalAudio(AsyncContextManager):
    def __init__(
        self,
        sdp: str,
    ):
        self.sdp = sdp

    async def __aenter__(self):
        with TemporaryDirectory() as dir:
            sdp_path = Path(dir) / "sdp"
            sdp_path.write_text(self.sdp)

            print(sdp_path.read_text())

            self.ffplay = await asyncio.create_subprocess_exec(
                "ffplay",
                "-protocol_whiltelist",
                "file,rtp,udp",
                str(sdp_path),
            )

        return self

    async def __aexit__(self, *args, **kwargs):
        self.ffplay.kill()
        await self.ffplay.wait()
