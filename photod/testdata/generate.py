#!/usr/bin/env python3
"""Generates synthetic scoring fixtures next to this file:
a red-frog scene, a blue-frog scene, an empty tank, and a blurred frog.
Run: python generate.py (needs pillow + numpy, e.g. inside the photod image)."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent
rng = np.random.default_rng(42)


def tank_background():
    # greenish-brown noise, roughly like moss/soil/glass
    base = rng.normal(0, 12, (720, 1280, 3))
    base += np.array([70, 95, 60])
    return Image.fromarray(base.clip(0, 255).astype("uint8"))


def add_frog(img, color):
    d = ImageDraw.Draw(img)
    d.ellipse([540, 350, 760, 500], fill=color)       # body
    d.ellipse([700, 310, 800, 400], fill=color)       # head
    return img


red = add_frog(tank_background(), (215, 40, 35))
red.save(HERE / "pos_red_frog.jpg", quality=90)

blue = add_frog(tank_background(), (40, 90, 220))
blue.save(HERE / "pos_blue_frog.jpg", quality=90)

tank_background().save(HERE / "neg_empty_tank.jpg", quality=90)

red.filter(ImageFilter.GaussianBlur(8)).save(HERE / "neg_blurry_frog.jpg", quality=90)

print("testdata generated")
