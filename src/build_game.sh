#!/bin/bash

# Detect OS
OS=$(uname)

APP_NAME=SmartTransportGame
ICON_FILE="game_icon.ico"
MAIN_SCRIPT="main.py"

# Unix uses colon separator for add-data
DATA_ASSETS=assets:assets
DATA_FONTS=fonts:fonts
DATA_SOUNDS=sounds:sounds

PYINSTALLER_CMD="pyinstaller --noconsole --onefile --name=\"$APP_NAME\" --icon=\"$ICON_FILE\" --hidden-import=backports --add-data $DATA_ASSETS --add-data $DATA_FONTS --add-data $DATA_SOUNDS $MAIN_SCRIPT"

echo "Building $APP_NAME..."

if [[ "$OS" == "Linux" || "$OS" == "Darwin" ]]; then
    echo "Detected Unix system: $OS"
    $PYINSTALLER_CMD
elif [[ "$OS" == "MINGW"* || "$OS" == "MSYS"* || "$OS" == "CYGWIN"* ]]; then
    echo "Detected Windows environment"
    powershell.exe -Command $PYINSTALLER_CMD
else
    echo "Unsupported OS: $OS"
    exit 1
fi

echo "Build finished!"
