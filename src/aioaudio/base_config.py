from pydantic import BaseModel


class AudioSourceBaseModel(BaseModel):
    mode: str


class AudioSinkBaseModel(BaseModel):
    mode: str
