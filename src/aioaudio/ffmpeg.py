import asyncio
from asyncio import subprocess
import numpy as np


async def ffmpeg(*args: str, **kwargs):
    return await asyncio.create_subprocess_exec("ffmpeg", *args, **kwargs)


async def ffmpeg_source(
    *args: str,
):
    ffmpeg = await asyncio.create_subprocess_exec(
        "ffmpeg",
        *args,
        stdout=subprocess.PIPE,
    )
    pipe = ffmpeg.stdout
    assert pipe is not None

    return ffmpeg, pipe


async def ffmpeg_sink(*args: str):
    ffmpeg = await asyncio.create_subprocess_exec(
        "ffmpeg",
        *args,
        stdin=subprocess.PIPE,
    )
    pipe = ffmpeg.stdin
    assert pipe is not None

    return ffmpeg, pipe


F2N = {
    "s16le": np.int16,
    "f32le": np.float32,
}
N2F = {v: k for k, v in F2N.items()}
