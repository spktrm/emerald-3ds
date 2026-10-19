#!/usr/bin/env python3
"""Turn the top screen frames a FRAME_DUMP build wrote into PNG pictures.

    python tools/frames_to_png.py frames.raw out/

frames.raw (3ds_port/src/3ds_video.c, CtrVideo_Present) is a run of records:
the frame number (u32, little endian), then the left eye and the right eye,
each the top screen's render target - 240 wide and 400 tall as the LCD runs,
RGBA8 stored A, B, G, R, in the PICA's 8x8 Morton tiles. The right eye is all
zeros without the 3D slider; it is written only when it is not. Each record
becomes <frame>_L.png (and <frame>_R.png), 400x240 as the screen shows it.
"""
import os
import sys

from PIL import Image

W, H = 240, 400
EYE = W * H * 4


def texel(x, y, w=W):
    """3ds_video_decode.c, CtrVideo_Texel: a pixel's index in the tiled buffer."""
    m = (x & 1) | ((y & 1) << 1) | ((x & 2) << 1) | ((y & 2) << 2) | ((x & 4) << 2) | ((y & 4) << 3)
    return ((y >> 3) * (w >> 3) + (x >> 3)) * 64 + m


ORDER = [texel(x, y) * 4 for y in range(H) for x in range(W)]


def eye(data):
    linear = bytearray(EYE)
    for i, t in enumerate(ORDER):
        linear[i * 4:i * 4 + 4] = data[t:t + 4]
    picture = Image.frombytes("RGBA", (W, H), bytes(linear), "raw", "ABGR").convert("RGB")
    return picture.transpose(Image.Transpose.ROTATE_90)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    raw, out = sys.argv[1], sys.argv[2]
    data = open(raw, "rb").read()
    record = 4 + 2 * EYE
    os.makedirs(out, exist_ok=True)
    count = len(data) // record
    for k in range(count):
        r = data[k * record:(k + 1) * record]
        frame = int.from_bytes(r[:4], "little")
        eye(r[4:4 + EYE]).save(os.path.join(out, "%06d_L.png" % frame))
        if any(r[4 + EYE:4 + 2 * EYE]):
            eye(r[4 + EYE:]).save(os.path.join(out, "%06d_R.png" % frame))
    print("%d frames from %s to %s" % (count, raw, out))


if __name__ == "__main__":
    main()
