from typing import Optional, Union

from pydantic import Field
from typing_extensions import Annotated, deprecated

from .base import AudioSink, AudioSource
from .local_config import LocalAudioSinkConfig, LocalAudioSourceConfig
from .rtmp_config import RTMPAudioSinkConfig
from .rtp_config import RTPAudioSinkConfig, RTPAudioSourceConfig
from .void import VoidAudioSink, VoidAudioSource
from .websocket_config import WebsocketClientAuduioConfig, WebsocketServerAudioConfig

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


@deprecated("Use load_audio_source instead of audio_source. This will be removed soon.")
def audio_source(config: AudioSourceConfig, sampling_rate: int) -> AudioSource:
    return load_audio_source(config, sampling_rate)


def load_audio_source(
    config: Optional[AudioSourceConfig], sampling_rate: int
) -> AudioSource:
    match config:
        case None:
            return VoidAudioSource()
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
        case _:
            raise NotImplementedError("Unknown audio source for config %s", config)


@deprecated("Use load_audio_sink instead of audio_sink. This will be removed soon.")
def audio_sink(config: AudioSinkConfig, sampling_rate: int) -> AudioSink:
    return load_audio_sink(config, sampling_rate)


def load_audio_sink(config: Optional[AudioSinkConfig], sampling_rate: int) -> AudioSink:
    match config:
        case None:
            return VoidAudioSink()
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
            keep_alive_interval=keep_alive_interval,
        ):
            from .rtmp import RTMPAudioSink

            return RTMPAudioSink(
                sampling_rate=sampling_rate,
                format=format,
                channels=channels,
                url=url,
                keep_alive_interval=keep_alive_interval,
            )
        case _:
            raise NotImplementedError("Unknown audio sink for config %s", config)
