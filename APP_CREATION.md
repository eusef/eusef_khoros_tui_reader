# macOS Application Creation Guide

This guide explains how to create and customize the Khoros TUI Reader macOS application.

## Quick Start

### Create the Application
```bash
./create_app.sh
```

This creates `Khoros TUI Reader.app` on your Desktop.

### Launch the Application
- **Double-click** the app icon on your Desktop
- Or drag it to your **Dock** for quick access
- Or move it to `/Applications` folder

## Customizing the Icon

### Option 1: Use Your Own Image
1. Find or create an icon image (PNG, JPEG, or ICNS)
2. Right-click `Khoros TUI Reader.app` → **Get Info**
3. Drag your image onto the small icon in the top-left of the Info window

### Option 2: Generate a Custom Icon
```bash
./create_custom_icon.sh
```

For better icon quality, install Pillow:
```bash
source .venv/bin/activate
pip install Pillow
./create_custom_icon.sh
```

## Troubleshooting

### Icon Doesn't Update
After changing the icon, you may need to:
```bash
# Refresh Finder's icon cache
killall Finder
# Or: Option + Right-click Finder icon in Dock → Relaunch
```

### App Won't Launch
- Make sure `start.sh` is executable: `chmod +x start.sh`
- Check that the virtual environment exists: `ls .venv/`
- Try running `./start.sh` directly from Terminal to see any errors

### Recreate the App
If you need to recreate the app (e.g., after moving the project):
```bash
# Remove old app
rm -rf ~/Desktop/"Khoros TUI Reader.app"

# Create new app
./create_app.sh
```

## How It Works

The `.app` bundle contains:
- **Info.plist**: Application metadata
- **launcher**: Script that opens Terminal and runs `start.sh`
- **AppIcon.icns**: The application icon

When you double-click the app, it:
1. Opens Terminal
2. Navigates to the project directory
3. Activates the Python virtual environment
4. Runs `start.sh` (which fetches data and starts the TUI)

## Advanced: Custom Icon from Web

To use an icon from the web:
```bash
# Download an icon
curl -o icon.png "https://example.com/icon.png"

# Convert to ICNS (requires imagemagick)
brew install imagemagick
convert icon.png -resize 512x512 icon.icns

# Copy to app
cp icon.icns ~/Desktop/"Khoros TUI Reader.app"/Contents/Resources/AppIcon.icns
touch ~/Desktop/"Khoros TUI Reader.app"  # Refresh
killall Finder  # Update icon cache
```

## Icon Resources

Free icon sites:
- [SF Symbols](https://developer.apple.com/sf-symbols/) (macOS native)
- [Flaticon](https://www.flaticon.com/)
- [Icons8](https://icons8.com/)
- [Noun Project](https://thenounproject.com/)

Remember to check licensing terms if using downloaded icons.

