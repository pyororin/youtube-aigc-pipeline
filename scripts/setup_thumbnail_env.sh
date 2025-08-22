#!/bin/bash

# This script installs the necessary dependencies for thumbnail generation.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Updating package lists..."
sudo apt-get update

echo "Installing ImageMagick and Noto CJK fonts..."
sudo apt-get install -y \
    imagemagick \
    fonts-noto-cjk-extra

echo "Setup complete. ImageMagick and Noto CJK fonts are installed."
