import asyncio
from typing import AsyncIterator, Optional

import numpy as np

from .base import AudioSink, AudioSource


class LocalAudioSource(AudioSource):
    def __init__(
        self,
        sampling_rate: int,
        frames_per_buffer: int,
        input_device_index: Optional[int] = None,
    ):
        self.sampling_rate = sampling_rate
        self.frames_per_buffer = frames_per_buffer
        self.input_device_index = input_device_index

    async def __aenter__(self):
        import pyaudio

        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            rate=self.sampling_rate,
            channels=1,
            format=pyaudio.paFloat32,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
            input_device_index=self.input_device_index,
        )
        self.stream.start_stream()
        return self

    async def __aexit__(self, *_, **__):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    async def __aiter__(self) -> AsyncIterator[np.ndarray]:
        while self.stream.is_active():
            audio_bytes = await asyncio.to_thread(
                self.stream.read, self.frames_per_buffer
            )
            yield np.frombuffer(audio_bytes, dtype=np.float32)

    def is_active(self) -> bool:
        return self.stream.is_active()


class LocalAudioSink(AudioSink):
    def __init__(
        self,
        sampling_rate: int,
        output_device_index: Optional[int] = None,
    ):
        self.sampling_rate = sampling_rate
        self.output_device_index = output_device_index

    async def __aenter__(self):
        import pyaudio

        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            rate=self.sampling_rate,
            channels=1,
            format=pyaudio.paFloat32,
            output=True,
            output_device_index=self.output_device_index,
        )

        self.stream.start_stream()
        return self

    async def __aexit__(self, *args, **kwargs):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    async def write(self, audio: np.ndarray):
        await asyncio.to_thread(self.stream.write, audio.tobytes())
