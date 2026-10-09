#!/usr/bin/env bash
# One-time setup for SPARK Python Lab on a Raspberry Pi (works on other Linux PCs too).
# Installs anything that's missing and adds a "SPARK Python Lab" icon to the desktop and menu.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$DIR/spark_lab.py"

need=()
python3 -c "import tkinter" 2>/dev/null || need+=(python3-tk)
python3 -c "import gpiozero" 2>/dev/null || need+=(python3-gpiozero)
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    python3 -c "import lgpio" 2>/dev/null || need+=(python3-lgpio)
fi
if [ ${#need[@]} -gt 0 ]; then
    echo "Installing: ${need[*]}"
    sudo apt-get update
    sudo apt-get install -y "${need[@]}"
fi

write_launcher() {
    cat > "$1" <<EOF
[Desktop Entry]
Type=Application
Name=SPARK Python Lab
Comment=Learn Python step by step, then blink LEDs with a Raspberry Pi
Exec=python3 "$DIR/spark_lab.py"
Icon=$DIR/assets/icon.png
Terminal=false
Categories=Education;Development;
EOF
    chmod +x "$1"
}

mkdir -p "$HOME/.local/share/applications"
write_launcher "$HOME/.local/share/applications/spark-python-lab.desktop"

DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
if [ -d "$DESKTOP_DIR" ]; then
    write_launcher "$DESKTOP_DIR/spark-python-lab.desktop"
    gio set "$DESKTOP_DIR/spark-python-lab.desktop" metadata::trusted true 2>/dev/null || true
fi

echo
echo "Done! Start SPARK Python Lab from the desktop icon, the Education menu, or with:"
echo "    python3 \"$DIR/spark_lab.py\""
