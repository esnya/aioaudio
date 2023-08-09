from typing import Literal, Optional, Union
from typing_extensions import Annotated
from pydantic import BaseModel, Field

from . import AudioSource, AudioSink


class AudioSourceBaseModel(BaseModel):
    mode: str


class AudioSinkBaseModel(BaseModel):
    mode: str


class LocalAudioSourceConfig(AudioSourceBaseModel):
    mode: Literal["local"] = "local"
    seconds_per_buffer: float = 10
    input_device_index: Optional[int] = None


class LocalAudioSinkConfig(AudioSinkBaseModel):
    mode: Literal["local"] = "local"
    output_device_index: Optional[int] = None


class WebsocketServerAudioConfig(AudioSourceBaseModel, AudioSinkBaseModel):
    mode: Literal["websocket-server"] = "websocket-server"
    host: str = "localhost"
    port: int = 8765


class WebsocketClientAuduioConfig(AudioSourceBaseModel, AudioSinkBaseModel):
    mode: Literal["websocket-client"] = "websocket-client"
    url: str = "ws://localhost:8765"


class RTPAudioSourceConfig(AudioSourceBaseModel):
    mode: Literal["rtp"] = "rtp"
    seconds_per_buffer: float = 10
    url: str = "rtp://localhost:1234"


class RTPAudioSinkConfig(AudioSinkBaseModel):
    mode: Literal["rtp"] = "rtp"
    url: str = "rtp://localhost:1234"


class RTMPAudioSinkConfig(AudioSinkBaseModel):
    mode: Literal["rtmp"] = "rtmp"
    format: str = "f32le"
    channels: int = 1
    url: str = "rtmp://localhost:1234/live/test"


AudioSourceConfig = Annotated[
    Union[
        LocalAudioSourceConfig,
        WebsocketServerAudioConfig,
        WebsocketClientAuduioConfig,
        RTPAudioSourceConfig,
    ],
    Field(discriminator="mode"),
]

AudioSinkConfig = Annotated[
    Union[
        LocalAudioSinkConfig,
        WebsocketServerAudioConfig,
        WebsocketClientAuduioConfig,
        RTPAudioSinkConfig,
        RTMPAudioSinkConfig,
    ],
    Field(discriminator="mode"),
]


def audio_source(config: AudioSourceConfig, sampling_rate: int) -> AudioSource:
    match config:
        case LocalAudioSourceConfig(
            seconds_per_buffer=seconds_per_buffer,
            input_device_index=input_device_index,
        ):
            from .local import LocalAudioSource

            return LocalAudioSource(
                sampling_rate,
                int(seconds_per_buffer * sampling_rate),
                input_device_index=input_device_index,
            )
        case WebsocketServerAudioConfig(
            host=host,
            port=port,
        ):
            from .websocket import WebsocketServerAudioSource

            return WebsocketServerAudioSource(
                sampling_rate,
                host=host,
                port=port,
            )
        case WebsocketClientAuduioConfig(
            url=url,
        ):
            from .websocket import WebsocketServerAudioSource

            return WebsocketServerAudioSource(
                sampling_rate,
                url=url,
            )
        case RTPAudioSourceConfig(
            seconds_per_buffer=seconds_per_buffer,
            url=url,
        ):
            from .rtp import RTPAudioSource

            return RTPAudioSource(
                int(seconds_per_buffer * sampling_rate * 4),
                sampling_rate,
                url=url,
            )
        case _:
            raise NotImplementedError("Unknown audio source for config %s", config)


def audio_sink(config: AudioSinkBaseModel, sampling_rate: int) -> AudioSink:
    match config:
        case LocalAudioSinkConfig(
            output_device_index=output_device_index,
        ):
            from .local import LocalAudioSink

            return LocalAudioSink(
                sampling_rate,
                output_device_index=output_device_index,
            )
        case WebsocketServerAudioConfig(
            host=host,
            port=port,
        ):
            from .websocket import WebsocketServerAudioSink

            return WebsocketServerAudioSink(
                sampling_rate,
                host=host,
                port=port,
            )
        case WebsocketClientAuduioConfig(
            url=url,
        ):
            from .websocket import WebsocketClientAudioSink

            return WebsocketClientAudioSink(
                sampling_rate,
                url=url,
            )
        case RTPAudioSinkConfig(
            format=format,
            channels=channels,
            url=url,
        ):
            from .rtp import RTPAudioSink

            return RTPAudioSink(
                sampling_rate,
                url=url,
            )
        case RTMPAudioSinkConfig(
            format=format,
            channels=channels,
            url=url,
        ):
            from .rtmp import RTMPAudioSink

            return RTMPAudioSink(
                sampling_rate=sampling_rate,
                format=format,
                channels=channels,
                url=url,
            )
        case _:
            raise NotImplementedError("Unknown audio sink for config %s", config)
