from typing import Literal

from .base_config import AudioSinkBaseModel, AudioSourceBaseModel


class WebsocketServerAudioConfig(AudioSourceBaseModel, AudioSinkBaseModel):
    mode: Literal["websocket-server"] = "websocket-server"
    host: str = "localhost"
    port: int = 8765


class WebsocketClientAuduioConfig(AudioSourceBaseModel, AudioSinkBaseModel):
    mode: Literal["websocket-client"] = "websocket-client"
    url: str = "ws://localhost:8765"
