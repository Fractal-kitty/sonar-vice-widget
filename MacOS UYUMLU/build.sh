#\!/bin/bash
# ============================================================
#   Sonar Vice Widget - macOS .app Build Script
# ============================================================

set -e

echo ""
echo "  ===================================================="
echo "     Sonar Vice Widget - macOS Build"
echo "  ===================================================="
echo ""

# --- Python check ---
echo "  [1/4] Python kontrol ediliyor..."

if \! command -v python3 &> /dev/null; then
    echo "  [\!] Python3 bulunamadi. Python 3.10+ yukleyin."
    echo "      brew install python3"
    exit 1
fi

PYVER=$(python3 --version 2>&1)
echo "        $PYVER bulundu."

# --- Dependencies ---
echo ""
echo "  [2/4] Bagimliliklar kuruluyor..."

cd "$(dirname "$0")"
python3 -m pip install --upgrade pip --quiet
python3 -m pip install -r requirements.txt --quiet
python3 -m pip install pyinstaller --quiet
echo "        Hazir."

# --- Icon ---
echo ""
echo "  [3/4] Icon olusturuluyor..."
python3 gen_icon.py

# --- Determine icon file ---
ICON_FILE="assets/icon.icns"
if [ \! -f "$ICON_FILE" ]; then
    ICON_FILE="assets/icon.ico"
fi

# --- Build ---
echo ""
echo "  [4/4] macOS .app olusturuluyor (1-2 dakika surebilir)..."
echo ""

python3 -m PyInstaller \n    --noconfirm \n    --onefile \n    --windowed \n    --name "SonarViceWidget" \n    --icon "$ICON_FILE" \n    --add-data "config.py:." \n    --add-data "api:api" \n    --add-data "ui:ui" \n    --hidden-import "pystray._darwin" \n    --hidden-import "customtkinter" \n    --collect-data "customtkinter" \n    main.py

if [ $? -ne 0 ]; then
    echo "  [\!] Build basarisiz oldu."
    exit 1
fi

# --- Cleanup ---
rm -rf build/
rm -f SonarViceWidget.spec

echo ""
echo "  ===================================================="
echo "     Build tamamlandi\!"
echo "  ===================================================="
echo ""
echo "  APP: dist/SonarViceWidget"
echo "  NOT: SteelSeries GG kurulu olmalidir."
echo "  ===================================================="
echo ""

# Open the dist folder in Finder
open dist/
