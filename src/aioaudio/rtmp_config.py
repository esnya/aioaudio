from typing import Literal, Optional

from .base_config import AudioSinkBaseModel


class RTMPAudioSinkConfig(AudioSinkBaseModel):
    mode: Literal["rtmp"] = "rtmp"
    format: str = "f32le"
    channels: int = 1
    url: str = "rtmp://localhost:1234/live/test"
    keep_alive_interval: Optional[int] = None
