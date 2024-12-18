#!/usr/bin/env bash
set -e

# Install required Python packages
pip install --upgrade pip
pip install --upgrade 'selenium>=4.15.2' 'webdriver-manager>=4.0.2'

# Create Chrome directories
CHROME_DIR="/opt/render/project/.chrome"
CHROME_LINUX_DIR="${CHROME_DIR}/chrome-linux64"
mkdir -p "$CHROME_LINUX_DIR"

# Download and extract Chrome
wget -q "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.108/linux64/chrome-linux64.zip"
unzip chrome-linux64.zip -d "/opt/render/project/.chrome"

# Correct the Chrome binary path
CHROME_BINARY_PATH="$CHROME_DIR/chrome/chrome"  # Updated path to match expected location

# Set permissions
chmod +x "/opt/render/project/.chrome/chrome-linux64/chrome"

# Cleanup
rm -f chrome-linux64.zip

# Verify installation
if [ ! -f "$CHROME_BINARY_PATH" ]; then
    echo "Chrome installation failed"
    exit 1
fi

echo "Chrome installation completed successfully"