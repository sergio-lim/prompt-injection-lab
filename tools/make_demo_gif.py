#!/usr/bin/env python3
"""Render assets/demo.gif from a live lab run. Stdlib only — no Pillow."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "demo.gif"

# 5x7 glyphs, bit 4 is the left column. Space is implicit (missing key).
FONT_5X7: dict[str, tuple[int, int, int, int, int, int, int]] = {
    "!": (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100),
    "$": (0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100),
    "&": (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    "'": (0b00100, 0b00100, 0b01000, 0b00000, 0b00000, 0b00000, 0b00000),
    "(": (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ")": (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    "*": (0b00100, 0b10101, 0b01110, 0b00100, 0b01110, 0b10101, 0b00100),
    ",": (0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00100, 0b01000),
    "#": (0b01010, 0b11111, 0b01010, 0b01010, 0b11111, 0b01010, 0b00000),
    "%": (0b11001, 0b11010, 0b00100, 0b01011, 0b10011, 0b00000, 0b00000),
    "+": (0b00000, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00000),
    "-": (0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000),
    ".": (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100),
    "/": (0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b00000, 0b00000),
    "0": (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    "1": (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "2": (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111),
    "3": (0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110),
    "4": (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    "5": (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    "6": (0b01110, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b01110),
    "7": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    "8": (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    "9": (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001, 0b01110),
    ":": (0b00000, 0b00100, 0b00000, 0b00000, 0b00100, 0b00000, 0b00000),
    "=": (0b00000, 0b00000, 0b11111, 0b00000, 0b11111, 0b00000, 0b00000),
    "?": (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b00000, 0b00100),
    "@": (0b01110, 0b10001, 0b10111, 0b11011, 0b10110, 0b10000, 0b01110),
    "A": (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "B": (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    "C": (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    "D": (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    "E": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    "F": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    "G": (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110),
    "H": (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "I": (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "J": (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "K": (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    "L": (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    "M": (0b10001, 0b11011, 0b10101, 0b10001, 0b10001, 0b10001, 0b10001),
    "N": (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    "O": (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "P": (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    "Q": (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    "R": (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    "S": (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    "T": (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "U": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "V": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "W": (0b10001, 0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b01010),
    "X": (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    "Y": (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    "Z": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    "_": (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111),
    "a": (0b00000, 0b00000, 0b01110, 0b00001, 0b01111, 0b10001, 0b01111),
    "b": (0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b11110),
    "c": (0b00000, 0b00000, 0b01110, 0b10000, 0b10000, 0b10001, 0b01110),
    "d": (0b00001, 0b00001, 0b01111, 0b10001, 0b10001, 0b10001, 0b01111),
    "e": (0b00000, 0b00000, 0b01110, 0b10001, 0b11111, 0b10000, 0b01110),
    "f": (0b00110, 0b01000, 0b11100, 0b01000, 0b01000, 0b01000, 0b01000),
    "g": (0b00000, 0b00000, 0b01111, 0b10001, 0b01111, 0b00001, 0b01110),
    "h": (0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b10001),
    "i": (0b00100, 0b00000, 0b01100, 0b00100, 0b00100, 0b00100, 0b01110),
    "j": (0b00010, 0b00000, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "k": (0b10000, 0b10000, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010),
    "l": (0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "m": (0b00000, 0b00000, 0b11010, 0b10101, 0b10101, 0b10101, 0b10101),
    "n": (0b00000, 0b00000, 0b11110, 0b10001, 0b10001, 0b10001, 0b10001),
    "o": (0b00000, 0b00000, 0b01110, 0b10001, 0b10001, 0b10001, 0b01110),
    "p": (0b00000, 0b00000, 0b11110, 0b10001, 0b11110, 0b10000, 0b10000),
    "q": (0b00000, 0b00000, 0b01111, 0b10001, 0b01111, 0b00001, 0b00001),
    "r": (0b00000, 0b00000, 0b10110, 0b11001, 0b10000, 0b10000, 0b10000),
    "s": (0b00000, 0b00000, 0b01111, 0b10000, 0b01110, 0b00001, 0b11110),
    "t": (0b01000, 0b01000, 0b11100, 0b01000, 0b01000, 0b01001, 0b00110),
    "u": (0b00000, 0b00000, 0b10001, 0b10001, 0b10001, 0b10011, 0b01101),
    "v": (0b00000, 0b00000, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "w": (0b00000, 0b00000, 0b10001, 0b10001, 0b10101, 0b10101, 0b01010),
    "x": (0b00000, 0b00000, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001),
    "y": (0b00000, 0b00000, 0b10001, 0b10001, 0b01111, 0b00001, 0b01110),
    "z": (0b00000, 0b00000, 0b11111, 0b00010, 0b00100, 0b01000, 0b11111),
}

# Palette indices
BG, DIM, GREEN, WHITE, YELLOW, RED, CYAN, BAR = range(8)
PALETTE = [
    (13, 17, 23),
    (110, 118, 129),
    (63, 185, 80),
    (230, 237, 243),
    (210, 153, 34),
    (248, 81, 73),
    (88, 166, 255),
    (22, 27, 34),
]

SCALE = 2
CW = 6 * SCALE
CH = 9 * SCALE
MARGIN_X = 16
MARGIN_Y = 28
FRAME_CS = 45  # hundredths of a second


def _glyph(ch: str) -> tuple[int, ...]:
    if ch == " ":
        return (0, 0, 0, 0, 0, 0, 0)
    return FONT_5X7.get(ch, FONT_5X7.get("?", (0, 0, 0, 0, 0, 0, 0)))


def _line_color(line: str) -> int:
    stripped = line.strip()
    if line.startswith("$"):
        return GREEN
    if stripped.startswith("prompt-injection-lab"):
        return CYAN
    if "OK = " in line or stripped.startswith("Wrote"):
        return DIM
    if stripped.startswith("Attack") or stripped.startswith("success"):
        return WHITE
    if set(stripped) <= {"-", " "}:
        return DIM
    return WHITE


def capture_lab() -> list[str]:
    """Run the lab with color off and return stdout lines."""
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "run_lab.py"), "--no-color"],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line.rstrip("\n") for line in proc.stdout.splitlines()]
    return ["$ python3 run_lab.py", ""] + lines


def blit_char(
    pixels: list[int],
    x: int,
    y: int,
    ch: str,
    color: int,
    width: int,
    height: int,
) -> None:
    glyph = _glyph(ch)
    for row, bits in enumerate(glyph):
        for col in range(5):
            if bits & (1 << (4 - col)):
                px = x + col * SCALE
                py = y + row * SCALE
                for dy in range(SCALE):
                    for dx in range(SCALE):
                        xx, yy = px + dx, py + dy
                        if 0 <= xx < width and 0 <= yy < height:
                            pixels[yy * width + xx] = color


def render_frame(lines: list[str], width: int, height: int) -> list[int]:
    pixels = [BG] * (width * height)
    for x in range(width):
        for y in range(MARGIN_Y - 8):
            pixels[y * width + x] = BAR
    title = "prompt-injection-lab"
    tx = 10
    for ch in title:
        blit_char(pixels, tx, 6, ch, CYAN, width, height)
        tx += CW
    y = MARGIN_Y
    max_rows = (height - MARGIN_Y - 8) // CH
    visible = lines[:max_rows]
    for line in visible:
        default = _line_color(line)
        x = MARGIN_X
        i = 0
        while i < len(line) and x < width - CW:
            ch = line[i]
            start = i
            while start > 0 and line[start - 1] not in " \t":
                start -= 1
            end = i
            while end < len(line) and line[end] not in " \t":
                end += 1
            token = line[start:end]
            color = default
            if token == "OK":
                color = GREEN
            elif token == "FAIL":
                color = RED
            elif token.endswith("%") and token[:-1].isdigit():
                color = GREEN if token == "0%" else YELLOW
            blit_char(pixels, x, y, ch, color, width, height)
            x += CW
            i += 1
        y += CH
    return pixels


def lzw_encode(indices: list[int], min_code_size: int) -> bytes:
    """GIF LZW, LSB-first, with clear/EOI and 12-bit cap."""
    clear = 1 << min_code_size
    eoi = clear + 1
    code_size = min_code_size + 1
    next_code = eoi + 1
    table: dict[bytes, int] = {bytes([i]): i for i in range(clear)}

    bits = 0
    bit_count = 0
    packed = bytearray()

    def emit(code: int, size: int) -> None:
        nonlocal bits, bit_count
        bits |= code << bit_count
        bit_count += size
        while bit_count >= 8:
            packed.append(bits & 0xFF)
            bits >>= 8
            bit_count -= 8

    emit(clear, code_size)
    w = bytes([indices[0]])
    for index in indices[1:]:
        wk = w + bytes([index])
        if wk in table:
            w = wk
            continue
        emit(table[w], code_size)
        if next_code < 4096:
            table[wk] = next_code
            # Increase width when the code just assigned needs the extra bit.
            # (The other order is rejected by common GIF decoders.)
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
            next_code += 1
        else:
            emit(clear, code_size)
            table = {bytes([i]): i for i in range(clear)}
            next_code = eoi + 1
            code_size = min_code_size + 1
        w = bytes([index])
    emit(table[w], code_size)
    emit(eoi, code_size)
    if bit_count:
        packed.append(bits & 0xFF)
    return bytes(packed)


def subblocks(data: bytes) -> bytes:
    out = bytearray()
    for i in range(0, len(data), 255):
        chunk = data[i : i + 255]
        out.append(len(chunk))
        out.extend(chunk)
    out.append(0)
    return bytes(out)


def write_gif(path: Path, frames: list[list[int]], width: int, height: int) -> None:
    """GIF89a, 8-color global palette, infinite loop."""
    min_code_size = 3  # 8 colors → 2^3
    header = bytearray()
    header.extend(b"GIF89a")
    header.extend(width.to_bytes(2, "little"))
    header.extend(height.to_bytes(2, "little"))
    header.append(0x80 | (2 << 4) | 2)  # GCT, 8-bit color, 8 entries
    header.append(0)  # background
    header.append(0)  # aspect
    palette = bytearray()
    for rgb in PALETTE:
        palette.extend(rgb)
    while len(palette) < 8 * 3:
        palette.extend(b"\x00\x00\x00")
    header.extend(palette)
    # Netscape loop
    header.extend(b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00")

    body = bytearray()
    for frame in frames:
        delay = FRAME_CS if frame is not frames[-1] else FRAME_CS * 4
        body.extend(b"\x21\xf9\x04\x00")
        body.extend(delay.to_bytes(2, "little"))
        body.extend(b"\x00\x00")
        body.extend(b"\x2c")
        body.extend(b"\x00\x00\x00\x00")
        body.extend(width.to_bytes(2, "little"))
        body.extend(height.to_bytes(2, "little"))
        body.append(0)
        encoded = lzw_encode(frame, min_code_size)
        body.append(min_code_size)
        body.extend(subblocks(encoded))
    body.append(0x3B)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(header) + bytes(body))


def canvas_size(lines: list[str]) -> tuple[int, int]:
    cols = max((len(line) for line in lines), default=1)
    rows = max(len(lines), 1)
    width = MARGIN_X + cols * CW + MARGIN_X
    height = MARGIN_Y + rows * CH + 16
    # GIF widths should be even for some viewers.
    if width % 2:
        width += 1
    if height % 2:
        height += 1
    return width, height


def main() -> int:
    lines = capture_lab()
    width, height = canvas_size(lines)
    frames: list[list[int]] = []
    # Reveal a couple of lines at a time so the table appears to type out.
    step = 2
    for end in range(1, len(lines) + 1, step):
        frames.append(render_frame(lines[:end], width, height))
    full = render_frame(lines, width, height)
    if not frames or frames[-1] != full:
        frames.append(full)
    write_gif(OUTPUT, frames, width, height)
    size = OUTPUT.stat().st_size
    print(f"wrote {OUTPUT} ({width}x{height}, {size} bytes, {len(frames)} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
