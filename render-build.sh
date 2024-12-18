#!/usr/bin/env bash

# Create Chrome directory
mkdir -p /opt/render/project/chrome-linux

# Download and install Chrome
echo "Installing Google Chrome"
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg-deb -x google-chrome-stable_current_amd64.deb /opt/render/project/chrome-linux

# Install ChromeDriver
echo "Installing ChromeDriver"
CHROME_DRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /opt/render/project/chrome-linux/chromedriver || { echo "Could not move chromedriver to /opt/render/project/chrome-linux/"; exit 1; }

# Verify chromedriver exists and is executable
if [ ! -f /opt/render/project/chrome-linux/chromedriver ]; then
    echo "chromedriver not found at /opt/render/project/chrome-linux/chromedriver"
    exit 1
fi

# Create symlink for Chrome binary
CHROME_PATH="/opt/render/project/chrome-linux/opt/google/chrome/chrome"
ln -s $CHROME_PATH /opt/render/project/chrome-linux/chrome || echo "Could not create symlink"

# Cleanup
rm google-chrome-stable_current_amd64.deb chromedriver_linux64.zip

# Verify installation 
echo "Chrome version:"
$CHROME_PATH --version || echo "Chrome not found"
echo "ChromeDriver version:"
/opt/render/project/chrome-linux/chromedriver --version || echo "ChromeDriver not found"