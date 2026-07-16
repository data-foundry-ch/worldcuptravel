"""Generate classic soccer-ball favicon PNG + ICO."""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PNG = ROOT / "frontend" / "public" / "favicon-32.png"
OUT_ICO = ROOT / "frontend" / "public" / "favicon.ico"
SIZE = 64


def clamp(v: int) -> int:
    return max(0, min(255, v))


def set_pixel(buf: bytearray, x: int, y: int, r: int, g: int, b: int, a: int = 255) -> None:
    if 0 <= x < SIZE and 0 <= y < SIZE:
        i = (y * SIZE + x) * 4
        buf[i : i + 4] = bytes((r, g, b, a))


def blend(buf: bytearray, x: int, y: int, r: int, g: int, b: int, a: float) -> None:
    if not (0 <= x < SIZE and 0 <= y < SIZE) or a <= 0:
        return
    i = (y * SIZE + x) * 4
    oa = buf[i + 3] / 255.0
    na = a + oa * (1 - a)
    if na <= 0:
        return
    buf[i] = clamp(int((r * a + buf[i] * oa * (1 - a)) / na))
    buf[i + 1] = clamp(int((g * a + buf[i + 1] * oa * (1 - a)) / na))
    buf[i + 2] = clamp(int((b * a + buf[i + 2] * oa * (1 - a)) / na))
    buf[i + 3] = clamp(int(na * 255))


def fill_circle(buf: bytearray, cx: float, cy: float, radius: float, color: tuple[int, int, int]) -> None:
    r2 = radius * radius
    for y in range(SIZE):
        for x in range(SIZE):
            d2 = (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2
            if d2 <= (radius - 0.7) ** 2:
                set_pixel(buf, x, y, *color)
            elif d2 <= (radius + 0.7) ** 2:
                edge = 1 - (math.sqrt(d2) - (radius - 0.7)) / 1.4
                blend(buf, x, y, color[0], color[1], color[2], max(0.0, min(1.0, edge)))


def point_in_poly(x: float, y: float, poly: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(poly) - 1
    for i, (xi, yi) in enumerate(poly):
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def fill_poly(buf: bytearray, poly: list[tuple[float, float]], color: tuple[int, int, int], clip_r: float) -> None:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            px, py = x + 0.5, y + 0.5
            if (px - 32) ** 2 + (py - 32) ** 2 > clip_r * clip_r:
                continue
            if point_in_poly(px, py, poly):
                set_pixel(buf, x, y, *color)


def regular_poly(cx: float, cy: float, radius: float, n: int, rot: float) -> list[tuple[float, float]]:
    return [
        (cx + math.cos(rot + i * 2 * math.pi / n) * radius, cy + math.sin(rot + i * 2 * math.pi / n) * radius)
        for i in range(n)
    ]


def write_png(path: Path, rgba: bytes) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + rgba[y * SIZE * 4 : (y + 1) * SIZE * 4] for y in range(SIZE))
    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.write_bytes(data)


def write_ico(path: Path, png: bytes) -> None:
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", SIZE, SIZE, 0, 0, 1, 32, len(png), 22)
    path.write_bytes(header + entry + png)


def main() -> None:
    buf = bytearray(SIZE * SIZE * 4)
    cream = (245, 240, 230)
    black = (18, 18, 18)
    rim = (70, 48, 23)

    fill_circle(buf, 32, 32, 30, cream)

    # Center pentagon
    fill_poly(buf, regular_poly(32, 30, 9.8, 5, -math.pi / 2), black, 29)

    # Five surrounding black patches
    for i in range(5):
        angle = -math.pi / 2 + i * 2 * math.pi / 5
        px = 32 + math.cos(angle) * 21.0
        py = 30 + math.sin(angle) * 21.0
        fill_poly(buf, regular_poly(px, py, 6.4, 5, angle + math.pi), black, 29)

    # Rim ring
    for y in range(SIZE):
        for x in range(SIZE):
            d = math.hypot(x + 0.5 - 32, y + 0.5 - 32)
            if 28.2 <= d <= 30.6:
                a = 1.0 - abs(d - 29.4) / 1.2
                blend(buf, x, y, rim[0], rim[1], rim[2], max(0.0, min(1.0, a)))

    write_png(OUT_PNG, bytes(buf))
    write_ico(OUT_ICO, OUT_PNG.read_bytes())
    print(f"wrote {OUT_PNG} ({OUT_PNG.stat().st_size} bytes)")
    print(f"wrote {OUT_ICO} ({OUT_ICO.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
