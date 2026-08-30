#!/usr/bin/env python3
"""
dotify.py — turn a photo into a dot-matrix SVG portrait.

Usage:
    python dotify.py input.jpg -o assets/portrait --cols 100 --equalize --detail 0.5 --color
"""
import argparse
import math
from PIL import Image, ImageOps, ImageFilter


def build_parser():
    p = argparse.ArgumentParser(description="Photo -> dot-matrix SVG portrait")
    p.add_argument("input", help="path to source photo")
    p.add_argument("-o", "--out", default="assets/portrait", help="output path prefix (no extension)")
    p.add_argument("--cols", type=int, default=88, help="number of dot columns")
    p.add_argument("--equalize", action="store_true", help="stretch tones against the subject's histogram")
    p.add_argument("--detail", type=float, default=0.0, help="local-contrast boost, 0-1ish")
    p.add_argument("--color", action="store_true", help="keep original colour instead of green monochrome")
    p.add_argument("--circle", action="store_true", help="mask the result to a circle")
    p.add_argument("--invert", action="store_true", help="invert brightness->dot-size mapping")
    p.add_argument("--accent", default="#39D353", help="accent hex used for the monochrome version")
    return p


def load_and_prep(path, cols, detail):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    cell = w / cols
    rows = max(1, round(h / cell))
    small = img.resize((cols, rows), Image.LANCZOS)

    gray = ImageOps.grayscale(small)
    if detail > 0:
        sharp = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=int(150 * detail), threshold=2))
        gray = sharp
    return small, gray, cols, rows


def equalize(gray):
    return ImageOps.equalize(gray)


def make_svg(small, gray, cols, rows, out_path, color=False, circle=False, invert=False, accent="#39D353"):
    cell = 10
    pad = 1
    W = cols * cell
    H = rows * cell

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    parts.append(f'<rect width="{W}" height="{H}" fill="none"/>')

    if circle:
        cx, cy, r = W / 2, H / 2, min(W, H) / 2
        parts.append(f'<clipPath id="clip"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
        parts.append('<g clip-path="url(#clip)">')

    px_small = small.load()
    px_gray = gray.load()

    for y in range(rows):
        for x in range(cols):
            v = px_gray[x, y] / 255.0
            if invert:
                v = 1 - v
            radius = (1 - v) * (cell / 2 - pad) + 0.4
            cx_ = x * cell + cell / 2
            cy_ = y * cell + cell / 2
            if color:
                r, g, b = px_small[x, y]
                fill = f'rgb({r},{g},{b})'
            else:
                fill = accent
            parts.append(f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="{radius:.2f}" fill="{fill}"/>')

    if circle:
        parts.append('</g>')

    parts.append('</svg>')
    svg = "\n".join(parts)

    with open(f"{out_path}.svg", "w") as f:
        f.write(svg)
    print(f"wrote {out_path}.svg ({W}x{H}px canvas, {cols}x{rows} dots)")


def main():
    args = build_parser().parse_args()
    small, gray, cols, rows = load_and_prep(args.input, args.cols, args.detail)
    if args.equalize:
        gray = equalize(gray)
    make_svg(small, gray, cols, rows, args.out,
              color=args.color, circle=args.circle, invert=args.invert, accent=args.accent)


if __name__ == "__main__":
    main()
