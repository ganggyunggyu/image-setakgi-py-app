#!/bin/bash

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Building executable..."
pyinstaller --noconfirm --windowed --onefile --name "ImageSetakgi" app/main.py

echo "Done! Executable is in dist/ImageSetakgi"
