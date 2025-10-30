#!/bin/bash
# Script to create a macOS .app bundle for Khoros TUI Reader

APP_NAME="Khoros TUI Reader"
APP_DIR="$HOME/Desktop/$APP_NAME.app"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Creating macOS application: $APP_NAME"
echo "Location: $APP_DIR"
echo ""

# Create the app bundle structure
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create the Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.khoros.tui.reader</string>
    <key>CFBundleName</key>
    <string>Khoros TUI Reader</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create the launcher script
cat > "$APP_DIR/Contents/MacOS/launcher" << EOF
#!/bin/bash

# Get the project directory
PROJECT_DIR="$SCRIPT_DIR"

# Open Terminal and run the start script
osascript <<'APPLESCRIPT'
tell application "Terminal"
    activate
    set currentTab to do script "cd '$SCRIPT_DIR' && source .venv/bin/activate && ./start.sh"
end tell
APPLESCRIPT
EOF

# Make the launcher executable
chmod +x "$APP_DIR/Contents/MacOS/launcher"

# Try to create a simple icon (using SF Symbols if available)
# This creates a basic icon - you can replace it with a custom one later
cat > "$APP_DIR/Contents/Resources/create_icon.sh" << 'ICONSCRIPT'
#!/bin/bash
# Create a simple icon using sips and iconutil
# This is a fallback - users can replace AppIcon.icns with their own

# Create a simple colored square as placeholder
ICONSET_DIR="$(dirname "$0")/AppIcon.iconset"
mkdir -p "$ICONSET_DIR"

# Generate a simple icon using sips (if imagemagick not available)
# We'll create a simple blue square with text
for size in 16 32 128 256 512; do
    size2x=$((size * 2))
    # Create a simple colored image
    sips -z $size $size /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/BookmarkIcon.icns \
         --out "$ICONSET_DIR/icon_${size}x${size}.png" 2>/dev/null
    sips -z $size2x $size2x /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/BookmarkIcon.icns \
         --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" 2>/dev/null
done

# Create the .icns file
iconutil -c icns "$ICONSET_DIR" -o "$(dirname "$0")/AppIcon.icns" 2>/dev/null
rm -rf "$ICONSET_DIR"
ICONSCRIPT

chmod +x "$APP_DIR/Contents/Resources/create_icon.sh"
cd "$APP_DIR/Contents/Resources" && ./create_icon.sh 2>/dev/null
rm -f "$APP_DIR/Contents/Resources/create_icon.sh"

echo "✅ Application created successfully!"
echo ""
echo "Location: $APP_DIR"
echo ""
echo "You can now:"
echo "  1. Double-click the app on your Desktop to launch"
echo "  2. Drag it to your Dock for quick access"
echo "  3. Move it to /Applications if you prefer"
echo ""
echo "To customize the icon:"
echo "  1. Find an icon image (PNG or ICNS format)"
echo "  2. Right-click the app → Get Info"
echo "  3. Drag your icon onto the small icon in the top-left"
echo ""

