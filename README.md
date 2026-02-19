# LEDBox

NeoPixel LED lighting system for the CCaWMU office. Controls a 300-pixel LED strip via Matrix chat commands.

## Architecture

```
┌──────────────┐   $led red    ┌──────────────────┐   poll 1s   ┌─────────────┐       ┌──────────────┐
│  Matrix Chat │ ────────────▶ │  Server (yakko)  │ ◀───────── │  LEDBox Pi  │ ────▶ │  300 NeoPixel │
│  $led #color │               │  :8878           │ ─────────▶ │  (pi@ledbox)│       │  LED Strip   │
└──────────────┘               └──────────────────┘             └─────────────┘       └──────────────┘
```

1. User sends `$led` command in Matrix chat
2. Chatbot POSTs color/mode to `yakko.cs.wmich.edu:8878`
3. LEDBox Pi polls server every 1 second
4. Pi drives NeoPixel strip with requested animation

## Chat Commands

Control the LEDs from Matrix using `$led`:

```
$led #ff0000                  — Set color to red (default mode: color)
$led #00ff22 chase            — Green with chase animation
$led rainbow                  — Rainbow cycle
$led #0000ff breathe          — Blue breathing effect
$led fire                     — Fire animation (color ignored)
$led off                      — Turn off LEDs
```

## Animation Modes

- **color** - Wipe color across strip
- **chase** - Chase animation
- **rainbow** - Rainbow cycle
- **solid** - Static color
- **breathe** - Breathing effect
- **strobe** - Strobe effect
- **fire** - Fire simulation (colorless)
- **meteor** - Meteor shower
- **scanner** - KITT scanner effect
- **sparkle** - Random sparkles
- **police** - Police lights (colorless)
- **gradient** - Color gradient
- **wave** - Wave effect
- **candy** - Candy cane pattern
- **off** - LEDs off

## Files

- **`updatecolors.py`** - Main client script (polls server, drives LEDs)
- **`ledbox.service`** - Systemd service for auto-start on boot
- **`ledbox-sync.sh`** - Git pull script for auto-updates
- **`ledbox-sync.service`** / **`.timer`** - Systemd timer for daily updates

## Installation

On the Raspberry Pi:

```bash
git clone https://github.com/ccowmu/LEDBox.git /home/pi/LEDBox
cd /home/pi/LEDBox
sudo cp ledbox.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ledbox
sudo systemctl start ledbox
```

Enable auto-updates:

```bash
sudo cp ledbox-sync.service ledbox-sync.timer /etc/systemd/system/
sudo systemctl enable ledbox-sync.timer
sudo systemctl start ledbox-sync.timer
```

## Hardware

- Raspberry Pi (any model with GPIO)
- 300-pixel WS2812B/NeoPixel LED strip
- 5V power supply (adequate for strip current)
- Level shifter (3.3V GPIO → 5V data line)

## Dependencies

```bash
sudo pip3 install rpi_ws281x requests
```

## Server

The server runs on `yakko.cs.wmich.edu:8878` and is part of the [Office-IoT](https://github.com/ccowmu/Office-IoT) project.

## License

GPL-3.0
