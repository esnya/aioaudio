from abc import abstractmethod
from typing import AsyncContextManager, AsyncIterable, AsyncIterator
import numpy as np


class AudioSource(AsyncContextManager, AsyncIterable[np.ndarray]):
    @abstractmethod
    def is_active(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[np.ndarray]:
        raise NotImplementedError()


class AudioSink(AsyncContextManager):
    @abstractmethod
    async def write(self, audio: np.ndarray):
        raise NotImplementedError()

    async def __call__(self, audio_stream: AsyncIterable[np.ndarray]):
        async for audio in audio_stream:
            await self.write(audio)
