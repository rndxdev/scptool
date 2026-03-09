#!/bin/bash
# Create a desktop shortcut/launcher for SCP Tool on Linux or macOS.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OS="$(uname -s)"

case "$OS" in
    Linux)
        DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
        DESKTOP_FILE="$DESKTOP_DIR/scptool.desktop"

        # Also install to applications menu
        APPS_DIR="$HOME/.local/share/applications"
        mkdir -p "$APPS_DIR"

        # Generate PNG icon from SVG if not present
        ICON_PATH="$SCRIPT_DIR/icon.png"
        if [ ! -f "$ICON_PATH" ] && [ -f "$SCRIPT_DIR/icon.svg" ]; then
            if command -v convert &>/dev/null; then
                convert "$SCRIPT_DIR/icon.svg" -resize 256x256 "$ICON_PATH"
            elif command -v rsvg-convert &>/dev/null; then
                rsvg-convert -w 256 -h 256 "$SCRIPT_DIR/icon.svg" -o "$ICON_PATH"
            else
                echo "Warning: No SVG converter found. Install imagemagick or librsvg2-bin for icon support."
                ICON_PATH="$SCRIPT_DIR/icon.svg"
            fi
        fi

        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=SCP Tool
Comment=Secure file transfers via SFTP
Exec=bash "$SCRIPT_DIR/launch.sh"
Icon=$ICON_PATH
Terminal=false
Type=Application
Categories=Utility;Network;
StartupNotify=true
EOF
        chmod +x "$DESKTOP_FILE"

        # Copy to applications menu
        cp "$DESKTOP_FILE" "$APPS_DIR/scptool.desktop"

        echo "Desktop shortcut created at: $DESKTOP_FILE"
        echo "Application menu entry created at: $APPS_DIR/scptool.desktop"

        # On some Ubuntu versions, mark desktop file as trusted
        if command -v gio &>/dev/null; then
            gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null
        fi
        ;;

    Darwin)
        APP_DIR="$HOME/Applications/SCP Tool.app"
        MACOS_DIR="$APP_DIR/Contents/MacOS"
        RESOURCES_DIR="$APP_DIR/Contents/Resources"

        mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

        # Create the launcher script
        cat > "$MACOS_DIR/scptool" << EOF
#!/bin/bash
exec bash "$SCRIPT_DIR/launch.sh"
EOF
        chmod +x "$MACOS_DIR/scptool"

        # Convert SVG to ICNS if possible, otherwise use PNG
        ICON_FILE="appicon"
        if [ -f "$SCRIPT_DIR/icon.svg" ]; then
            if command -v rsvg-convert &>/dev/null; then
                rsvg-convert -w 256 -h 256 "$SCRIPT_DIR/icon.svg" -o "$RESOURCES_DIR/appicon.png"
                ICON_FILE="appicon"
            elif command -v sips &>/dev/null && command -v iconutil &>/dev/null; then
                # macOS native approach: SVG -> PNG -> iconset -> ICNS
                ICONSET_DIR=$(mktemp -d)/appicon.iconset
                mkdir -p "$ICONSET_DIR"
                # Use Python to convert SVG since sips can't read SVG
                VENV_PYTHON="$SCRIPT_DIR/backend/venv/bin/python"
                if [ -f "$VENV_PYTHON" ]; then
                    "$VENV_PYTHON" -c "
from PIL import Image
import cairosvg, io, sys
try:
    png_data = cairosvg.svg2png(url='$SCRIPT_DIR/icon.svg', output_width=1024, output_height=1024)
    img = Image.open(io.BytesIO(png_data))
except:
    img = Image.new('RGBA', (1024, 1024), (37, 99, 235, 255))
for size in [16, 32, 64, 128, 256, 512, 1024]:
    resized = img.resize((size, size), Image.LANCZOS)
    resized.save(f'$ICONSET_DIR/icon_{size}x{size}.png')
    if size <= 512:
        double = img.resize((size*2, size*2), Image.LANCZOS)
        double.save(f'$ICONSET_DIR/icon_{size}x{size}@2x.png')
" 2>/dev/null
                    if iconutil -c icns "$ICONSET_DIR" -o "$RESOURCES_DIR/appicon.icns" 2>/dev/null; then
                        ICON_FILE="appicon"
                    fi
                fi
                rm -rf "$(dirname "$ICONSET_DIR")"
            fi
        fi

        # Create Info.plist
        cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>SCP Tool</string>
    <key>CFBundleDisplayName</key>
    <string>SCP Tool</string>
    <key>CFBundleIdentifier</key>
    <string>com.scptool.app</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>scptool</string>
    <key>CFBundleIconFile</key>
    <string>${ICON_FILE}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

        echo "macOS app bundle created at: $APP_DIR"
        echo "You can drag it to /Applications or find it in ~/Applications."
        ;;

    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac
