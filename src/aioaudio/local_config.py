from typing import Literal, Optional

from .base_config import AudioSinkBaseModel, AudioSourceBaseModel


class LocalAudioSourceConfig(AudioSourceBaseModel):
    mode: Literal["local"] = "local"
    seconds_per_buffer: float = 10
    input_device_index: Optional[int] = None


class LocalAudioSinkConfig(AudioSinkBaseModel):
    mode: Literal["local"] = "local"
    output_device_index: Optional[int] = None
