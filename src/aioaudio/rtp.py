from asyncio import subprocess
import asyncio
from typing import AsyncContextManager, AsyncIterator

import numpy as np
from . import AudioSource, AudioSink


class RTPAudioSource(AudioSource):
    def __init__(
        self,
        bytes_per_buffer: int,
        sampling_rate: int,
        url: str = "rtp://localhost:1234",
    ):
        self.bytes_per_buffer = bytes_per_buffer
        self.sampling_rate = sampling_rate
        self.url = url

    async def __aenter__(self):
        self.ffmpeg = await subprocess.create_subprocess_exec(
            "ffmpeg",
            "-i",
            self.url,
            "-acodec",
            "copy",
            "-f",
            "wav",
            "-",
            stdout=subprocess.PIPE,
        )
        pipe = self.ffmpeg.stdout
        assert pipe is not None
        self.pipe = pipe
        return self

    async def __aexit__(self, *args, **kwargs):
        self.ffmpeg.kill()
        await self.ffmpeg.wait()

    async def __aiter__(self) -> AsyncIterator[np.ndarray]:
        while self.is_active():
            data = await self.pipe.read(self.bytes_per_buffer)
            yield np.frombuffer(data, dtype=np.float32)

    def is_active(self) -> bool:
        return self.ffmpeg.returncode is None


class RTPAudioSink(AudioSink):
    def __init__(
        self,
        sampling_rate: int,
        url: str = "rtp://localhost:1234",
    ):
        self.sampling_rate = sampling_rate
        self.url = url

    async def __aenter__(self):
        self.ffmepg = await subprocess.create_subprocess_exec(
            "ffmpeg",
            "-i",
            "pipe:0",
            "-acodec",
            "copy",
            "-ar",
            str(self.sampling_rate),
            "-ac",
            str(1),
            "-f",
            "rtp",
            self.url,
            stdin=subprocess.PIPE,
        )
        pipe = self.ffmepg.stdin
        assert pipe is not None
        self.pipe = pipe
        return self

    async def __aexit__(self, *args, **kwargs):
        self.pipe.close()
        await self.ffmepg.wait()

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
        self.ffmpeg = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-f",
            "dshow",
            "-i",
            f'audio="{self.audio_device_name}"',
            "-acodec",
            "copy",
            "-ar",
            str(self.sampling_rate),
            "-ac",
            str(1),
            "-f",
            "rtp",
            self.url,
        )
        return self

    async def __aexit__(self, *args, **kwargs):
        self.ffmpeg.kill()
        await self.ffmpeg.wait()


class RTPToLocalAudio(AsyncContextManager):
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
        self.ffmpeg = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i",
            self.url,
            "-acodec",
            "copy",
            "-f",
            "wav",
            "pipe:1",
            stdout=subprocess.PIPE,
        )
        pipe_out = self.ffmpeg.stdout
        assert pipe_out is not None
        self.pipe_out = pipe_out

        self.ffplayt = await asyncio.create_subprocess_exec(
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-i",
            "-",
            stdin=subprocess.PIPE,
        )
        pipe_in = self.ffplayt.stdin
        assert pipe_in is not None
        self.pipe_in = pipe_in

        async for data in pipe_out:
            pipe_in.write(data)

        return self

    async def __aexit__(self, *args, **kwargs):
        self.ffmpeg.kill()
        self.ffplayt.kill()
        await asyncio.gather(self.ffmpeg.wait(), self.ffplayt.wait())
