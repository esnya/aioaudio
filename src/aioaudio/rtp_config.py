from typing import Literal

from .base_config import AudioSinkBaseModel, AudioSourceBaseModel


class RTPAudioSourceConfig(AudioSourceBaseModel):
    mode: Literal["rtp"] = "rtp"
    seconds_per_buffer: float = 10
    url: str = "rtp://localhost:1234"


class RTPAudioSinkConfig(AudioSinkBaseModel):
    mode: Literal["rtp"] = "rtp"
    url: str = "rtp://localhost:1234"
