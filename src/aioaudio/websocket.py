from abc import abstractmethod
import asyncio
import json
import logging
from typing import AsyncContextManager, AsyncIterator, Set, Union
import numpy as np
from websockets.client import connect, WebSocketClientProtocol
from websockets.server import WebSocketServerProtocol, serve

from . import AudioSource, AudioSink

WebSocketProtocol = Union[WebSocketServerProtocol, WebSocketClientProtocol]

logger = logging.getLogger(__name__)


class WebsocketBaseAudioMixin(AsyncContextManager):
    def __init__(
        self, sampling_rate: int, host: str = "localhost", port: int = 8765, **kwargs
    ):
        self.sampling_rate = sampling_rate
        self.kwargs = kwargs

    async def _handle(self, websocket: WebSocketProtocol):
        raise NotImplementedError()

    async def _on_connection(self, websocket: WebSocketProtocol):
        await websocket.send(
            json.dumps(dict(sampling_rate=self.sampling_rate, channels=1))
        )
        await self._handle(websocket)


class WebsocketServerAudioMixin(WebsocketBaseAudioMixin):
    def __init__(
        self, sampling_rate: int, host: str = "localhost", port: int = 8765, **kwargs
    ):
        super().__init__(sampling_rate, **kwargs)
        self.host = host
        self.port = port

    async def __aenter__(self):
        self.server = await serve(
            self._on_connection, self.host, self.port, **self.kwargs
        )
        await self.server.__aenter__()
        return self

    async def __aexit__(self, *args, **kwargs):
        self.server.close()
        await self.server.wait_closed()


class WebsocketClientAudioMixin(WebsocketBaseAudioMixin):
    def __init__(self, sampling_rate: int, url: str = "ws://localhost:8765", **kwargs):
        super().__init__(sampling_rate, **kwargs)
        self.url = url

    async def __aenter__(self):
        self.connection = await connect(self.url, **self.kwargs)
        await self.connection.send(
            json.dumps(dict(sampling_rate=self.sampling_rate, channels=1))
        )
        await self._handle(self.connection)
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.connection.close()


class WebsocketAudioSourceMixin(AudioSource):
    def __init__(self, sampling_rate: int, **kwargs):
        self.sampling_rate = sampling_rate
        self.kwargs = kwargs
        self.audio_queue = asyncio.Queue()

    async def _handle(self, websocket: WebSocketProtocol):
        async for message in websocket:
            if not isinstance(message, bytes):
                logger.warn(f"Received non-bytes message: {message}")
                continue

            await self.audio_queue.put(np.frombuffer(message, dtype=np.float32))

    async def __aiter__(self) -> AsyncIterator[np.ndarray]:
        while self.is_active():
            yield await self.audio_queue.get()
            self.audio_queue.task_done()

    @abstractmethod
    def is_active(self) -> bool:
        raise NotImplementedError()


class WebsocketServerAudioSource(WebsocketServerAudioMixin, WebsocketAudioSourceMixin):
    def __init__(
        self, sampling_rate: int, host: str = "localhost", port: int = 8765, **kwargs
    ):
        super().__init__(sampling_rate, host, port, **kwargs)
        WebsocketAudioSourceMixin.__init__(self, sampling_rate, **kwargs)

    def _handle(self, websocket: WebSocketProtocol):
        return WebsocketAudioSourceMixin._handle(self, websocket)

    def is_active(self) -> bool:
        return self.server.is_serving()


class WebsocketServerAudioSink(WebsocketServerAudioMixin, AudioSink):
    def __init__(
        self, sampling_rate: int, host: str = "localhost", port: int = 8765, **kwargs
    ):
        super().__init__(sampling_rate, host, port, **kwargs)
        self.websockets: Set[WebSocketServerProtocol] = set()

    async def _handle(self, websocket: WebSocketServerProtocol):
        self.websockets.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.websockets.remove(websocket)

    async def write(self, audio: np.ndarray):
        await asyncio.gather(
            *[websocket.send(audio.tobytes()) for websocket in self.websockets]
        )


class WebsocketClientAudioSource(WebsocketClientAudioMixin, WebsocketAudioSourceMixin):
    def __init__(self, sampling_rate: int, url: str = "ws://localhost:8765", **kwargs):
        super().__init__(sampling_rate, url, **kwargs)
        WebsocketAudioSourceMixin.__init__(self, sampling_rate, **kwargs)

    def _handle(self, websocket: WebSocketProtocol):
        return WebsocketAudioSourceMixin._handle(self, websocket)

    def is_active(self) -> bool:
        return not self.connection.closed


class WebsocketClientAudioSink(WebsocketClientAudioMixin, AudioSink):
    def __init__(self, sampling_rate: int, url: str = "ws://localhost:8765", **kwargs):
        super().__init__(sampling_rate, url, **kwargs)

    async def write(self, audio: np.ndarray):
        await self.connection.send(audio.tobytes())
