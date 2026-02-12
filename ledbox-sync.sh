#!/bin/bash
# Auto-sync LEDBox repo from GitHub and restart service if changed
REPO_DIR="/home/pi/LEDBox"
BRANCH="main"
SERVICE="ledbox.service"
SYSTEMD_DIR="/etc/systemd/system"

cd "$REPO_DIR" || exit 1

# Fetch latest
git fetch origin "$BRANCH" 2>/dev/null || exit 1

# Check if there are new changes
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] Updating from $LOCAL to $REMOTE"
    git reset --hard "origin/$BRANCH"

    # Install systemd units if they changed
    RELOAD_NEEDED=false
    for unit in ledbox.service ledbox-sync.service ledbox-sync.timer; do
        if [ -f "$REPO_DIR/$unit" ]; then
            if ! diff -q "$REPO_DIR/$unit" "$SYSTEMD_DIR/$unit" >/dev/null 2>&1; then
                sudo cp "$REPO_DIR/$unit" "$SYSTEMD_DIR/$unit"
                RELOAD_NEEDED=true
                echo "[$(date)] Updated $unit"
            fi
        fi
    done

    if $RELOAD_NEEDED; then
        sudo systemctl daemon-reload
    fi

    sudo systemctl restart "$SERVICE"
    echo "[$(date)] Service restarted"
else
    echo "[$(date)] Already up to date"
fi
