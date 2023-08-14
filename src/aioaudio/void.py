import numpy as np

from .base import AudioSink, AudioSource


class VoidAudioSource(AudioSource):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_, **__):
        pass

    async def __aiter__(self):
        if False:
            yield np.array([])

    def is_active(self) -> bool:
        return False


class VoidAudioSink(AudioSink):
    async def __aexit__(self, *_, **__):
        pass

    async def write(self, audio: np.ndarray):
        pass
