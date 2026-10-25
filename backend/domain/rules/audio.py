"""Audio telefónico: μ-law a 8 kHz (lo que usa la red telefónica) a PCM de 16 bits, y mezcla de pistas."""

import struct


def _mulaw_sample(byte):
    byte = ~byte & 0xFF
    sign = byte & 0x80
    exponent = (byte >> 4) & 0x07
    mantissa = byte & 0x0F
    magnitude = ((mantissa << 3) + 0x84) << exponent
    value = magnitude - 0x84
    return -value if sign else value


MULAW_TABLE = [_mulaw_sample(i) for i in range(256)]


def mulaw_to_pcm16(data):
    """Bytes μ-law -> PCM 16 bits little-endian."""
    return struct.pack(f"<{len(data)}h", *(MULAW_TABLE[b] for b in data))


def mix_frames(frames):
    """Suma varias pistas PCM16 del mismo instante, recortando para no saturar."""
    if not frames:
        return b""
    if len(frames) == 1:
        return frames[0]
    length = min(len(f) for f in frames) // 2
    tracks = [struct.unpack(f"<{length}h", f[: length * 2]) for f in frames]
    mixed = (max(-32768, min(32767, sum(samples))) for samples in zip(*tracks, strict=True))
    return struct.pack(f"<{length}h", *mixed)
