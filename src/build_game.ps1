# PowerShell build script

$APP_NAME = "SmartTransportGame"
$ICON_FILE = "game.ico"
$MAIN_SCRIPT = "main.py"

$DATA_ASSETS = "assets;assets"
$DATA_FONTS = "fonts;fonts"
$DATA_SOUNDS = "sounds;sounds"

$PYINSTALLER_CMD = "pyinstaller --noconsole --onefile --name=`"$APP_NAME`" --icon=`"$ICON_FILE`" --hidden-import=`"backports`" --add-data `"$DATA_ASSETS`" --add-data `"$DATA_FONTS`" --add-data `"$DATA_SOUNDS`" $MAIN_SCRIPT"

Write-Host "Building $APP_NAME..."
Invoke-Expression $PYINSTALLER_CMD
Write-Host "Build finished!"
