#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.

import time
import math
from rpi_ws281x import *
import argparse
import requests
import json
import os
import random
import threading

API_KEY = os.getenv("YAKKO_API_KEY", "")
SERVER_URL = os.getenv("YAKKO_URL", "http://yakko.cs.wmich.edu:8878")


# LED strip configuration:
LED_COUNT      = 300      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

# request thread
STATUS = {}

def interrupted():
    """Check if the animation type has changed, allowing faster mode switching."""
    return STATUS.get('_last_type') != STATUS.get('type')

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=25):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        if interrupted():
            return
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChase(strip, color, wait_ms=100, iterations=50):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        if interrupted():
            return
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        if interrupted():
            return
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        if interrupted():
            return
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        if interrupted():
            return
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

# --- New animation modes ---

def solid(strip, color):
    """Set all pixels instantly to the color."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()
    # Hold until mode changes
    while not interrupted():
        time.sleep(0.5)

def breathe(strip, color, cycles=10):
    """Smooth fade in/out of the current color (breathing/pulse effect)."""
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    for _ in range(cycles):
        # Fade in and out using a sine curve
        for step in range(200):
            if interrupted():
                return
            brightness = (math.sin(step * math.pi / 100) ** 2)
            cr = int(r * brightness)
            cg = int(g * brightness)
            cb = int(b * brightness)
            c = Color(cr, cg, cb)
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, c)
            strip.show()
            time.sleep(0.015)

def strobe(strip, color, flashes=50, on_ms=50, off_ms=50):
    """Fast on/off flashing."""
    off = Color(0, 0, 0)
    for _ in range(flashes):
        if interrupted():
            return
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, color)
        strip.show()
        time.sleep(on_ms / 1000.0)
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, off)
        strip.show()
        time.sleep(off_ms / 1000.0)

def fire(strip, cooling=55, sparking=120, iterations=500):
    """Flickering fire simulation (red/orange/yellow)."""
    num = strip.numPixels()
    heat = [0] * num
    for _ in range(iterations):
        if interrupted():
            return
        # Cool down every cell
        for i in range(num):
            heat[i] = max(0, heat[i] - random.randint(0, ((cooling * 10) // num) + 2))
        # Heat diffuses upward
        for i in range(num - 1, 1, -1):
            heat[i] = (heat[i - 1] + heat[i - 2] + heat[i - 2]) // 3
        # Randomly ignite sparks near bottom
        if random.randint(0, 255) < sparking:
            y = random.randint(0, min(7, num - 1))
            heat[y] = min(255, heat[y] + random.randint(160, 255))
        # Map heat to color
        for i in range(num):
            t = heat[i]
            if t > 170:
                # hot: white-yellow
                strip.setPixelColor(i, Color(255, 255, min(255, (t - 170) * 3)))
            elif t > 85:
                # medium: orange
                strip.setPixelColor(i, Color(255, min(255, (t - 85) * 3), 0))
            else:
                # cool: red
                strip.setPixelColor(i, Color(min(255, t * 3), 0, 0))
        strip.show()
        time.sleep(0.02)

def meteor(strip, color, meteor_size=10, decay=64, iterations=3):
    """Shooting light with fading tail."""
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    num = strip.numPixels()
    for _ in range(iterations):
        if interrupted():
            return
        # Clear strip
        for i in range(num):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        for j in range(num + meteor_size):
            if interrupted():
                return
            # Fade all pixels
            for i in range(num):
                cr = (strip.getPixelColor(i) >> 16) & 0xFF
                cg = (strip.getPixelColor(i) >> 8) & 0xFF
                cb = strip.getPixelColor(i) & 0xFF
                cr = max(0, cr - decay) if random.randint(0, 10) > 3 else cr
                cg = max(0, cg - decay) if random.randint(0, 10) > 3 else cg
                cb = max(0, cb - decay) if random.randint(0, 10) > 3 else cb
                strip.setPixelColor(i, Color(cr, cg, cb))
            # Draw meteor
            for k in range(meteor_size):
                if 0 <= j - k < num:
                    strip.setPixelColor(j - k, Color(r, g, b))
            strip.show()
            time.sleep(0.01)

def scanner(strip, color, iterations=5):
    """Knight Rider bouncing light (Larson scanner)."""
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    num = strip.numPixels()
    eye_size = max(1, num // 30)
    for _ in range(iterations):
        if interrupted():
            return
        # Forward
        for j in range(num - eye_size - 1):
            if interrupted():
                return
            for i in range(num):
                strip.setPixelColor(i, Color(0, 0, 0))
            # Dim leading pixel
            strip.setPixelColor(j, Color(r // 10, g // 10, b // 10))
            # Eye
            for i in range(eye_size):
                strip.setPixelColor(j + 1 + i, Color(r, g, b))
            # Dim trailing pixel
            strip.setPixelColor(j + eye_size + 1, Color(r // 10, g // 10, b // 10))
            strip.show()
            time.sleep(0.005)
        # Backward
        for j in range(num - eye_size - 1, 0, -1):
            if interrupted():
                return
            for i in range(num):
                strip.setPixelColor(i, Color(0, 0, 0))
            strip.setPixelColor(j, Color(r // 10, g // 10, b // 10))
            for i in range(eye_size):
                strip.setPixelColor(j + 1 + i, Color(r, g, b))
            strip.setPixelColor(j + eye_size + 1, Color(r // 10, g // 10, b // 10))
            strip.show()
            time.sleep(0.005)

def sparkle(strip, color, iterations=300):
    """Random twinkling pixels over base color."""
    num = strip.numPixels()
    # Set base color
    for i in range(num):
        strip.setPixelColor(i, color)
    strip.show()
    for _ in range(iterations):
        if interrupted():
            return
        # Light a random pixel white
        pixel = random.randint(0, num - 1)
        strip.setPixelColor(pixel, Color(255, 255, 255))
        strip.show()
        time.sleep(0.05)
        # Restore base color
        strip.setPixelColor(pixel, color)
        strip.show()
        time.sleep(0.05)

def police(strip, flashes=50):
    """Red/blue alternating flash."""
    num = strip.numPixels()
    half = num // 2
    red = Color(255, 0, 0)
    blue = Color(0, 0, 255)
    off = Color(0, 0, 0)
    for _ in range(flashes):
        if interrupted():
            return
        # Red left, blue right
        for i in range(half):
            strip.setPixelColor(i, red)
        for i in range(half, num):
            strip.setPixelColor(i, blue)
        strip.show()
        time.sleep(0.1)
        # Off
        for i in range(num):
            strip.setPixelColor(i, off)
        strip.show()
        time.sleep(0.05)
        # Blue left, red right
        for i in range(half):
            strip.setPixelColor(i, blue)
        for i in range(half, num):
            strip.setPixelColor(i, red)
        strip.show()
        time.sleep(0.1)
        for i in range(num):
            strip.setPixelColor(i, off)
        strip.show()
        time.sleep(0.05)

def gradient(strip, color):
    """Smooth gradient from the set color to its complement."""
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    # Complement color
    cr, cg, cb = 255 - r, 255 - g, 255 - b
    num = strip.numPixels()
    for i in range(num):
        ratio = i / max(1, num - 1)
        pr = int(r + (cr - r) * ratio)
        pg = int(g + (cg - g) * ratio)
        pb = int(b + (cb - b) * ratio)
        strip.setPixelColor(i, Color(pr, pg, pb))
    strip.show()
    # Hold until mode changes
    while not interrupted():
        time.sleep(0.5)

def wave(strip, color, iterations=100):
    """Sinusoidal brightness wave moving along the strip."""
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    num = strip.numPixels()
    for offset in range(iterations * num):
        if interrupted():
            return
        for i in range(num):
            brightness = (math.sin((i + offset) * 2 * math.pi / 60) + 1) / 2
            strip.setPixelColor(i, Color(
                int(r * brightness),
                int(g * brightness),
                int(b * brightness)
            ))
        strip.show()
        time.sleep(0.02)

def candy(strip, color, segment_len=15, iterations=300):
    """Alternating colored segments that scroll."""
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    num = strip.numPixels()
    for offset in range(iterations):
        if interrupted():
            return
        for i in range(num):
            pos = (i + offset) % (segment_len * 2)
            if pos < segment_len:
                strip.setPixelColor(i, Color(r, g, b))
            else:
                strip.setPixelColor(i, Color(255, 255, 255))
        strip.show()
        time.sleep(0.05)

def off(strip):
    """Turn all LEDs off."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    # Hold until mode changes
    while not interrupted():
        time.sleep(0.5)


def get_status():
   global STATUS
   while 1:
        try:
            r = requests.get(SERVER_URL, headers={"Authorization": "Bearer " + API_KEY})
        except:
            print("Failed connection.")
            time.sleep(2)
            continue
        print("GET: " + str(r.text))
        STATUS = json.loads(r.text)
        time.sleep(5)

# Main program logic follows:
if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    print ('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    # start requests thread
    t = threading.Thread(target=get_status)
    t.daemon = True
    t.start()

    # wait for first request
    time.sleep(3)

    try:
        while True:
            status = STATUS
            print (status)

            # Track which type we're running so interrupted() works
            STATUS['_last_type'] = status.get('type', 'color')

            color = Color(random.randint(16, 128), random.randint(16, 128), random.randint(16, 128))
            if status.get('type') != "random":
                color = Color(int(status.get('red', 0)), int(status.get('green', 0)), int(status.get('blue', 0)))

            rand = random.randint(1, 3)
            mode = status.get('type', 'color')

            if mode == "off":
                off(strip)
            elif mode == "solid":
                solid(strip, color)
            elif mode == "breathe":
                breathe(strip, color)
            elif mode == "strobe":
                strobe(strip, color)
            elif mode == "fire":
                fire(strip)
            elif mode == "meteor":
                meteor(strip, color)
            elif mode == "scanner":
                scanner(strip, color)
            elif mode == "sparkle":
                sparkle(strip, color)
            elif mode == "police":
                police(strip)
            elif mode == "gradient":
                gradient(strip, color)
            elif mode == "wave":
                wave(strip, color)
            elif mode == "candy":
                candy(strip, color)
            elif mode == "rainbow" or (mode == "random" and rand == 1):
                rainbowCycle(strip)
            elif mode == "chase" or (mode == "random" and rand == 2):
                theaterChase(strip, color)
                colorWipe(strip, color, 1)
                colorWipe(strip, Color(0,0,0), 1)
            else:
                colorWipe(strip, color)
                colorWipe(strip, Color(0,0,0), 5)


    except KeyboardInterrupt:
        if args.clear:
            colorWipe(strip, Color(0,0,0), 10)
