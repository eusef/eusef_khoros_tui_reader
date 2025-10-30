#!/bin/bash
# Create a custom icon for the Khoros TUI Reader app

APP_NAME="Khoros TUI Reader"
APP_PATH="$HOME/Desktop/$APP_NAME.app"
ICON_PATH="$APP_PATH/Contents/Resources/AppIcon.icns"

echo "Creating custom icon for $APP_NAME..."
echo ""

# Check if the app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: App not found at $APP_PATH"
    echo "Please run create_app.sh first"
    exit 1
fi

# Create a temporary directory for icon generation
TEMP_DIR=$(mktemp -d)
ICONSET_DIR="$TEMP_DIR/AppIcon.iconset"
mkdir -p "$ICONSET_DIR"

# Create different sizes of the icon
# We'll use Python with PIL (if available) or fall back to sips

if command -v python3 &> /dev/null && python3 -c "from PIL import Image, ImageDraw, ImageFont" 2>/dev/null; then
    echo "Using Python to generate icon..."
    
    python3 << 'PYCODE'
from PIL import Image, ImageDraw, ImageFont
import os

# Create a base image at highest resolution
sizes = [(16, 16), (32, 32), (128, 128), (256, 256), (512, 512), (1024, 1024)]
iconset_dir = os.environ['ICONSET_DIR']

for size, size_tuple in enumerate(sizes):
    width, height = size_tuple
    
    # Create image with gradient background
    img = Image.new('RGB', (width, height), color='#1e3a8a')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple design
    # Blue gradient background
    for i in range(height):
        color_val = int(30 + (i / height) * 50)
        draw.rectangle([(0, i), (width, i+1)], fill=(color_val, color_val+20, 140))
    
    # Draw a simple "K" or book icon representation
    if width >= 128:
        # Draw a simple envelope/mail icon
        margin = int(width * 0.15)
        draw.rectangle(
            [(margin, margin*1.5), (width-margin, height-margin*1.5)],
            fill='white', outline='#e5e7eb', width=max(2, int(width/64))
        )
        # Envelope flap
        points = [
            (margin, margin*1.5),
            (width//2, height//2),
            (width-margin, margin*1.5)
        ]
        draw.line(points, fill='#9ca3af', width=max(2, int(width/64)))
    
    # Save with and without @2x
    img.save(f'{iconset_dir}/icon_{width}x{height}.png')
    if size < len(sizes) - 1:  # Don't create @2x for 1024
        img.save(f'{iconset_dir}/icon_{width}x{height}@2x.png')

print("Icon images generated!")
PYCODE

else
    echo "Python PIL not available, using system icons as fallback..."
    # Use a nice system icon as base
    BASE_ICON="/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns"
    
    if [ ! -f "$BASE_ICON" ]; then
        BASE_ICON="/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/BookmarkIcon.icns"
    fi
    
    for size in 16 32 128 256 512; do
        size2x=$((size * 2))
        sips -z $size $size "$BASE_ICON" --out "$ICONSET_DIR/icon_${size}x${size}.png" 2>/dev/null
        if [ $size -lt 512 ]; then
            sips -z $size2x $size2x "$BASE_ICON" --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" 2>/dev/null
        fi
    done
fi

# Convert to .icns
echo "Converting to .icns format..."
iconutil -c icns "$ICONSET_DIR" -o "$ICON_PATH"

# Clean up
rm -rf "$TEMP_DIR"

# Touch the app to refresh Finder
touch "$APP_PATH"

echo ""
echo "✅ Custom icon created successfully!"
echo ""
echo "The icon has been updated. You may need to:"
echo "  1. Restart Finder (Option + Right-click Finder icon → Relaunch)"
echo "  2. Or log out and log back in to see the new icon everywhere"
echo ""
echo "To install PIL for better icons in the future:"
echo "  source .venv/bin/activate && pip install Pillow"
echo ""

