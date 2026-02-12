# LEDBox

LEDBox is the NeoPixel LED lighting system for the CCaWMU office. It drives a 300-pixel LED strip that can be controlled remotely through Matrix chat commands.

---

## How It Works

```
┌──────────────┐   $led red    ┌──────────────────┐   poll 5s   ┌─────────────┐       ┌──────────────┐
│  Matrix Chat │ ────────────▶ │  Server (yakko)  │ ◀───────── │  LEDBox Pi  │ ────▶ │  300 NeoPixel │
│  $led / $rgb │               │  :8878           │ ─────────▶ │  (LEDbox)   │       │  LED Strip   │
└──────────────┘               └──────────────────┘             └─────────────┘       └──────────────┘
```

1. A user sends a command in Matrix chat (e.g. `$led red`, `$led rainbow`, `$led chase`)
2. The chatbot POSTs the color/mode to the server at `yakko.cs.wmich.edu:8878`
3. The LEDBox Pi polls the server every 5 seconds for the current state
4. The Pi drives the NeoPixel strip with the requested color or animation

---

## Chat Commands

Control the LEDs from Matrix chat using the `$led` command:

```
$led #ff0000              Set color to red (default mode: color)
$led #00ff22 chase        Set color to green with chase animation
$led #0000ff rainbow      Rainbow cycle (color value ignored for rainbow)
$led #ffffff random       Random mode — picks random animations and colors
```

The hex color values are halved by the chatbot before being sent to the server to keep brightness at a reasonable level.

## Animation Modes

| Mode | Behavior |
|---|---|
| **color** | Wipes the solid color across the strip, then fades to black |
| **chase** | Theater-style chasing lights in the current color |
| **rainbow** | Full rainbow cycle across all 300 pixels |
| **random** | Randomly picks between rainbow, chase, and color with random colors |

---

## Hardware

| Component | Details |
|---|---|
| **Computer** | Raspberry Pi 3 Model B+ |
| **Hostname** | `LEDbox` |
| **IP Address** | `192.168.1.194` |
| **LED Strip** | 300x WS2812B (NeoPixel) — GRB color order |
| **Data Pin** | GPIO 18 (PWM) |
| **Brightness** | 255 (max) |

### LED Strip Parameters

| Parameter | Value |
|---|---|
| Pixel Count | 300 |
| Signal Frequency | 800 kHz |
| DMA Channel | 10 |
| PWM Channel | 0 |
| Color Order | GRB |

---

## Software

All source code lives in one repo: **https://github.com/ccowmu/LEDBox**

The Pi automatically mirrors this repo. Push to `main` and the changes go live within 60 seconds — no SSH required.

### Repository Contents

```
LEDBox/
├── updatecolors.py        # Main controller — polls server, drives NeoPixels
├── ledbox.service          # Systemd unit for the controller
├── ledbox-sync.sh          # Auto-sync script (fetch + reset + restart)
├── ledbox-sync.service     # Systemd unit for sync
├── ledbox-sync.timer       # Runs sync every 60 seconds
├── .env                    # API key (gitignored)
└── .gitignore
```

### Systemd Services

| Service | What It Does |
|---|---|
| `ledbox.service` | Runs the controller as root (required for GPIO/PWM). Starts on boot, restarts on failure. |
| `ledbox-sync.timer` | Every 60s: pulls from GitHub, restarts controller if code changed. |

### Auto-Sync (GitHub → Pi)

The `ledbox-sync.sh` script runs every minute via systemd timer:

1. `git fetch origin main`
2. Compares local HEAD to remote — if identical, does nothing
3. If there are changes: `git reset --hard origin/main`
4. Checks if any `.service` or `.timer` files changed — if so, copies them to `/etc/systemd/system/` and reloads systemd
5. Restarts `ledbox.service`

**To deploy a change:** just push to `main` on GitHub. Done.

---

## Server API

The LEDBox Pi polls the same Office-IoT server as doorbot (`yakko.cs.wmich.edu:8878`).

### GET / (status polling)

Returns the current LED state:

```json
{
  "red": 255,
  "green": 0,
  "blue": 0,
  "type": "color",
  "letmein": false,
  "timestamp": 1707700000
}
```

The `type` field determines the animation mode: `color`, `chase`, `rainbow`, or `random`.

### POST / (control — from chatbot)

```json
{
  "status": {
    "red": 255,
    "green": 0,
    "blue": 0,
    "type": "rainbow"
  }
}
```

---

## Common Commands

```bash
# SSH into the Pi
ssh pi@192.168.1.194

# Check if the controller is running
sudo systemctl status ledbox

# View live logs
sudo journalctl -u ledbox -f

# Restart the controller
sudo systemctl restart ledbox

# Force an immediate sync from GitHub
/home/pi/LEDBox/ledbox-sync.sh

# Check sync timer status
systemctl status ledbox-sync.timer

# Test server connection
curl -H "Authorization: Bearer $YAKKO_API_KEY" http://yakko.cs.wmich.edu:8878/
```

---

## Architecture Notes

- The controller runs as **root** because the `rpi_ws281x` library requires root access for PWM/DMA hardware control
- The background thread polls the server every **5 seconds** for state changes
- Animations are blocking — the current animation runs to completion before checking for new state, so there can be a delay between sending a command and seeing the change
- The API key is stored in `/home/pi/LEDBox/.env` (not in the repo)

---

## Troubleshooting

**LEDs not responding:**
```bash
sudo systemctl status ledbox           # Is the service running?
sudo journalctl -u ledbox -n 50        # Check recent logs
```

**Wrong colors / flickering:**
- The strip uses **GRB** color order — if colors look swapped, check the `ORDER` constant
- Ensure the Pi has adequate power — a 300-pixel strip at full brightness draws significant current
- Check GPIO 18 connection to the data line

**Service won't start:**
- Must run as root (the `rpi_ws281x` library needs DMA access)
- Check that `python3`, `rpi_ws281x`, and `requests` are installed

**Sync not working:**
```bash
systemctl status ledbox-sync.timer     # Is the timer active?
sudo journalctl -u ledbox-sync -n 20   # Check sync logs
git -C /home/pi/LEDBox fetch origin    # Can it reach GitHub?
```

---

## Network

| Endpoint | Address |
|---|---|
| **Server API** | http://yakko.cs.wmich.edu:8878 |
| **Pi SSH** | `pi@192.168.1.194` |
| **Source Code** | https://github.com/ccowmu/LEDBox |

---

## See Also

- [Door Bot](https://github.com/ccowmu/doorbot) — the office door lock system, controlled by the same server
- [Office-IoT](https://github.com/ccowmu/Office-IoT) — the server that both LEDBox and doorbot poll
